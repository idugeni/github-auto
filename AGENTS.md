# AGENTS.md — github-auto

## Project Context

This is a **GitHub account automation tool** with:
- Python backend for automation logic
- Tauri + React desktop UI with glassmorphism design
- Modular architecture with single responsibility

## When Working on This Project

### Code Style

- **Python:** PEP 8, type hints, `from __future__ import annotations`
- **TypeScript:** Strict mode, functional components, `@/` imports
- **Rust:** 2021 edition, serde serialization

### File Organization

- **100-300 LOC per file** (target)
- **Max 400 LOC** (refactor if exceeded)
- **Single responsibility** — one module, one purpose

### Import Conventions

```python
# Python
from __future__ import annotations
from typing import Optional
from .base import EmailProvider  # relative imports in packages
```

```typescript
// TypeScript
import { Button } from "@/components/ui/button";  // @/ alias
import { cn } from "@/lib/utils";
```

### Config Pattern

All configuration lives in `config/settings.py` as frozen dataclasses.
Environment variables loaded via `dotenv`. No hardcoded values.

### Error Handling

```python
# Python - use loguru, specific exceptions
from loguru import logger
logger.warning("OTP timeout for %s", address)
raise TimeoutError(f"OTP timeout after {timeout}s")
```

```typescript
// TypeScript - try/catch, specific error types
try {
  const result = await invoke<Account[]>("get_accounts");
  return result;
} catch (error) {
  console.error("Failed to get accounts:", error);
  throw error;
}
```

## Adding New Modules

### Python Module

1. Create `src/{module}/__init__.py`
2. Create `src/{module}/base.py` (ABC interface)
3. Create `src/{module}/implementation.py`
4. Register in `providers/github.py` factory
5. Add config in `config/settings.py`
6. Add tests in `tests/test_{module}.py`

### React Page

1. Create `src/features/{page}/page.tsx`
2. Export as named export: `export function {Page}Page()`
3. Add to router in `src/App.tsx`
4. Add nav item in `src/components/layout/sidebar.tsx`
5. Add page title in `src/components/layout/shell.tsx`

### Tauri Command

1. Add Rust function in `src-tauri/src/lib.rs`
2. Add to `tauri::generate_handler![]`
3. Add IPC wrapper in `src/lib/tauri-ipc.ts`
4. Use in React via `invoke()`

## Key Files to Understand

### Python Core Flow

```
cli.py → providers/github.py → src/github/signup.py
                                   ↓
                             src/email/manager.py
                             src/browser/{driver}.py
                             src/captcha/{solver}.py
                                   ↓
                             src/core/store.py (save)
                             src/core/pipeline.py (batch)
```

### Frontend Architecture

```
App.tsx → Shell (layout) → Sidebar + Header + Content
                              ↓
                         features/{page}/page.tsx
                              ↓
                         lib/tauri-ipc.ts → Tauri commands
                              ↓
                         src-tauri/src/lib.rs → Python subprocess
```

## Testing Checklist

Before submitting changes:

```bash
# 1. Python syntax check
python -m py_compile {changed_file}.py

# 2. Python tests
pytest tests/ -v

# 3. TypeScript type check
cd frontend && npx tsc --noEmit

# 4. Frontend build
cd frontend && npm run build

# 5. Verify no LOC regression
wc -l {changed_file}
```

## Common Patterns

### Adding a New Provider

```python
# src/email/newprovider.py
from __future__ import annotations
from .base import EmailProvider, Inbox

class NewProvider(EmailProvider):
    def create_inbox(self, username: str, domain: str | None = None) -> Inbox:
        ...
    def poll_otp(self, address: str, sender_contains: str | None = None, timeout: int = 120) -> str:
        ...
    def delete_inbox(self, address: str, token: str) -> None:
        ...
```

### Adding a New Frontend Component

```tsx
// src/components/ui/newcomponent.tsx
import { cn } from "@/lib/utils";

interface NewComponentProps {
  className?: string;
  // ...
}

export function NewComponent({ className, ...props }: NewComponentProps) {
  return (
    <div className={cn("base-styles", className)} {...props}>
      ...
    </div>
  );
}
```

## Glassmorphism Design Tokens

```css
/* Light mode */
--glass-bg: rgba(255, 255, 255, 0.65);
--glass-border: rgba(255, 255, 255, 0.5);
--mica-bg: rgba(243, 243, 243, 0.72);

/* Dark mode */
--glass-bg: rgba(44, 44, 44, 0.65);
--glass-border: rgba(255, 255, 255, 0.08);
--mica-bg: rgba(32, 32, 32, 0.80);
```

Use utility classes: `glass`, `glass-card`, `sidebar-glass`, `titlebar`

## Performance Targets

| Metric | Target |
|--------|--------|
| Python LOC/file | 100-300 |
| React LOC/file | 50-150 |
| Rust LOC/file | 100-300 |
| Frontend build | <5s |
| TypeScript check | <10s |
| Python syntax | <5s |

## Security Notes

- Never commit `.env` files
- API keys in env vars only
- Proxy credentials in `config/proxies.txt` (gitignored)
- Session data in `data/sessions/` (gitignored)
- Recovery codes in `data/accounts.json` (gitignored)

## Module Dependencies

