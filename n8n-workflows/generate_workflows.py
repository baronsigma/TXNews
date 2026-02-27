#!/usr/bin/env python3
"""
generate_workflows.py
Generates all n8n workflow JSON files for TXNews.

Produces 12 workflow files:
  Stream 1 — Building Permit Digest  (Celina, Anna, Princeton, Melissa)
  Stream 2 — Business License Digest (Fate, Fulshear)
  Stream 3 — Meeting Agenda Digest   (all 6 cities)

Run: python3 generate_workflows.py
Output: ./generated/*.json  (import each into n8n via Settings → Import)

Note on category IDs (set up by init-sites.sh in this order):
  1 = Uncategorized (WP default)
  2 = Development        ← Stream 1 permit digest
  3 = Civic Governance   ← Stream 3 agenda digest
  4 = Business           ← Stream 2 license digest
  5 = Public Notices
  6 = Schools & Education
"""

import json
import os
import uuid
from pathlib import Path

OUT_DIR = Path(__file__).parent / "generated"
OUT_DIR.mkdir(exist_ok=True)

# Load .env from repo root if present (so passwords can be embedded at generate time)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


def _app_pass(city_key: str) -> str:
    """Return WP Application Password for the given city key, or a placeholder."""
    env_key = f"WP_APP_PASS_{city_key.upper()}"
    return os.environ.get(env_key, f"REPLACE_WITH_APP_PASS_{city_key.upper()}")

OLLAMA_URL  = "http://172.17.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"

# ─── City Configurations ──────────────────────────────────────────────────────

PERMIT_CITIES = [
    {"key": "celina",    "name": "Celina",    "publication": "The Celina Report",
     "site_url": "https://celinareport.com",    "wp_user": "admin", "category_id": 2, "cad_city_filter": "CELINA"},
    {"key": "anna",      "name": "Anna",      "publication": "Anna Record",
     "site_url": "https://theannanews.com",     "wp_user": "admin", "category_id": 2, "cad_city_filter": "ANNA"},
    {"key": "princeton", "name": "Princeton", "publication": "Princeton TX News",
     "site_url": "https://princetontxnews.com", "wp_user": "admin", "category_id": 2, "cad_city_filter": "PRINCETON"},
    {"key": "melissa",   "name": "Melissa",   "publication": "Melissa TX News",
     "site_url": "https://melissatxnews.com",   "wp_user": "admin", "category_id": 2, "cad_city_filter": "MELISSA"},
]

LICENSE_CITIES = [
    {"key": "fate",     "name": "Fate",     "publication": "Fate Daily Post",
     "site_url": "https://fatedailypost.com",     "wp_user": "admin", "category_id": 4, "tdlr_filter": "FATE"},
    {"key": "fulshear", "name": "Fulshear", "publication": "The Fulshear Report",
     "site_url": "https://thefulshearreport.com", "wp_user": "admin", "category_id": 4, "tdlr_filter": "FULSHEAR"},
]

AGENDA_CITIES = [
    {"key": "celina",    "name": "Celina",    "publication": "The Celina Report",
     "site_url": "https://celinareport.com",    "wp_user": "admin", "category_id": 3, "scraper_city": "celina"},
    {"key": "anna",      "name": "Anna",      "publication": "Anna Record",
     "site_url": "https://theannanews.com",     "wp_user": "admin", "category_id": 3, "scraper_city": "anna"},
    {"key": "princeton", "name": "Princeton", "publication": "Princeton TX News",
     "site_url": "https://princetontxnews.com", "wp_user": "admin", "category_id": 3, "scraper_city": "princeton"},
    {"key": "fate",      "name": "Fate",      "publication": "Fate Daily Post",
     "site_url": "https://fatedailypost.com",   "wp_user": "admin", "category_id": 3, "scraper_city": "fate"},
    {"key": "melissa",   "name": "Melissa",   "publication": "Melissa TX News",
     "site_url": "https://melissatxnews.com",   "wp_user": "admin", "category_id": 3, "scraper_city": "melissa"},
    {"key": "fulshear",  "name": "Fulshear",  "publication": "The Fulshear Report",
     "site_url": "https://thefulshearreport.com", "wp_user": "admin", "category_id": 3, "scraper_city": "fulshear"},
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def uid():
    return str(uuid.uuid4())


def pos(col, row=0):
    return [col * 240, row * 160]


# ─── n8n Node Builders ────────────────────────────────────────────────────────

def node_schedule(cron_expr, position):
    return {
        "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": cron_expr}]}},
        "id": uid(), "name": "Schedule Trigger",
        "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.1,
        "position": position,
    }


