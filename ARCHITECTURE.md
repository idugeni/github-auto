# Architecture

Detailed architecture documentation for github-auto.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Desktop UI (Tauri)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Dashboard │  │ Accounts │  │ Register │  │   Logs   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │              │
│  ┌────┴──────────────┴──────────────┴──────────────┴────┐       │
│  │                    React Frontend                     │       │
│  │              (Glassmorphism/Mica Design)              │       │
│  └────────────────────────┬────────────────────────────┘       │
│                           │ Tauri IPC                           │
│  ┌────────────────────────┴────────────────────────────┐       │
│  │                   Rust Backend                       │       │
│  │              (Commands + Python Bridge)               │       │
│  └────────────────────────┬────────────────────────────┘       │
└───────────────────────────┼────────────────────────────────────┘
                            │ Subprocess
┌───────────────────────────┼────────────────────────────────────┐
│                    Python Backend                               │
│  ┌────────────────────────┴────────────────────────────┐       │
│  │                 providers/github.py                   │       │
│  │              (Main Orchestration Layer)               │       │
│  └──┬─────────┬─────────┬─────────┬─────────┬─────────┘       │
│     │         │         │         │         │                   │
│  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐               │
│  │Email│  │Brwsr│  │Capt.│  │Proxy│  │Store│               │
│  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘               │
│     │         │         │         │         │                   │
│  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐               │
│  │LwTk │  │Camfx│  │rCAP │  │Detct│  │JSON │               │
│  │Supa │  │Patch│  │Turn │  │Mgr  │  │SQLit│               │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Account Creation Flow

```
1. User initiates via CLI or UI
         │
         ▼
2. Pipeline.run(count)
         │
         ▼
3. GithubProvider.create_account()
         │
         ├──► EmailManager.create_inbox()
         │         │
         │         ├──► LewatTokClient.create_inbox()
         │         └──► SupabaseEmailProvider.create_inbox()
         │
         ├──► BrowserDriver.launch(proxy)
         │         │
         │         ├──► CamoufoxBrowser.launch()
         │         └──► CamoufoxBrowser.launch()
         │
         ├──► GithubSignup.register()
         │         │
         │         ├──► Fill signup form
         │         ├──► Solve CAPTCHA (if present)
         │         └──► Submit registration
         │
         ├──► EmailManager.poll_otp()
         │         │
         │         └──► Wait for verification code
         │
         ├──► enter_otp_code()
         │
         ├──► save_session()
         │
         └──► AccountStore.save()
```

### Email Provider Fallback

```
EmailManager.create_inbox()
         │
         ├──► Try primary provider (LewatTok)
         │         │
         │         ├──► Success → return Inbox
         │         └──► Failure → continue
         │
         └──► Try fallback provider (Supabase)
                   │
                   ├──► Success → return Inbox
                   └──► Failure → raise error
```

### Browser Driver Selection

```
_create_browser(driver_name)
         │
         ├──► "camoufox" → CamoufoxBrowser
         │         │
         │         └──► Camoufox (Firefox-based)
         │                   │
         │                   ├── fingerprint_preset=True
         │                   ├── geoip=True
         │                   └── Anti-detection built-in
         │
         └──► "camoufox" → CamoufoxBrowser
                   │
                   └──► Camoufox (Firefox-based)
                             │
                             ├── apply_stealth() → 25+ measures
                             ├── CHROME_ARGS (30+ flags)
                             └── Human behavior simulation
```

## Module Architecture

### Core Layer (`src/core/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `account.py` | 52 | Pydantic data model, status enum |
| `store.py` | 185 | Dual JSON + SQLite persistence |
| `pipeline.py` | 142 | Batch orchestrator with retry/checkpoint |

**Design Principles:**
- `Account` is a pure data model (Pydantic)
- `AccountStore` handles all persistence (dual-write)
- `Pipeline` manages batch execution with callbacks

### Email Layer (`src/email/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `base.py` | 35 | Abstract `EmailProvider` interface |
| `lewattok.py` | 159 | LewatTok API client |
| `supabase.py` | 189 | Supabase Edge Functions client |
| `manager.py` | 94 | Provider selection + fallback |

**Design Principles:**
- All providers implement `EmailProvider` ABC
- `EmailManager` handles fallback chain
- Each provider is independent and testable

### Browser Layer (`src/browser/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `camoufox.py` | 50 | Camoufox (Firefox) headless driver |
| `session.py` | 60 | Session + cookie management |
| `stealth.py` | 20 | Anti-detection injection |

**Design Principles:**
- All drivers implement `BrowserDriver` ABC
- `stealth.py` is shared across drivers
- Human behavior utils are pure functions

### CAPTCHA Layer (`src/captcha/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `base.py` | 16 | Abstract `CaptchaSolver` interface |
| `recaptcha.py` | 194 | reCAPTCHA audio ASR via Groq |
| `turnstile.py` | 117 | Cloudflare Turnstile solver |

**Design Principles:**
- All solvers implement `CaptchaSolver` ABC
- Each solver is independent
- Easy to add new solvers

### GitHub Layer (`src/github/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `signup.py` | 292 | GitHub signup flow |
| `verify.py` | 149 | Email/device verification |
| `session.py` | 142 | Cookie/session persistence |
| `api.py` | 65 | GitHub REST API client |

**Design Principles:**
- `signup.py` orchestrates the signup flow
- `verify.py` handles OTP and device verification
- `session.py` manages browser state persistence

### Proxy Layer (`src/proxy/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `detect.py` | 101 | Country/latency detection |
| `manager.py` | 156 | Rotation + health tracking |

