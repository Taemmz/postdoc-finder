# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system deps needed by lxml / BeautifulSoup
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Default command — Coolify will override this with the scheduled cron call
CMD ["python", "main.py"]
