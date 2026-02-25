"""
scraper/server.py
Playwright microservice — scrapes CivicPlus AgendaCenter pages,
downloads agenda PDFs, extracts text with pdftotext.

API:
  POST /scrape   {"city": "celina"}
  GET  /health

Returns:
  {
    "success": true,
    "city": "celina",
    "meeting_title": "City Council Meeting",
    "meeting_date": "2025-03-03",
    "meeting_type": "City Council",
    "agenda_url": "https://...",
    "agenda_text": "full extracted text..."
  }
"""

import os
import re
import subprocess
import tempfile
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ─── Config ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

CITY_CONFIGS = {
    "celina": {
        "name": "Celina",
        "agenda_url": "https://www.celina-tx.gov/AgendaCenter",
    },
    "anna": {
        "name": "Anna",
        "agenda_url": "https://www.annatexas.gov/AgendaCenter",
    },
    "princeton": {
        "name": "Princeton",
        "agenda_url": "https://www.princetontx.gov/AgendaCenter",
    },
    "melissa": {
        "name": "Melissa",
        "agenda_url": "https://www.cityofmelissa.com/AgendaCenter",
    },
    "fate": {
        "name": "Fate",
        "agenda_url": "https://www.fatetx.gov/AgendaCenter",
    },
    "fulshear": {
        "name": "Fulshear",
        "agenda_url": "https://www.fulsheartexas.gov/AgendaCenter",
    },
}

# Keywords that identify relevant meeting types (case-insensitive)
MEETING_KEYWORDS = [
    "city council",
    "planning and zoning",
    "planning & zoning",
    "p&z",
    "town council",
    "board of aldermen",
    "regular meeting",
]

# How far ahead to look for "upcoming" meetings (days)
UPCOMING_WINDOW_DAYS = 30


# ─── Flask Routes ─────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "txnews-scraper"}), 200


@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json(force=True, silent=True) or {}
    city_key = (data.get("city") or "").lower().strip()

    if city_key not in CITY_CONFIGS:
        return jsonify({
            "success": False,
            "error": f"Unknown city '{city_key}'. Valid: {list(CITY_CONFIGS.keys())}",
        }), 400

    config = CITY_CONFIGS[city_key]
    log.info(f"Scraping AgendaCenter for {config['name']} at {config['agenda_url']}")

    try:
        result = scrape_agenda_center(city_key, config)
        return jsonify(result), 200 if result["success"] else 404
    except Exception as exc:
        log.exception(f"Unexpected error scraping {city_key}: {exc}")
        return jsonify({"success": False, "error": str(exc), "city": city_key}), 500


# ─── Core Scraper ─────────────────────────────────────────────────────────────

def scrape_agenda_center(city_key: str, config: dict) -> dict:
    """
    Use Playwright to load the AgendaCenter, find the most recent upcoming
    council/P&Z meeting, download its agenda PDF, and extract the text.
    """
    base_url = config["agenda_url"]
    city_name = config["name"]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        try:
            page.goto(base_url, wait_until="networkidle", timeout=30_000)
        except PlaywrightTimeoutError:
            log.warning(f"Timeout loading {base_url}, trying domcontentloaded…")
            page.goto(base_url, wait_until="domcontentloaded", timeout=20_000)

        # Give JS a moment to render agenda list
        page.wait_for_timeout(2000)

        # ── Collect candidate meeting links ────────────────────────────────────
        candidates = _collect_meeting_candidates(page, base_url)

        if not candidates:
            browser.close()
            return {
                "success": False,
                "city": city_key,
                "error": "No upcoming council or P&Z meetings found on AgendaCenter.",
            }

        # ── Pick the soonest upcoming meeting ──────────────────────────────────
        best = _select_best_meeting(candidates)
        if not best:
            browser.close()
            return {
                "success": False,
                "city": city_key,
                "error": "No meetings within the upcoming window found.",
            }

        log.info(f"Selected meeting: {best['title']} on {best['date_str']} — {best['pdf_url']}")

        # ── Download PDF using authenticated session ────────────────────────────
        pdf_bytes = _download_pdf(context, best["pdf_url"])
        browser.close()

    if not pdf_bytes:
        return {
            "success": False,
            "city": city_key,
            "error": "Could not download agenda PDF.",
            "meeting_title": best.get("title"),
            "meeting_date": best.get("date_str"),
        }

    # ── Extract text with pdftotext ────────────────────────────────────────────
    agenda_text = _extract_pdf_text(pdf_bytes)
    if not agenda_text:
        return {
            "success": False,
            "city": city_key,
            "error": "pdftotext returned no content.",
            "meeting_title": best.get("title"),
        }

    return {
        "success": True,
        "city": city_key,
        "meeting_title": best["title"],
        "meeting_date": best["date_str"],
        "meeting_type": best["meeting_type"],
        "agenda_url": best["pdf_url"],
        "agenda_text": agenda_text,
        "char_count": len(agenda_text),
    }