```
config/settings.py (no deps)
  ↓
src/utils/* (no deps)
  ↓
src/email/base.py (no deps)
  ↓
src/email/lewattok.py (depends on: base, requests)
src/email/supabase.py (depends on: base, requests)
  ↓
src/email/manager.py (depends on: base, lewattok, supabase)
  ↓
src/browser/base.py (no deps)
  ↓
src/browser/stealth.py (no deps)
src/browser/human.py (no deps)
  ↓
src/browser/camoufox.py (depends on: base, camoufox)
src/browser/camoufox.py (depends on: camoufox, stealth)
  ↓
src/captcha/base.py (no deps)
  ↓
src/captcha/recaptcha.py (depends on: base, openai)
src/captcha/turnstile.py (depends on: base)
  ↓
src/github/signup.py (depends on: browser, human)
src/github/verify.py (depends on: email)
src/github/session.py (no deps)
  ↓
src/core/account.py (no deps)
src/core/store.py (depends on: account)
src/core/pipeline.py (depends on: account, store)
  ↓
providers/github.py (depends on: all above)
  ↓
cli.py (depends on: providers, core, utils)
```

## Anti-Detection Measures

### Browser Stealth (src/browser/stealth.py)

25+ measures including:
- `navigator.webdriver` removal
- Plugin/mimeType spoofing
- WebGL vendor/renderer spoofing
- Canvas fingerprint noise
- AudioContext fingerprint spoofing
- Chrome runtime restoration
- CDP stack trace filtering
- Performance timing jitter
- userAgentData spoofing
- 30+ Chrome launch flags

### Human Behavior (src/browser/human.py)

- Character-by-character typing (60-180ms delay)
- Random mouse movement with easing
- Random scroll behavior
- Dynamic Chrome user-agent generation

## Email OTP Extraction

### Patterns (src/email/supabase.py)

1. **Keyword + digits:** `otp.*?(\d{4,8})`
2. **Digits + keyword:** `(\d{4,8}).*?otp`
3. **Fallback:** `(\d{4,8})`

### Year Filtering

Codes matching 1900-2099 are filtered as false positives.

## Proxy Health Tracking

### States (src/proxy/manager.py)

- **Available:** `fail_count < 3` AND `cooldown elapsed`
- **Cooldown:** `last_used + cooldown_seconds > now`
- **Failed:** `fail_count >= 3`

### Rotation Strategy

- Round-robin with health check
- Sticky per-account (same proxy for retries)
- Country-based selection (optional)

## CAPTCHA Solving

### reCAPTCHA Audio ASR (src/captcha/recaptcha.py)

1. Find reCAPTCHA iframe
2. Click checkbox
3. Switch to audio challenge
4. Download MP3
5. Transcribe via Groq Whisper
6. Fill answer
7. Verify

### Turnstile (src/captcha/turnstile.py)

1. Find Turnstile iframe
2. Move mouse to trigger
3. Check for token
4. Click checkbox if needed

## Session Management

### Cookie Persistence (src/github/session.py)

```python
# Save
save_cookies(context, "data/sessions/{username}.json")

# Load
load_cookies(context, "data/sessions/{username}.json")
```

### Auth State Detection

```python
# Check if logged in
is_logged_in(page)  # Returns bool

# Get username
get_username(page)  # Returns Optional[str]
```

## Batch Processing

### Pipeline (src/core/pipeline.py)

```python
# Sequential with retry
pipeline = Pipeline(store, worker, delay_base=8, max_retries=2)
result = pipeline.run(count=10, resume=True)

# Callbacks
result = pipeline.run(
    count=10,
    on_success=lambda acc: print(f"OK: {acc.username}"),
    on_failure=lambda acc, exc: print(f"FAIL: {exc}"),
    on_progress=lambda cur, tot: print(f"{cur}/{tot}"),
)
```

### Checkpointing

- Saves `{last_index: N}` after each account
- Resume with `--resume` flag
- Clears on completion

## Data Persistence

### Dual Storage (src/core/store.py)

- **SQLite:** Primary query store
- **JSON:** Human-readable backup

### Export Formats

- **creds:** `email|password|username`
- **csv:** `email,password,username`

## Future Considerations

When extending this codebase:

1. **Parallel processing:** Add worker pool to pipeline
2. **Web dashboard:** Flask/FastAPI backend
3. **Docker:** Containerized deployment
4. **CI/CD:** GitHub Actions pipeline
5. **Account rotation:** Manage account lifecycle
6. **Advanced analytics:** Success rates, timing
7. **API server:** REST API for external integration

## Current Codebase Stats (Auto-generated)

*Last updated: 2026-08-15 19:35*

- **Python LOC:** 4894
- **Modules:** 11
- **Frontend features:** 8
- **Largest Python module:** `captcha` (941 LOC)
- **Largest frontend page:** `register` (135 LOC)

### Module Health

| Module | Status | LOC |
|--------|--------|-----|
| `api` | [OK] | 161 |
| `browser` | [OK] | 467 |
| `captcha` | [OK] | 941 |
| `core` | [OK] | 379 |
| `dashboard` | [OK] | 277 |
| `email` | [OK] | 891 |
| `github` | [OK] | 678 |
| `parallel` | [OK] | 296 |
| `plugin` | [OK] | 147 |
| `proxy` | [OK] | 314 |
| `utils` | [OK] | 343 |