def node_config(position, assignments_dict):
    assignments = []
    for k, v in assignments_dict.items():
        assignments.append({"id": uid(), "name": k, "value": v,
                            "type": "number" if isinstance(v, int) else "string"})
    return {
        "parameters": {
            "mode": "manual", "duplicateItem": False,
            "assignments": {"assignments": assignments}, "options": {},
        },
        "id": uid(), "name": "Config",
        "type": "n8n-nodes-base.set", "typeVersion": 3.4,
        "position": position,
    }


def node_http_get(name, url_expr, position):
    return {
        "parameters": {"url": url_expr, "authentication": "none", "method": "GET",
                       "options": {"timeout": 30000}},
        "id": uid(), "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": position,
    }


def node_http_post_raw(name, url, body_expr, position):
    return {
        "parameters": {
            "url": url, "method": "POST",
            "sendBody": True, "contentType": "raw",
            "rawContentType": "application/json",
            "body": body_expr,
            "options": {"timeout": 120000},
        },
        "id": uid(), "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": position,
    }


def node_publish_wp(position):
    """WordPress REST API publish node using Basic Auth credential."""
    return {
        "parameters": {
            "url": "={{ $json.siteUrl }}/wp-json/wp/v2/posts",
            "method": "POST",
            "authentication": "genericCredentialType",
            "genericAuthType": "httpBasicAuth",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": '={"title":"{{ $json.title }}","content":"{{ $json.body }}","status":"publish","categories":[{{ $json.categoryId }}]}',
            "options": {"timeout": 30000},
        },
        "id": uid(), "name": "Publish to WordPress",
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": position,
        "credentials": {"httpBasicAuth": {"id": "wp-basic-auth", "name": "WP Basic Auth"}},
    }


def node_code(name, js_code, position):
    return {
        "parameters": {"mode": "runOnceForAllItems", "jsCode": js_code},
        "id": uid(), "name": name,
        "type": "n8n-nodes-base.code", "typeVersion": 2,
        "position": position,
    }


def node_if_bool(name, left_expr, right_val, position):
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [{
                    "id": uid(), "leftValue": left_expr, "rightValue": right_val,
                    "operator": {"type": "boolean", "operation": "equals"},
                }],
                "combinator": "and",
            },
            "options": {},
        },
        "id": uid(), "name": name,
        "type": "n8n-nodes-base.if", "typeVersion": 2.2,
        "position": position,
    }


def make_workflow(name, nodes, connections):
    return {
        "name": name, "nodes": nodes, "connections": connections,
        "active": False, "settings": {"executionOrder": "v1"},
        "id": uid(), "tags": [],
    }


# ─── Shared JavaScript Code Blocks ────────────────────────────────────────────
# These are plain Python strings — no f-string escaping conflicts.
# City-specific text (CITY_NAME, PUBLICATION) is substituted via str.replace().

