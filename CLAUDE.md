# CLAUDE.md — github-auto

## Project Overview

Automated GitHub account creation tool with anti-detection capabilities.

**Dual architecture:**
- **Python backend** — Core automation (signup, email, CAPTCHA, proxy, browser)
- **Tauri + React frontend** — Desktop UI with glassmorphism design

## Tech Stack

| Layer | Tech | Version | Purpose |
|-------|------|---------|---------|
| Backend | Python | 3.11+ | Core automation logic |
| Frontend | React | 19.1 | Desktop UI |
| Desktop | Tauri | 2.2 | Native wrapper |
| Styling | Tailwind CSS | 4.1 | Utility-first CSS |
| UI Components | shadcn/ui | latest | Radix + CVA |
| Build | Vite | 6.4 | Frontend bundler |
| TypeScript | TypeScript | 5.8 | Type safety |
| Rust | Tauri backend | 2021 edition | Native bridge |

## Directory Structure

```
github-auto/
├── config/                  # Centralized config (settings.py, proxies.txt, domains.txt)
├── src/
│   ├── core/                # Account model, store, pipeline
│   ├── email/               # Temp email providers (LewatTok, Supabase)
│   ├── browser/             # Browser drivers (Camoufox, Patchright) + stealth
│   ├── captcha/             # CAPTCHA solvers (reCAPTCHA, Turnstile)
│   ├── github/              # GitHub signup, verification, session
│   ├── proxy/               # Proxy rotation and detection
│   └── utils/               # HTTP, identity, logging, UI
├── providers/               # High-level orchestration (GithubProvider)
├── tests/                   # Unit tests
├── scripts/                 # Utility scripts (update_docs.py)
├── frontend/                # Tauri + React desktop app
│   ├── src-tauri/           # Rust backend
│   ├── src/                 # React frontend
│   └── package.json
├── cli.py                   # CLI entry point (typer)
├── pyproject.toml           # Python project config
├── requirements.txt         # Python dependencies
├── CLAUDE.md                # This file
├── AGENTS.md                # AI agent instructions
├── ARCHITECTURE.md          # Detailed architecture docs
├── DEPLOYMENT.md            # Deployment guide
├── CONTRIBUTING.md          # Contribution guide
├── CHANGELOG.md             # Version history
├── API.md                   # API reference
└── LICENSE                  # MIT License
```

## Code Conventions

### Python

- **Style:** PEP 8, type hints mandatory
- **Imports:** `from __future__ import annotations` at top
- **Error handling:** Specific exceptions, log with loguru
- **Config:** All config via `config/settings.py` dataclasses, env-driven
- **File size:** Target 100-300 LOC, max 400 LOC
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Docstrings:** Google style for public functions
- **Tests:** pytest with descriptive test names

```python
# Good
from __future__ import annotations

from typing import Optional
from loguru import logger

def create_inbox(username: str, domain: Optional[str] = None) -> Inbox:
    """Create a new temporary email inbox.

    Args:
        username: Desired username for the inbox.
        domain: Optional domain override.

    Returns:
        Inbox with address and token.

    Raises:
        RuntimeError: If inbox creation fails.
    """
    logger.info("Creating inbox for %s", username)
    # Implementation
```

### TypeScript/React

- **Style:** Strict TypeScript, functional components
- **Imports:** Use `@/` alias for src paths
- **Components:** shadcn/ui pattern (Radix + CVA + tailwind-merge)
- **State:** React hooks, no external state library
- **File size:** Target 50-150 LOC, max 300 LOC
- **Naming:** PascalCase for components, camelCase for functions/variables
- **Types:** Interface for props, type for unions

```tsx
// Good
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface AccountCardProps {
  username: string;
  email: string;
  status: "created" | "verified" | "failed";
  className?: string;
}

export function AccountCard({
  username,
  email,
  status,
  className,
}: AccountCardProps) {
  return (
    <div className={cn("glass-card", className)}>
      <h3 className="font-medium">{username}</h3>
      <p className="text-sm text-muted-foreground">{email}</p>
    </div>
  );
}
```

### Rust (Tauri)

- **Style:** Rust 2021 edition, serde for serialization
- **Commands:** Each Tauri command bridges to Python via subprocess
- **File size:** Target 100-300 LOC
- **Naming:** snake_case for functions/variables, PascalCase for types
- **Error handling:** Result types with descriptive errors

```rust
// Good
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Account {
    pub username: String,
    pub email: String,
    pub status: String,
}

#[tauri::command]
fn get_accounts() -> Result<Vec<Account>, String> {
    // Implementation
    Ok(vec![])
}
```

