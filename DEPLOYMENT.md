# Deployment Guide

Complete deployment guide for github-auto.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10/11, macOS 12+, Linux | Windows 11, macOS 14+ |
| Python | 3.11+ | 3.12+ |
| Node.js | 18+ | 20+ |
| RAM | 4GB | 8GB+ |
| Storage | 1GB | 5GB+ |

### Required Tools

```bash
# Python
python --version  # 3.11+
pip --version

# Node.js
node --version  # 18+
npm --version

# Rust (for Tauri desktop app)
rustc --version  # 1.70+
cargo --version
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/github-auto.git
cd github-auto
```

### 2. Python Backend

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install browser engine
camoufox fetch
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
# Required: GROQ_API_KEY (for reCAPTCHA solving)
# Optional: LEWATTOK_API_KEY, SUPABASE_URL, etc.
```

### 4. Frontend (Desktop App)

```bash
cd frontend

# Install dependencies
npm install

# For Tauri development
npm run tauri dev

# For production build
npm run tauri build
```

## Deployment Options

### Option 1: CLI Only (No Desktop App)

Best for: Server deployment, automation scripts, CI/CD.

```bash
# Install
pip install -r requirements.txt
camoufox fetch

# Configure
cp .env.example .env
# Edit .env

# Run
python cli.py register -n 5
python cli.py status
```

### Option 2: Desktop App

Best for: Personal use, GUI-based workflow.

```bash
cd frontend

# Development
npm run tauri dev

# Production build
npm run tauri build

# Installer location
ls src-tauri/target/release/bundle/nsis/
```

### Option 3: Docker (Experimental)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install browser
RUN camoufox fetch

# Copy application
COPY . .

# Run
CMD ["python", "cli.py", "register", "-n", "1"]
```

```bash
# Build
docker build -t github-auto .

# Run
docker run -e GROQ_API_KEY=your_key github-auto
```

## Production Configuration

### Environment Variables

```bash
# Required for CAPTCHA solving
GROQ_API_KEY=gsk_your_key_here

# Email provider (choose one)
LEWATTOK_API_KEY=your_key
# OR
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# Browser settings
BROWSER_DRIVER=camoufox
BROWSER_HEADLESS=true

# Performance
BATCH_DELAY_BASE=10
BATCH_DELAY_JITTER=3
OTP_TIMEOUT=180
MAX_RETRIES=3

# Proxy (optional)
PROXY_URL=socks5://user:pass@host:1080
# OR
PROXIES_FILE=config/proxies.txt

# Logging
LOG_LEVEL=INFO
```

### Proxy Configuration

```bash
# config/proxies.txt
# One proxy per line
# Format: protocol://user:pass@host:port|Country

socks5://user:pass@us1.proxy.com:1080|United States
socks5://user:pass@de1.proxy.com:1080|Germany
http://user:pass@jp1.proxy.com:8080|Japan
```

### Security Hardening

1. **API Keys:** Store in environment variables, never in code
2. **Proxies:** Use authenticated proxies, rotate regularly
3. **Passwords:** Use strong, unique passwords per account
4. **Sessions:** Clear session data after use
5. **Logs:** Rotate logs, don't log sensitive data

## Monitoring

### Log Files

```bash
# Python logs
data/results/logs/github-auto_YYYY-MM-DD.log

# Tauri logs (desktop app)
# Windows: %APPDATA%/github-auto/logs/
# macOS: ~/Library/Logs/github-auto/
# Linux: ~/.local/share/github-auto/logs/
```

### Health Checks

```bash
# Check account inventory
python cli.py status

# Check configuration
python cli.py config

# Test proxy
python -c "from src.proxy.manager import ProxyManager; pm = ProxyManager(); print(pm.count, 'proxies loaded')"
```

## Troubleshooting

### Common Issues

**1. Browser won't launch**
```bash
# Install browser engine
camoufox fetch

# Check system dependencies
# Linux: sudo apt-get install libgtk-3-0 libnotify-dev
# macOS: xcode-select --install
```

**2. CAPTCHA solving fails**
```bash
# Verify GROQ_API_KEY
echo $GROQ_API_KEY

# Test Groq API
curl -X POST "https://api.groq.com/openai/v1/audio/transcriptions" \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

**3. Proxy connection fails**
```bash
# Test proxy manually
curl -x socks5://user:pass@host:1080 https://api.ipify.org

# Check proxy health in logs
grep "proxy" data/results/logs/*.log
```

**4. Email verification timeout**
```bash
# Increase timeout
export OTP_TIMEOUT=300

# Check email provider status
python -c "from src.email.manager import EmailManager; em = EmailManager(); print('OK')"
```

### Debug Mode

```bash
# Enable debug screenshots
python cli.py register -n 1 --debug

# Screenshots saved to
ls data/results/screenshots/

# Enable verbose logging
export LOG_LEVEL=DEBUG
python cli.py register -n 1
```

## Performance Tuning

### Batch Size

```bash
# Small batches (safer)
python cli.py register -n 5 --delay 15

# Larger batches (faster, more risk)
python cli.py register -n 20 --delay 5
```

### Proxy Optimization

```bash
# Use sticky proxies (recommended)
# One proxy per account, consistent IP

# Use rotating proxies
# Multiple IPs per account, may trigger detection
```

### Browser Optimization

```bash
# Headless mode (faster, less detection risk)
python cli.py register -n 10 --headless

# Headed mode (slower, better for debugging)
python cli.py register -n 1 --debug
```

## Backup & Recovery

### Backup

```bash
# Backup accounts
cp data/accounts.json data/accounts.json.backup

# Backup sessions
tar -czf sessions_backup.tar.gz data/sessions/

# Backup config
cp .env .env.backup
cp config/proxies.txt config/proxies.txt.backup
```

### Recovery

```bash
# Restore accounts
cp data/accounts.json.backup data/accounts.json

# Restore sessions
tar -xzf sessions_backup.tar.gz

# Resume interrupted batch
python cli.py register -n 10 --resume
```

## Updates

```bash
# Pull latest changes
git pull origin main

# Update Python dependencies
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd frontend && npm update

# Rebuild browser engine
camoufox fetch

# Update docs
python scripts/update_docs.py
```

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/github-auto/issues)
- **Documentation:** [docs/](docs/)
- **Logs:** Check `data/results/logs/` for error details