PARSE_RESPONSE_JS = r"""
// Extract title and body from Ollama JSON response
const raw = (items[0].json.response || '').trim();

const lines = raw.split('\n');

// First non-blank line = title
let titleIdx = 0;
while (titleIdx < lines.length && lines[titleIdx].trim() === '') titleIdx++;
let title = lines[titleIdx].trim()
  .replace(/^(title[:\-\s]*)/i, '')
  .replace(/\*+/g, '');

// Skip blank separator line
let bodyStart = titleIdx + 1;
while (bodyStart < lines.length && lines[bodyStart].trim() === '') bodyStart++;
let body = lines.slice(bodyStart).join('\n').trim();

// Fallback: if title looks like body prose (> 150 chars or empty)
if (!title || title.length > 150) {
  const firstSentence = (body || raw).replace(/\n/g, ' ').split(/(?<=[.!?])\s+/)[0];
  title = firstSentence.slice(0, 90).trim();
  if (!body) body = raw;
}

// Strip forbidden phrases from body
const forbidden = [
  /valued as not reported/gi, /builder not listed/gi,
  /not available/gi, /unknown builder/gi,
];
forbidden.forEach(re => { body = body.replace(re, ''); });

// Pass config fields forward for WP publish
const cfg = $('Config').first().json;
return [{json: {
  title,
  body,
  cityName:   cfg.cityName,
  siteUrl:    cfg.siteUrl,
  wpUser:     cfg.wpUser,
  wpAppPass:  cfg.wpAppPass,
  categoryId: cfg.categoryId,
}}];
"""

# Check duplicate — window_days substituted via str.replace("WINDOW_DAYS", ...)
CHECK_DUP_TEMPLATE = r"""
// Query WP REST for recent posts in same category (WINDOW_DAYS-day window)
const data = items[0].json;
const { siteUrl, wpUser, wpAppPass, categoryId } = data;

const cutoff = new Date();
cutoff.setDate(cutoff.getDate() - WINDOW_DAYS);

const url = `${siteUrl}/wp-json/wp/v2/posts?categories=${categoryId}&after=${cutoff.toISOString()}&per_page=5&status=publish`;
const auth = 'Basic ' + Buffer.from(`${wpUser}:${wpAppPass}`).toString('base64');

let isDuplicate = false;
try {
  const resp = await fetch(url, { headers: { 'Authorization': auth } });
  const posts = await resp.json();
  isDuplicate = Array.isArray(posts) && posts.length > 0;
} catch (e) {
  isDuplicate = false; // fail open
}

return [{json: {...data, isDuplicate}}];
"""


def check_dup_js(window_days: int) -> str:
    return CHECK_DUP_TEMPLATE.replace("WINDOW_DAYS", str(window_days))


# ─── Stream 1 — Building Permit Digest ───────────────────────────────────────

PERMIT_PROCESS_JS = r"""
// Filter Collin CAD permits for our city, within 60-day window
const allPermits = items[0].json;
if (!Array.isArray(allPermits)) {
  return [{json: {hasData: false}}];
}

const cfg = $('Config').first().json;
const cadFilter = (cfg.cadCityFilter || '').toUpperCase();

const cutoff = new Date();
cutoff.setDate(cutoff.getDate() - 60);
const cutoffStr = cutoff.toISOString().split('T')[0];

const filtered = allPermits.filter(p => {
  const city  = (p.situscity || '').toUpperCase().trim();
  const issued = (p.permitissueddate || '').substring(0, 10);
  return city.includes(cadFilter) && issued >= cutoffStr;
});

if (filtered.length === 0) {
  return [{json: {
    hasData: false,
    cityName:   cfg.cityName,
    siteUrl:    cfg.siteUrl,
    wpUser:     cfg.wpUser,
    wpAppPass:  cfg.wpAppPass,
    categoryId: cfg.categoryId,
  }}];
}

// Group by subdivision
const bySubdivision = {};
filtered.forEach(p => {
  const sub = (p.situssubdivision || p.legalsubdivision || 'General Area').trim() || 'General Area';
  if (!bySubdivision[sub]) bySubdivision[sub] = [];
  bySubdivision[sub].push(p);
});

return [{json: {
  hasData:       true,
  permits:       filtered,
  bySubdivision,
  count:         filtered.length,
  cityName:      cfg.cityName,
  siteUrl:       cfg.siteUrl,
  wpUser:        cfg.wpUser,
  wpAppPass:     cfg.wpAppPass,
  categoryId:    cfg.categoryId,
}}];
"""

