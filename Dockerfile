FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libgtk-3-0 \
    libnotify-dev \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    xdg-utils \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install browser engine
RUN python -m camoufox fetch

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/results data/sessions data/logs

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV BROWSER_HEADLESS=true
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core.store import AccountStore; print('OK')" || exit 1

# Run
ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