## Development Commands

### Python Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python cli.py register -n 5
python cli.py status
python cli.py export -f creds

# Run tests
pytest tests/ -v

# Lint (if configured)
flake8 src/ tests/
black src/ tests/
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Dev server
npm run dev

# Type check
npx tsc --noEmit

# Build
npm run build

# Tauri dev (requires Rust toolchain)
npm run tauri dev

# Tauri build
npm run tauri build
```

## Key Modules

### Python Backend

- **`config/settings.py`** — Central config (frozen dataclasses, env-driven)
- **`providers/github.py`** — Main orchestration (ties all modules)
- **`src/core/pipeline.py`** — Batch processing with retry/checkpoint
- **`src/core/store.py`** — Dual JSON + SQLite persistence
- **`src/email/manager.py`** — Email provider with fallback chain
- **`src/browser/stealth.py`** — 25+ anti-fingerprint measures
- **`src/github/signup.py`** — GitHub signup flow
- **`src/captcha/recaptcha.py`** — reCAPTCHA audio ASR via Groq Whisper

### Frontend

- **`src/components/layout/shell.tsx`** — Main layout with glass sidebar
- **`src/components/layout/sidebar.tsx`** — Navigation with backdrop-blur
- **`src/lib/tauri-ipc.ts`** — Tauri invoke wrappers
- **`src/globals.css`** — Glassmorphism/Mica design tokens
- **`src-tauri/src/lib.rs`** — Rust commands bridging to Python

## Architecture Patterns

### Python → Frontend Bridge

```
React UI → Tauri IPC → Rust commands → Python subprocess → Backend modules
```

### Email Provider Fallback

```
EmailManager → primary provider (LewatTok) → fallback (Supabase) on failure
```

### Browser Driver Selection

```
GithubProvider → Camoufox (Firefox, anti-fingerprint) or Patchright (Chromium)
```

### Glassmorphism Design

```
CSS tokens → backdrop-filter: blur(20px) saturate(180%)
           → background: rgba(255,255,255,0.65)
           → border: 1px solid rgba(255,255,255,0.5)
```

### Error Handling Pattern

```python
# Python: Specific exceptions + loguru
try:
    result = risky_operation()
except SpecificError as exc:
    logger.error("Operation failed: %s", exc)
    raise
except Exception as exc:
    logger.exception("Unexpected error")
    raise RuntimeError(f"Failed: {exc}") from exc
```

```typescript
// TypeScript: try/catch + user feedback
try {
  const result = await invoke<T>("command");
  return result;
} catch (error) {
  console.error("Command failed:", error);
  toast.error("Operation failed");
  throw error;
}
```

### Testing Pattern

```python
# Python: pytest with fixtures
import pytest
from src.email.supabase import SupabaseEmailProvider

class TestSupabaseOTP:
    def test_extract_otp_from_subject(self):
        code = SupabaseEmailProvider.extract_otp(
            "Your code is 123456",
            "Body text",
        )
        assert code == "123456"

    def test_no_code_returns_none(self):
        code = SupabaseEmailProvider.extract_otp("Subject", "No code here")
        assert code is None
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LEWATTOK_API_KEY` | LewatTok temp email API | For LewatTok | - |
| `SUPABASE_URL` | Supabase project URL | For Supabase | - |
| `SUPABASE_ANON_KEY` | Supabase anon key | For Supabase | - |
| `GROQ_API_KEY` | Groq API for Whisper ASR | For reCAPTCHA | - |
| `BROWSER_DRIVER` | `camoufox` or `patchright` | No | `camoufox` |
| `BROWSER_HEADLESS` | Run headless | No | `false` |
| `REGISTRATION_PASSWORD` | Default password | No | `AutoGen2026!` |
| `PROXY_URL` | Single proxy | No | - |
| `BATCH_DELAY_BASE` | Delay between accounts | No | `8s` |
| `BATCH_DELAY_JITTER` | Random jitter | No | `2s` |
| `OTP_TIMEOUT` | OTP wait timeout | No | `120s` |
| `MAX_RETRIES` | Max retries per account | No | `2` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## Adding New Features

### New Email Provider

1. Create `src/email/newprovider.py` implementing `EmailProvider` ABC
2. Add config in `config/settings.py`
3. Register in `src/email/manager.py`
4. Add tests in `tests/test_email.py`

### New Browser Driver

1. Create `src/browser/newdriver.py` implementing `BrowserDriver` ABC
2. Add to factory in `providers/github.py`
3. Add tests in `tests/test_browser.py`

### New CAPTCHA Solver

1. Create `src/captcha/newsolver.py` implementing `CaptchaSolver` ABC
2. Integrate in `src/github/signup.py`
3. Add tests in `tests/test_captcha.py`

### New Frontend Page

1. Create `src/features/newpage/page.tsx`
2. Add to router in `src/App.tsx`
3. Add nav item in `src/components/layout/sidebar.tsx`
4. Add page title in `src/components/layout/shell.tsx`

### New Tauri Command

1. Add Rust function in `src-tauri/src/lib.rs`
2. Add to `tauri::generate_handler![]`
3. Add IPC wrapper in `src/lib/tauri-ipc.ts`
4. Use in React via `invoke()`

## Testing

```bash
# Python tests
pytest tests/ -v