# Permit prompt template — CITY_NAME and PUBLICATION are replaced by str.replace()
PERMIT_PROMPT_TEMPLATE = r"""
// Build Qwen prompt for building permit digest
const data = items[0].json;
const { bySubdivision, count, cityName } = data;

let permitSummary = '';
for (const [sub, permits] of Object.entries(bySubdivision)) {
  const builders = {};
  permits.forEach(p => {
    const b = (p.contractorname || p.contractor || '').trim();
    if (b && !['NOT LISTED','N/A','NONE','UNKNOWN',''].includes(b.toUpperCase())) {
      builders[b] = (builders[b] || 0) + 1;
    }
  });
  const builderStr = Object.entries(builders)
    .map(([b, c]) => `${b} (${c} permit${c > 1 ? 's' : ''})`).join(', ');
  permitSummary += `Subdivision: ${sub} — ${permits.length} permit(s). ${builderStr ? 'Builders: ' + builderStr : ''}\n`;
}

const prompt = `You are a civic journalist writing for PUBLICATION, a community newspaper covering CITY_NAME, Texas.

Write a news article about recent residential building permit activity using the data below. Follow the EXAMPLE exactly.

ABSOLUTE RULES (violation = failure):
- Prose paragraphs ONLY. No bullets, dashes, numbered lists, or asterisks under any circumstances.
- Every subdivision name and builder name must appear inside a grammatically complete sentence.
- Group permits by subdivision into flowing paragraphs — one paragraph per subdivision or logical grouping.
- If builder information is missing, omit the builder — never write "not listed", "unknown", "not available", or "N/A".
- Forbidden phrases: "valued as not reported", "builder not listed", "not available", "unknown builder".
- Article length: 250–350 words. Factual local newspaper tone.
- Output exactly: article title on line 1 (no "Title:" prefix), blank line, then article body.

EXAMPLE OUTPUT:
Fourteen New Homes Break Ground Across CITY_NAME Subdivisions

Residential construction activity picked up across CITY_NAME last month as developers broke ground on fourteen new single-family homes spanning three established subdivisions. The permits, issued through the county, reflect continued interest from buyers in one of the region's fastest-growing communities.

The largest concentration of new starts was in Light Farms, where D.R. Horton secured permits for six homes along the neighborhood's northern edge. Neighboring Lilyana recorded four new permits, with Toll Brothers accounting for three of those starts, continuing the builder's prominent presence in the enclave.

Three additional permits were issued for homes in Mustang Lakes, a gated community near the city's western corridor. Village Homes was the builder of record on two of those projects.

City officials note that CITY_NAME's residential pipeline remains robust heading into spring, with multiple new subdivision plats pending approval before the planning and zoning commission.

PERMIT DATA:
${permitSummary}
Total permits (last 60 days): ${count}
City: CITY_NAME

Now write the article:`;

const rawBody = JSON.stringify({
  model: 'OLLAMA_MODEL',
  prompt,
  temperature: 0.3,
  num_predict: 1500,
  stream: false,
});

return [{json: {
  rawBody,
  cityName:   data.cityName,
  siteUrl:    data.siteUrl,
  wpUser:     data.wpUser,
  wpAppPass:  data.wpAppPass,
  categoryId: data.categoryId,
}}];
"""


def permit_prompt_js(city: dict) -> str:
    return (PERMIT_PROMPT_TEMPLATE
            .replace("CITY_NAME",    city["name"])
            .replace("PUBLICATION",  city["publication"])
            .replace("OLLAMA_MODEL", OLLAMA_MODEL))


