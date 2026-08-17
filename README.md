# github-auto

> Automated GitHub account creation with anti-detection, multi-driver support, and a modern desktop UI.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri)](https://tauri.app)
[![Tailwind](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Overview

**github-auto** is a dual-architecture automation tool:

- **Python backend** — Core automation logic (signup, email verification, CAPTCHA solving, proxy rotation, browser anti-detection)
- **Tauri + React frontend** — Modern desktop UI with glassmorphism/Mica design, real-time logs, and account management

### Key Features

| Feature | Description |
|---------|-------------|
| **Browser** | Camoufox (Firefox, headless, anti-fingerprint) |
| **Anti-Detection** | 25+ stealth measures: fingerprint spoofing, canvas noise, timing jitter, WebGL vendor spoofing |
| **Temp Email** | LewatTok and Supabase providers with automatic fallback |
| **CAPTCHA Solving** | reCAPTCHA audio ASR via Groq Whisper, Turnstile solver |
| **Proxy Rotation** | Per-account sticky proxies with health tracking and country detection |
| **Batch Processing** | Configurable delays, checkpointing, resume support |
| **Session Persistence** | Cookies and localStorage saved per account |
| **Desktop UI** | Glassmorphism design, dark mode, real-time log streaming |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust toolchain (for Tauri desktop app)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/github-auto.git
cd github-auto

# Install Python dependencies
pip install -r requirements.txt

# Install browser engine
camoufox fetch

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Usage

```bash
# Create 1 account
python cli.py register -n 1

# Create 5 accounts with proxy
python cli.py register -n 5 --proxy socks5://user:pass@host:1080

# Create accounts with specific driver
python cli.py register -n 10 --headless

# Check inventory
python cli.py status

# Export accounts
python cli.py export -o data/results/creds.txt
python cli.py export -f csv -o data/results/accounts.csv

# Check configuration
python cli.py config
```

### Desktop App

```bash
cd frontend

# Development mode
npm run tauri dev

# Production build
npm run tauri build
```

---

## Architecture

```
github-auto/
├── config/                  # Configuration (settings, proxies, domains)
├── src/
│   ├── core/                # Account model, store, pipeline
│   ├── email/               # Temp email providers (LewatTok, Supabase)
│   ├── browser/             # Browser driver (Camoufox headless) + stealth
│   ├── captcha/             # CAPTCHA solvers (reCAPTCHA, Turnstile)
│   ├── github/              # GitHub signup, verification, session
│   ├── proxy/               # Proxy rotation and detection
│   └── utils/               # HTTP, identity, logging, UI
├── providers/               # High-level orchestration
├── tests/                   # Unit tests
├── scripts/                 # Utility scripts (update_docs.py)
├── frontend/                # Tauri + React desktop app
│   ├── src-tauri/           # Rust backend
│   └── src/                 # React frontend
├── cli.py                   # CLI entry point
├── pyproject.toml           # Python project config
├── requirements.txt         # Python dependencies
├── CLAUDE.md                # Claude Code instructions
├── AGENTS.md                # AI agent instructions
├── ARCHITECTURE.md          # Detailed architecture docs
├── DEPLOYMENT.md            # Deployment guide
├── CONTRIBUTING.md          # Contribution guide
└── CHANGELOG.md             # Version history
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

---

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LEWATTOK_API_KEY` | LewatTok temp email API key | For LewatTok | - |
| `SUPABASE_URL` | Supabase project URL | For Supabase | - |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | For Supabase | - |
| `GROQ_API_KEY` | Groq API key for Whisper ASR | For reCAPTCHA | - |
| `BROWSER_HEADLESS` | Run headless | No | `true` |
| `BROWSER_HEADLESS` | Run browser headless | No | `false` |
| `REGISTRATION_PASSWORD` | Default password | No | `AutoGen2026!` |
| `PROXY_URL` | Single proxy URL | No | - |
| `PROXIES_FILE` | Proxy list file | No | `config/proxies.txt` |
| `BATCH_DELAY_BASE` | Base delay (seconds) | No | `8` |
| `BATCH_DELAY_JITTER` | Random jitter (seconds) | No | `2` |
| `OTP_TIMEOUT` | OTP wait timeout (seconds) | No | `120` |
| `MAX_RETRIES` | Max retries per account | No | `2` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

### Proxy Format

```
# config/proxies.txt
# Format: protocol://user:pass@host:port|Country
socks5://user:pass@us1.proxy.com:1080|United States
http://user:pass@de1.proxy.com:8080|Germany
socks5://user:pass@jp1.proxy.com:1080|Japan
```

---

## CLI Commands

### `register` — Create GitHub accounts

```bash
python cli.py register [OPTIONS]

Options:
  -n, --count INTEGER       Number of accounts (default: 1)
  --proxy TEXT              Single proxy URL
  --proxy-file TEXT         Proxy list file
  --headless                Run in headless mode (default: true)
  --headless                Run browser headless
  --email-provider TEXT     Email provider: lewattok|supabase
  --delay FLOAT             Delay between accounts (seconds)
  --debug                   Enable debug screenshots
  --resume                  Resume from checkpoint
```

### `status` — Show account inventory

```bash
python cli.py status
```

### `export` — Export accounts to file

```bash
python cli.py export [OPTIONS]

Options:
  -o, --output TEXT         Output file (default: data/results/creds.txt)
  -f, --format TEXT         Format: creds|csv (default: creds)
```

### `config` — Show configuration

```bash
python cli.py config
```

---

## API Reference

See [API.md](API.md) for detailed API documentation.

### Python Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `config/settings.py` | Central configuration | `AppConfig` |
| `providers/github.py` | Main orchestration | `GithubProvider` |
| `src/core/account.py` | Account data model | `Account`, `AccountStatus` |
| `src/core/store.py` | Persistence | `AccountStore` |
| `src/core/pipeline.py` | Batch processing | `Pipeline`, `PipelineResult` |
| `src/email/base.py` | Email interface | `EmailProvider`, `Inbox` |
| `src/email/manager.py` | Provider fallback | `EmailManager` |
| `src/browser/base.py` | Browser interface | `BrowserDriver` |
| `src/browser/stealth.py` | Anti-detection | `apply_stealth()`, `get_stealth_script()` |
| `src/captcha/base.py` | CAPTCHA interface | `CaptchaSolver` |
| `src/github/signup.py` | Signup flow | `GithubSignup`, `SignupResult` |
| `src/proxy/manager.py` | Proxy rotation | `ProxyManager` |

---

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

### Testing

```bash
# Python tests
pytest tests/ -v

# TypeScript type check
cd frontend && npx tsc --noEmit

# Full build test
cd frontend && npm run build
```

### Code Style

- **Python:** PEP 8, type hints, 100-300 LOC/file
- **TypeScript:** Strict mode, functional components, 50-150 LOC/file
- **Rust:** 2021 edition, 100-300 LOC/file

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guide.

### Quick Deploy

```bash
# Build desktop app
cd frontend && npm run tauri build

# Installer location
ls frontend/src-tauri/target/release/bundle/nsis/
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built from components of:
- **qoderush** — GitHub signup flow, HTTP client, proxy rotation
- **autoregister-account** — Stealth suite, temp email, reCAPTCHA ASR
- **tokenharbor** — Turnstile solver, email detection
- **aerolink** — Turnstile API integration

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/github-auto/issues)
- **Documentation:** [docs/](docs/)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

## Codebase Stats

*Last updated: 2026-08-15 19:35*

| Category | Files | Total LOC |
|----------|-------|-----------|
| Python backend | 35 | 4894 |
| Frontend features | 8 | 815 |
| **Total** | **43** | **5709** |