def _collect_meeting_candidates(page, base_url: str) -> list:
    """
    Scrape the AgendaCenter page for agenda items that match council/P&Z keywords
    and have a viewable agenda (PDF) link.
    Returns list of dicts: {title, date_str, parsed_date, meeting_type, pdf_url}.
    """
    candidates = []

    # CivicPlus AgendaCenter renders agendas in <ul class="catAgendaRow"> or
    # similar structures. We look broadly for any <a> that says "Agenda" or links
    # to a ViewFile or AgendaCenter path, near a date and a meeting-type string.

    # Strategy: find all anchor links pointing to agenda/document viewers or PDFs
    links = page.query_selector_all("a[href]")

    for link in links:
        try:
            href = link.get_attribute("href") or ""
            text = (link.inner_text() or "").strip()
        except Exception:
            continue

        # Only care about agenda/document links
        if not _is_agenda_link(href, text):
            continue

        # Walk up the DOM to find the meeting title and date
        title, date_str, parsed_date, meeting_type = _extract_meeting_context(link, page)
        if not title or not parsed_date:
            continue

        # Build absolute URL for PDF
        pdf_url = _make_absolute(href, base_url)

        candidates.append({
            "title": title,
            "date_str": date_str,
            "parsed_date": parsed_date,
            "meeting_type": meeting_type,
            "pdf_url": pdf_url,
        })

    # Deduplicate by pdf_url
    seen = set()
    unique = []
    for c in candidates:
        if c["pdf_url"] not in seen:
            seen.add(c["pdf_url"])
            unique.append(c)

    log.info(f"Found {len(unique)} candidate meeting(s)")
    return unique


def _is_agenda_link(href: str, text: str) -> bool:
    """Return True if this looks like an agenda PDF or viewer link."""
    href_lower = href.lower()
    text_lower = text.lower()

    # Explicit PDF extension
    if href_lower.endswith(".pdf"):
        return True
    # CivicPlus ViewFile or AgendaCenter document viewer patterns
    if "viewfile" in href_lower or "agendacenter/view" in href_lower:
        return True
    if "document" in href_lower and ("agenda" in href_lower or "meeting" in text_lower):
        return True
    # Link text says "Agenda" or "View Agenda"
    if "agenda" in text_lower and len(text_lower) < 40:
        return True

    return False


def _extract_meeting_context(link, page):
    """
    Walk up the DOM from the agenda link to find meeting title and date text.
    Returns (title, date_str, parsed_date, meeting_type).
    """
    # Try to get text from row/container elements up to 5 levels up
    title = ""
    date_str = ""
    parsed_date = None
    meeting_type = "Meeting"

    try:
        # Evaluate JS to walk up DOM and gather surrounding text
        context_text = page.evaluate("""(el) => {
            let node = el;
            let texts = [];
            for (let i = 0; i < 6; i++) {
                node = node.parentElement;
                if (!node) break;
                texts.push(node.innerText || '');
                if (texts[texts.length-1].length > 50) break;
            }
            return texts.join(' | ');
        }""", link)
    except Exception:
        return title, date_str, parsed_date, meeting_type

    # ── Extract date ──────────────────────────────────────────────────────────
    date_patterns = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b',
    ]

    for pat in date_patterns:
        m = re.search(pat, context_text, re.IGNORECASE)
        if m:
            date_str = m.group(0)
            parsed_date = _parse_date(date_str)
            if parsed_date:
                break

    # ── Extract title / meeting type ──────────────────────────────────────────
    for keyword in MEETING_KEYWORDS:
        if keyword.lower() in context_text.lower():
            meeting_type = keyword.title()
            # Try to find a longer title phrase containing the keyword
            m = re.search(
                r'([A-Z][^|\n]{5,60}' + re.escape(keyword) + r'[^|\n]{0,40})',
                context_text,
                re.IGNORECASE
            )
            if m:
                title = m.group(0).strip()[:100]
            else:
                title = keyword.title() + " — " + date_str
            break

    if not title and date_str:
        title = "Meeting — " + date_str

    return title, date_str, parsed_date, meeting_type


def _parse_date(date_str: str):
    """Try to parse a date string into a date object. Returns None on failure."""
    formats = [
        "%m/%d/%Y", "%m-%d-%Y",
        "%m/%d/%y", "%m-%d-%y",
        "%B %d, %Y", "%B %d %Y",
        "%b %d, %Y", "%b. %d, %Y",
        "%b %d %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _select_best_meeting(candidates: list) -> dict | None:
    """
    From candidates, select the soonest upcoming meeting
    (within UPCOMING_WINDOW_DAYS days from today).
    Prefers City Council over P&Z if on same day.
    """
    today = datetime.now(timezone.utc).date()
    window_end = today + timedelta(days=UPCOMING_WINDOW_DAYS)

    upcoming = [
        c for c in candidates
        if c["parsed_date"] and today <= c["parsed_date"] <= window_end
    ]

    if not upcoming:
        # Fallback: take the most recently listed meeting even if past
        past = sorted(
            [c for c in candidates if c["parsed_date"]],
            key=lambda c: c["parsed_date"],
            reverse=True,
        )
        return past[0] if past else None

    # Sort: soonest first, council before P&Z
    def sort_key(c):
        council = 0 if "council" in c["meeting_type"].lower() else 1
        return (c["parsed_date"], council)

    return sorted(upcoming, key=sort_key)[0]


def _download_pdf(context, url: str) -> bytes | None:
    """Download a PDF using the authenticated Playwright session."""
    try:
        response = context.request.get(url, timeout=20_000)
        if response.status == 200:
            return response.body()
        log.warning(f"PDF download returned HTTP {response.status} for {url}")
    except Exception as exc:
        log.error(f"PDF download error: {exc}")
    return None


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Write bytes to a temp file and run pdftotext, return extracted text."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(pdf_bytes)
        tmp_path = tf.name

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", tmp_path, "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            # Trim to first ~8000 chars to keep prompt manageable
            return text[:8000]
        log.error(f"pdftotext failed (rc={result.returncode}): {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        log.error("pdftotext timed out")
    except FileNotFoundError:
        log.error("pdftotext not found — install poppler-utils")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return ""


def _make_absolute(href: str, base_url: str) -> str:
    """Convert a relative href to absolute using the base URL."""
    if href.startswith("http"):
        return href
    from urllib.parse import urljoin
    return urljoin(base_url, href)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