def build_permit_workflow(city: dict) -> dict:
    data_url = (
        "https://data.texas.gov/resource/82ee-gbj5.json"
        "?$where=situscity+like+'" + city["cad_city_filter"] + "%25'"
        "&$limit=500&$order=permitissueddate+DESC"
    )

    nodes = [
        node_schedule("0 13 * * 1,3,5", pos(0)),        # Mon/Wed/Fri 8am CT
        node_config(pos(1), {
            "cityName":      city["name"],
            "publication":   city["publication"],
            "siteUrl":       city["site_url"],
            "wpUser":        city["wp_user"],
            "wpAppPass":     _app_pass(city["key"]),
            "categoryId":    city["category_id"],
            "cadCityFilter": city["cad_city_filter"],
            "dataUrl":       data_url,
        }),
        node_http_get("Fetch Permits", "={{ $json.dataUrl }}", pos(2)),
        node_code("Process Permits",  PERMIT_PROCESS_JS,        pos(3)),
        node_if_bool("Has Permits?",  "={{ $json.hasData }}", True, pos(4)),
        node_code("Build Prompt",     permit_prompt_js(city),    pos(5)),
        node_http_post_raw("Call Ollama", OLLAMA_URL, "={{ $json.rawBody }}", pos(6)),
        node_code("Parse Response",   PARSE_RESPONSE_JS,         pos(7)),
        node_code("Check Duplicate",  check_dup_js(2),            pos(8)),
        node_if_bool("Is Duplicate?", "={{ $json.isDuplicate }}", False, pos(9)),
        node_publish_wp(pos(10)),
    ]

    connections = {
        "Schedule Trigger": {"main": [[{"node": "Config",          "type": "main", "index": 0}]]},
        "Config":           {"main": [[{"node": "Fetch Permits",   "type": "main", "index": 0}]]},
        "Fetch Permits":    {"main": [[{"node": "Process Permits", "type": "main", "index": 0}]]},
        "Process Permits":  {"main": [[{"node": "Has Permits?",    "type": "main", "index": 0}]]},
        "Has Permits?":     {"main": [[{"node": "Build Prompt",    "type": "main", "index": 0}], []]},
        "Build Prompt":     {"main": [[{"node": "Call Ollama",     "type": "main", "index": 0}]]},
        "Call Ollama":      {"main": [[{"node": "Parse Response",  "type": "main", "index": 0}]]},
        "Parse Response":   {"main": [[{"node": "Check Duplicate", "type": "main", "index": 0}]]},
        "Check Duplicate":  {"main": [[{"node": "Is Duplicate?",   "type": "main", "index": 0}]]},
        "Is Duplicate?":    {"main": [[{"node": "Publish to WordPress", "type": "main", "index": 0}], []]},
    }

    return make_workflow("Permit Digest — " + city["name"], nodes, connections)


# ─── Stream 2 — Business License Digest ──────────────────────────────────────

LICENSE_PROCESS_JS = r"""
const allLicenses = items[0].json;
if (!Array.isArray(allLicenses)) {
  return [{json: {hasData: false}}];
}

const cfg = $('Config').first().json;
const filter = (cfg.tdlrFilter || '').toUpperCase();

const active = allLicenses.filter(lic => {
  const city   = (lic.business_city_state_zip || lic.city || '').toUpperCase();
  const status = (lic.license_status || lic.status || '').toUpperCase();
  return city.includes(filter) && (!status || status === 'ACTIVE' || status === 'ISSUED');
});

if (active.length === 0) {
  return [{json: {hasData: false, cityName: cfg.cityName}}];
}

const byTrade = {};
active.forEach(lic => {
  const trade = (lic.license_type || lic.trade_type || lic.program || 'General').trim();
  if (!byTrade[trade]) byTrade[trade] = [];
  byTrade[trade].push(lic);
});

return [{json: {
  hasData:    true,
  byTrade,
  count:      active.length,
  cityName:   cfg.cityName,
  siteUrl:    cfg.siteUrl,
  wpUser:     cfg.wpUser,
  wpAppPass:  cfg.wpAppPass,
  categoryId: cfg.categoryId,
}}];
"""

