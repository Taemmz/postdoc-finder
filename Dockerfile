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

# Keep container alive in idle state so Coolify's cron engine can exec into it.
# Without this, Docker sees Python exit 0 and restarts the container (Exit 137).
CMD ["tail", "-f", "/dev/null"]
