# Slim, production-ready image. Same source runs unchanged on Termux, a
# bare VPS, or here — only environment variables differ.
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; sqlite3 CLI is handy for manual DB inspection.
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data

# Runs as a non-root user inside the container.
RUN useradd --create-home --shell /bin/bash botuser \
    && chown -R botuser:botuser /app
USER botuser

EXPOSE 8099

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('WEB_PORT','8099') + '/healthz', timeout=3)" || exit 1

CMD ["python", "main.py"]