LICENSE_PROMPT_TEMPLATE = r"""
const data = items[0].json;
const { byTrade, count, cityName } = data;

let tradeSummary = '';
for (const [trade, lics] of Object.entries(byTrade)) {
  tradeSummary += `${trade}: ${lics.length} active license(s)\n`;
}

const prompt = `You are a civic journalist writing for PUBLICATION, a community newspaper covering CITY_NAME, Texas.

Write a news article summarizing recently active business licenses in CITY_NAME from the Texas Department of Licensing and Regulation (TDLR).

ABSOLUTE RULES:
- Prose paragraphs ONLY. No bullets, dashes, numbered lists, or asterisks.
- Group licenses by trade type into flowing paragraphs.
- Every business name and trade type must appear inside a complete sentence.
- Do not write "not listed" or "unknown" — omit any item without usable information.
- Factual, local newspaper tone. 200–300 words.
- Output: article title on line 1 (no prefix), blank line, then article body.

EXAMPLE OUTPUT:
New Businesses Register Across Skilled Trades in CITY_NAME

A new batch of state-issued business licenses recorded this month through the Texas Department of Licensing and Regulation shows continued commercial activity in CITY_NAME. The registrations span several skilled trade categories, reflecting the growing demand for services in one of the region's fastest-expanding communities.

The cosmetology sector led the filings with four new active licenses, including salons and individual stylists establishing practices within the city. Electrical contractors accounted for three registrations, with licensed firms now authorized to serve both new residential construction and commercial retrofit projects.

Two HVAC businesses joined the local registry, as demand for climate-control installation continues to rise alongside the residential building boom in the county.

LICENSE DATA:
${tradeSummary}
Total active licenses: ${count}
City: CITY_NAME
Source: TDLR — Texas Open Data Portal

Now write the article:`;

const rawBody = JSON.stringify({
  model: 'OLLAMA_MODEL',
  prompt,
  temperature: 0.3,
  num_predict: 1200,
  stream: false,
});

return [{json: {
  rawBody,
  cityName:   data.cityName,
  siteUrl:    data.siteUrl,
  wpUser:     data.wpUser,
  wpAppPass:  data.wpAppPass,
  categoryId: data.categoryId,
}}];
"""


def license_prompt_js(city: dict) -> str:
    return (LICENSE_PROMPT_TEMPLATE
            .replace("CITY_NAME",    city["name"])
            .replace("PUBLICATION",  city["publication"])
            .replace("OLLAMA_MODEL", OLLAMA_MODEL))


def build_license_workflow(city: dict) -> dict:
    data_url = (
        "https://data.texas.gov/resource/7358-krk7.json"
        "?$where=business_city_state_zip+like+'" + city["tdlr_filter"] + "%25'"
        "&$limit=200&$order=license_expiration_date+DESC"
    )

    nodes = [
        node_schedule("0 13 1 * *", pos(0)),   # 1st of month, 8am CT
        node_config(pos(1), {
            "cityName":    city["name"],
            "publication": city["publication"],
            "siteUrl":     city["site_url"],
            "wpUser":      city["wp_user"],
            "wpAppPass":   _app_pass(city["key"]),
            "categoryId":  city["category_id"],
            "tdlrFilter":  city["tdlr_filter"],
            "dataUrl":     data_url,
        }),
        node_http_get("Fetch Licenses", "={{ $json.dataUrl }}", pos(2)),
        node_code("Process Licenses", LICENSE_PROCESS_JS,          pos(3)),
        node_if_bool("Has Licenses?", "={{ $json.hasData }}", True, pos(4)),
        node_code("Build Prompt",     license_prompt_js(city),      pos(5)),
        node_http_post_raw("Call Ollama", OLLAMA_URL, "={{ $json.rawBody }}", pos(6)),
        node_code("Parse Response",   PARSE_RESPONSE_JS,             pos(7)),
        node_code("Check Duplicate",  check_dup_js(25),               pos(8)),
        node_if_bool("Is Duplicate?", "={{ $json.isDuplicate }}", False, pos(9)),
        node_publish_wp(pos(10)),
    ]

    connections = {
        "Schedule Trigger": {"main": [[{"node": "Config",           "type": "main", "index": 0}]]},
        "Config":           {"main": [[{"node": "Fetch Licenses",   "type": "main", "index": 0}]]},
        "Fetch Licenses":   {"main": [[{"node": "Process Licenses", "type": "main", "index": 0}]]},
        "Process Licenses": {"main": [[{"node": "Has Licenses?",    "type": "main", "index": 0}]]},
        "Has Licenses?":    {"main": [[{"node": "Build Prompt",     "type": "main", "index": 0}], []]},
        "Build Prompt":     {"main": [[{"node": "Call Ollama",      "type": "main", "index": 0}]]},
        "Call Ollama":      {"main": [[{"node": "Parse Response",   "type": "main", "index": 0}]]},
        "Parse Response":   {"main": [[{"node": "Check Duplicate",  "type": "main", "index": 0}]]},
        "Check Duplicate":  {"main": [[{"node": "Is Duplicate?",    "type": "main", "index": 0}]]},
        "Is Duplicate?":    {"main": [[{"node": "Publish to WordPress", "type": "main", "index": 0}], []]},
    }

    return make_workflow("Business License Digest — " + city["name"], nodes, connections)