**Design Principles:**
- `ProxyManager` handles rotation logic
- `detect.py` is stateless utility
- Health tracking prevents bad proxies

### Utils Layer (`src/utils/`)

| File | LOC | Responsibility |
|------|-----|----------------|
| `http.py` | 68 | curl_cffi HTTP wrapper |
| `identity.py` | 155 | Hardware identity spoofing |
| `logging.py` | 56 | loguru setup |
| `ui.py` | 64 | Rich terminal UI |

**Design Principles:**
- All utils are stateless functions
- `http.py` wraps curl_cffi for TLS impersonation
- `identity.py` generates deterministic fake hardware

## Frontend Architecture

### Component Hierarchy

```
App.tsx
  └── Shell.tsx (layout)
        ├── Sidebar.tsx (navigation)
        ├── Header.tsx (titlebar + controls)
        └── Content (page router)
              ├── DashboardPage.tsx
              ├── AccountsPage.tsx
              ├── RegisterPage.tsx
              ├── ProxiesPage.tsx
              ├── EmailPage.tsx
              ├── LogsPage.tsx
              ├── ExportPage.tsx
              └── SettingsPage.tsx
```

### Design System

**Glassmorphism Tokens:**
```css
--glass-bg: rgba(255, 255, 255, 0.65)
--glass-border: rgba(255, 255, 255, 0.5)
--mica-bg: rgba(243, 243, 243, 0.72)
```

**Dark Mode:**
```css
--glass-bg: rgba(44, 44, 44, 0.65)
--glass-border: rgba(255, 255, 255, 0.08)
--mica-bg: rgba(32, 32, 32, 0.80)
```

**Utility Classes:**
- `glass` — Full glass effect with backdrop-blur
- `glass-card` — Glass card with padding
- `sidebar-glass` — Sidebar glass effect
- `titlebar` — Titlebar glass effect

### Tauri Bridge

```
React → invoke("command_name") → Rust handler → Python subprocess
```

**Commands:**
- `get_accounts()` — Fetch account list
- `get_status()` — Get inventory stats
- `register_accounts(count)` — Start registration
- `export_accounts(format, path)` — Export accounts
- `get_config()` / `update_config()` — Config management
- `get_proxies()` / `add_proxy()` / `remove_proxy()` — Proxy management
- `get_logs()` — Fetch log entries

## Error Handling

### Python

```python
# Specific exceptions
class AccountStateError(Exception):
    def __init__(self, state: str, detail: str):
        self.state = state
        self.detail = detail

# Logging
from loguru import logger
logger.warning("OTP timeout for %s", address)
logger.error("Signup failed: %s", exc)

# Pipeline error handling
try:
    account = worker(context)
    store.save(account)
except Exception as exc:
    account.mark_failed(str(exc))
    store.save(account)
```

### TypeScript

```typescript
// Tauri IPC error handling
try {
  const accounts = await invoke<Account[]>("get_accounts");
  setAccounts(accounts);
} catch (error) {
  console.error("Failed to fetch accounts:", error);
  toast.error("Failed to load accounts");
}
```

## Performance Considerations

| Metric | Target | Current |
|--------|--------|---------|
| Python LOC/file | 100-300 | ✅ Max 292 |
| React LOC/file | 50-150 | ✅ Max 135 |
| Rust LOC/file | 100-300 | ✅ 188 |
| Frontend build | <5s | ✅ ~2.5s |
| TypeScript check | <10s | ✅ ~3s |

## Security Considerations

- API keys stored in environment variables only
- Proxy credentials in gitignored config files
- Session data in gitignored data directory
- No hardcoded secrets in source code
- CSP enabled in Tauri config

## Extensibility

### Adding New Email Provider

1. Create `src/email/newprovider.py`
2. Implement `EmailProvider` ABC
3. Add config in `config/settings.py`
4. Register in `src/email/manager.py`
5. Add tests in `tests/test_email.py`

### Adding New Browser Driver

1. Create `src/browser/newdriver.py`
2. Implement `BrowserDriver` ABC
3. Add to factory in `providers/github.py`
4. Add tests in `tests/test_browser.py`

### Adding New CAPTCHA Solver

1. Create `src/captcha/newsolver.py`
2. Implement `CaptchaSolver` ABC
3. Integrate in `src/github/signup.py`
4. Add tests in `tests/test_captcha.py`

### Adding New Frontend Page

1. Create `src/features/newpage/page.tsx`
2. Export as named export
3. Add to router in `src/App.tsx`
4. Add nav item in `src/components/layout/sidebar.tsx`
5. Add page title in `src/components/layout/shell.tsx`

## Testing Strategy

### Unit Tests

- **Location:** `tests/`
- **Framework:** pytest
- **Coverage:** Core logic, email providers, utils

```bash
pytest tests/ -v
```

### Integration Tests

- **Location:** `tests/integration/`
- **Scope:** End-to-end flows

### Frontend Tests

- **Location:** `frontend/src/**/*.test.tsx`
- **Framework:** Vitest + React Testing Library

```bash
cd frontend && npm test
```

## Monitoring & Observability

### Logging

- **Python:** loguru with file rotation
- **Frontend:** Console logs + Tauri events
- **Rust:** stderr logging

### Metrics

- Account creation success rate
- Average creation time
- CAPTCHA solve rate
- Proxy health status

## Future Considerations

- [ ] Multi-account parallel processing
- [ ] Web dashboard (Flask/FastAPI)
- [ ] Docker deployment
- [ ] CI/CD pipeline
- [ ] Account rotation management
- [ ] Advanced proxy management
- [ ] CAPTCHA solver API server
