FROM python:3.12-slim

# System deps: Chromium runtime + poppler-utils (pdftotext)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgtk-3-0 \
    fonts-liberation fonts-noto-color-emoji \
    wget curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only)
# --with-deps is intentionally omitted: system deps are already installed above
RUN python -m playwright install chromium

COPY server.py .

EXPOSE 5001

CMD ["python", "server.py"]