# ─── Stream 3 — Meeting Agenda Digest ────────────────────────────────────────

AGENDA_FETCH_JS = r"""
// Call the local Playwright scraper (txnews-scraper:5001)
const cfg = $('Config').first().json;

let result;
try {
  const resp = await fetch('http://txnews-scraper:5001/scrape', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city: cfg.scraperCity }),
  });
  result = await resp.json();
} catch (e) {
  return [{json: {hasData: false, error: e.message, cityName: cfg.cityName}}];
}

if (!result.success || !result.agenda_text) {
  return [{json: {
    hasData:  false,
    error:    result.error || 'No agenda text returned',
    cityName: cfg.cityName,
  }}];
}

return [{json: {
  hasData:      true,
  meetingTitle: result.meeting_title,
  meetingDate:  result.meeting_date,
  meetingType:  result.meeting_type,
  agendaText:   result.agenda_text,
  cityName:     cfg.cityName,
  siteUrl:      cfg.siteUrl,
  wpUser:       cfg.wpUser,
  wpAppPass:    cfg.wpAppPass,
  categoryId:   cfg.categoryId,
}}];
"""

AGENDA_PROMPT_TEMPLATE = r"""
const data = items[0].json;
const { meetingTitle, meetingDate, meetingType, agendaText, cityName } = data;

const prompt = `You are a civic journalist writing for PUBLICATION, a community newspaper covering CITY_NAME, Texas.

Write a news article previewing an upcoming ${meetingType || 'city council'} meeting based on the agenda text below.

ABSOLUTE RULES:
- Prose paragraphs ONLY. No bullets, dashes, numbered lists, or asterisks.
- Summarize key agenda items in plain English for a general audience.
- Include the meeting date, body name, and key action items in complete sentences.
- Do not reproduce the agenda verbatim — synthesize and explain what each item means for residents.
- 200–350 words. Factual local newspaper tone.
- Output: article title on line 1 (no prefix), blank line, then article body.

EXAMPLE OUTPUT:
CITY_NAME City Council to Consider Rezoning Request and Road Bond at March 3 Meeting

The CITY_NAME City Council will convene Monday, March 3, for its regular monthly meeting, where members are expected to take up a rezoning request from a residential developer along the city's northern growth corridor and consider authorizing a bond package for road improvements near the new elementary school campus.

The rezoning item seeks to reclassify approximately 47 acres from agricultural to planned development to accommodate a 180-unit townhome community. The project has previously received a favorable recommendation from the Planning and Zoning Commission, clearing the way for a council vote.

Also on the agenda is a resolution to call a May bond election, which would ask voters to approve up to $18 million in general obligation bonds to fund the extension of a county road and intersection upgrades at two high-priority safety locations.

The council is also set to hear a presentation from the city manager on infrastructure needs associated with ongoing residential expansion and to approve routine consent items. The meeting begins at 6:30 p.m. at CITY_NAME City Hall.

MEETING INFORMATION:
Title: ${meetingTitle}
Date: ${meetingDate}
Type: ${meetingType}

AGENDA TEXT (from official PDF):
${(agendaText || '').slice(0, 6000)}

Now write the article:`;

const rawBody = JSON.stringify({
  model: 'OLLAMA_MODEL',
  prompt,
  temperature: 0.3,
  num_predict: 1500,
  stream: false,
});

return [{json: {
  rawBody,
  cityName:   data.cityName,
  siteUrl:    data.siteUrl,
  wpUser:     data.wpUser,
  wpAppPass:  data.wpAppPass,
  categoryId: data.categoryId,
}}];
"""


def agenda_prompt_js(city: dict) -> str:
    return (AGENDA_PROMPT_TEMPLATE
            .replace("CITY_NAME",    city["name"])
            .replace("PUBLICATION",  city["publication"])
            .replace("OLLAMA_MODEL", OLLAMA_MODEL))