# TypeScript type check
cd frontend && npx tsc --noEmit

# Full build test
cd frontend && npm run build

# Run all checks
python -m py_compile {file}.py  # Syntax check
pytest tests/ -v                # Unit tests
cd frontend && npx tsc --noEmit && npm run build  # Frontend
```

## Performance Notes

- **File size limit:** 300 LOC (Python), 150 LOC (React), 300 LOC (Rust)
- **Module responsibility:** Single responsibility principle
- **Config:** All env-driven, no hardcoded values in code
- **Dependencies:** Pin versions, no range specifiers
- **Caching:** Use appropriate caching for repeated operations
- **Lazy loading:** Load resources only when needed

## Security Considerations

- Never commit `.env` files
- API keys in env vars only
- Proxy credentials in gitignored config files
- Session data in gitignored data directory
- No hardcoded secrets in source code
- Use HTTPS for all API calls
- Validate all user inputs
- Sanitize logs (no sensitive data)

## Troubleshooting

### Common Issues

1. **Browser won't launch** → Run `camoufox fetch`
2. **CAPTCHA fails** → Check `GROQ_API_KEY`
3. **Email timeout** → Increase `OTP_TIMEOUT`
4. **Proxy fails** → Test proxy manually
5. **TypeScript errors** → Run `npx tsc --noEmit`

### Debug Mode

```bash
# Python debug
export LOG_LEVEL=DEBUG
python cli.py register -n 1 --debug

# Frontend debug
cd frontend && npm run dev
# Open browser dev tools
```

### Log Locations

- **Python:** `data/results/logs/`
- **Tauri:** System log directory
- **Frontend:** Browser console

## Auto-Update

```bash
# Update documentation
python scripts/update_docs.py

# This updates:
# - CLAUDE.md (stats section)
# - AGENTS.md (stats section)
# - README.md (stats section)
# - CHANGELOG.md (stats section)
```

## Key Relationships

```
cli.py
  └── providers/github.py (GithubProvider)
        ├── src/email/manager.py (EmailManager)
        │     ├── src/email/lewattok.py (LewatTokClient)
        │     └── src/email/supabase.py (SupabaseEmailProvider)
        ├── src/browser/camoufox.py (CamoufoxBrowser)
        │     └── src/browser/stealth.py (apply_stealth)
        ├── src/browser/patchright.py (PatchrightBrowser)
        │     └── src/browser/stealth.py (apply_stealth)
        ├── src/github/signup.py (GithubSignup)
        ├── src/github/verify.py (enter_otp_code)
        ├── src/captcha/recaptcha.py (RecaptchaAudioSolver)
        ├── src/proxy/manager.py (ProxyManager)
        └── src/core/store.py (AccountStore)
```

## Codebase Stats (Auto-generated)

*Last updated: 2026-08-15 12:43*

| Category | Files | Total LOC |
|----------|-------|-----------|
| Python backend | 25 | 2898 |
| Frontend pages | 8 | 815 |

### Python Modules

| Module | Files | Total LOC | Avg LOC | Max File | Max LOC |
|--------|-------|-----------|---------|----------|---------|
| `browser` | 5 | 467 | 93 | `stealth.py` | 201 |
| `captcha` | 3 | 327 | 109 | `recaptcha.py` | 194 |
| `core` | 3 | 379 | 126 | `store.py` | 185 |
| `email` | 4 | 477 | 119 | `supabase.py` | 189 |
| `github` | 4 | 648 | 162 | `signup.py` | 292 |
| `proxy` | 2 | 257 | 128 | `manager.py` | 156 |
| `utils` | 4 | 343 | 85 | `identity.py` | 155 |

### Frontend Features

| Feature | LOC |
|---------|-----|
| `accounts` | 103 |
| `dashboard` | 101 |
| `email` | 86 |
| `export` | 100 |
| `logs` | 86 |
| `proxy` | 85 |
| `register` | 135 |
| `settings` | 119 |
