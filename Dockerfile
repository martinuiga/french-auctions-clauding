FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (note: .env is in .gitignore, won't be copied)
COPY . .

ENV PYTHONUNBUFFERED=1

# Environment variables should be passed at runtime, not built into image
# Required: DATABASE_URL
# Optional: SCRAPE_HOUR, SCRAPE_MINUTE, EEX_BASE_URL

CMD ["python", "main.py"]

# Usage:
# docker build -t eex-scraper .
# docker run -e DATABASE_URL="postgresql://..." eex-scraper
# Or with env file: docker run --env-file .env.production eex-scraper