def build_agenda_workflow(city: dict) -> dict:
    nodes = [
        node_schedule("0 12 * * 1,3,5", pos(0)),   # Mon/Wed/Fri 7am CT
        node_config(pos(1), {
            "cityName":    city["name"],
            "publication": city["publication"],
            "siteUrl":     city["site_url"],
            "wpUser":      city["wp_user"],
            "wpAppPass":   _app_pass(city["key"]),
            "categoryId":  city["category_id"],
            "scraperCity": city["scraper_city"],
        }),
        node_code("Fetch Agenda",  AGENDA_FETCH_JS,               pos(2)),
        node_if_bool("Has Agenda?", "={{ $json.hasData }}", True,  pos(3)),
        node_code("Build Prompt",  agenda_prompt_js(city),         pos(4)),
        node_http_post_raw("Call Ollama", OLLAMA_URL, "={{ $json.rawBody }}", pos(5)),
        node_code("Parse Response", PARSE_RESPONSE_JS,              pos(6)),
        node_code("Check Duplicate", check_dup_js(3),               pos(7)),
        node_if_bool("Is Duplicate?", "={{ $json.isDuplicate }}", False, pos(8)),
        node_publish_wp(pos(9)),
    ]

    connections = {
        "Schedule Trigger": {"main": [[{"node": "Config",           "type": "main", "index": 0}]]},
        "Config":           {"main": [[{"node": "Fetch Agenda",     "type": "main", "index": 0}]]},
        "Fetch Agenda":     {"main": [[{"node": "Has Agenda?",      "type": "main", "index": 0}]]},
        "Has Agenda?":      {"main": [[{"node": "Build Prompt",     "type": "main", "index": 0}], []]},
        "Build Prompt":     {"main": [[{"node": "Call Ollama",      "type": "main", "index": 0}]]},
        "Call Ollama":      {"main": [[{"node": "Parse Response",   "type": "main", "index": 0}]]},
        "Parse Response":   {"main": [[{"node": "Check Duplicate",  "type": "main", "index": 0}]]},
        "Check Duplicate":  {"main": [[{"node": "Is Duplicate?",    "type": "main", "index": 0}]]},
        "Is Duplicate?":    {"main": [[{"node": "Publish to WordPress", "type": "main", "index": 0}], []]},
    }

    return make_workflow("Agenda Digest — " + city["name"], nodes, connections)


# ─── Generate All Workflows ───────────────────────────────────────────────────

def main():
    generated = []

    print("Generating Stream 1 — Building Permit Digest…")
    for city in PERMIT_CITIES:
        wf    = build_permit_workflow(city)
        fname = "permit-digest-" + city["key"] + ".json"
        (OUT_DIR / fname).write_text(json.dumps(wf, indent=2))
        print(f"  OK  {fname}")
        generated.append(fname)

    print("Generating Stream 2 — Business License Digest…")
    for city in LICENSE_CITIES:
        wf    = build_license_workflow(city)
        fname = "business-license-" + city["key"] + ".json"
        (OUT_DIR / fname).write_text(json.dumps(wf, indent=2))
        print(f"  OK  {fname}")
        generated.append(fname)

    print("Generating Stream 3 — Meeting Agenda Digest…")
    for city in AGENDA_CITIES:
        wf    = build_agenda_workflow(city)
        fname = "agenda-digest-" + city["key"] + ".json"
        (OUT_DIR / fname).write_text(json.dumps(wf, indent=2))
        print(f"  OK  {fname}")
        generated.append(fname)

    print(f"\n{len(generated)} workflow files written to {OUT_DIR}/")
    print("\nNext steps:")
    print("1. If WP_APP_PASS_* were not in .env, edit the Config node in each imported workflow")
    print("   OR add WP_APP_PASS_<CITY> vars to .env and re-run this script.")
    print("2. In n8n: Settings → Import → select each JSON file")
    print("3. Create a 'WP Basic Auth' credential in n8n (user: admin, pass: <app-password>)")
    print("4. Activate each workflow after import")


if __name__ == "__main__":
    main()
