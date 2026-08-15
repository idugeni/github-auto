# API Reference

Complete API reference for github-auto Python modules.

## Table of Contents

- [Core](#core)
- [Email](#email)
- [Browser](#browser)
- [CAPTCHA](#captcha)
- [GitHub](#github)
- [Proxy](#proxy)
- [Utils](#utils)
- [Providers](#providers)
- [CLI](#cli)

---

## Core

### `config.settings`

Central configuration module.

```python
from config.settings import config

# Access configuration
print(config.email.provider)  # "lewattok"
print(config.browser.driver)  # "camoufox"
print(config.proxy.url)       # None
```

#### `AppConfig`

```python
@dataclass(frozen=True)
class AppConfig:
    email: EmailConfig
    browser: BrowserConfig
    captcha: CaptchaConfig
    proxy: ProxyConfig
    registration: RegistrationConfig
    pipeline: PipelineConfig
    storage: StorageConfig
    log: LogConfig
```

#### `EmailConfig`

| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| `lewattok_api_key` | `str` | `""` | `LEWATTOK_API_KEY` |
| `supabase_url` | `str` | `""` | `SUPABASE_URL` |
| `supabase_anon_key` | `str` | `""` | `SUPABASE_ANON_KEY` |
| `provider` | `str` | `"lewattok"` | `EMAIL_PROVIDER` |
| `poll_interval` | `float` | `1.5` | - |
| `otp_timeout` | `int` | `120` | - |

#### `BrowserConfig`

| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| `headless` | `bool` | `false` | `BROWSER_HEADLESS` |
| `driver` | `str` | `"camoufox"` | `BROWSER_DRIVER` |
| `viewport_width` | `int` | `1280` | - |
| `viewport_height` | `int` | `720` | - |
| `default_timeout` | `int` | `60000` | - |

---

### `src.core.account`

Account data model.

```python
from src.core.account import Account, AccountStatus

# Create account
account = Account(
    username="gh_user1",
    password="SecurePass123",
    email="user1@temp.com",
)

# Update status
account.mark_created()
account.mark_verified()
account.mark_failed("OTP timeout")

# Export
line = account.to_creds_line()  # "user1@temp.com|SecurePass123|gh_user1"
```

#### `Account`

```python
class Account(BaseModel):
    username: str
    password: str
    email: str
    email_password: str = ""
    status: AccountStatus = AccountStatus.PENDING
    recovery_codes: list[str] = []
    session_cookies: dict = {}
    provider: str = ""
    proxy: str = ""
    error: str = ""
    created_at: str  # ISO timestamp
    verified_at: Optional[str] = None
    metadata: dict = {}
```

#### `AccountStatus`

```python
class AccountStatus(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    VERIFIED = "verified"
    FAILED = "failed"
```

---

### `src.core.store`

Dual JSON + SQLite persistence.

```python
from src.core.store import AccountStore

# Initialize
store = AccountStore("data/accounts.json")

# Save account
store.save(account)

# Get account
account = store.get("gh_user1")

# List accounts
accounts = store.list_all()
accounts = store.list_all(status=AccountStatus.CREATED)

# Count
total = store.count()
created = store.count(AccountStatus.CREATED)

# Export
count = store.export_creds("output.txt", AccountStatus.VERIFIED)
```

#### `AccountStore`

```python
class AccountStore:
    def __init__(self, json_path: str, sqlite_path: Optional[str] = None)

    def save(self, account: Account) -> None
    def get(self, username: str) -> Optional[Account]
    def list_all(self, status: Optional[AccountStatus] = None) -> list[Account]
    def count(self, status: Optional[AccountStatus] = None) -> int
    def export_creds(self, path: str, status: AccountStatus = AccountStatus.VERIFIED) -> int
```

---

### `src.core.pipeline`

Batch orchestrator with retry/checkpoint.

```python
from src.core.pipeline import Pipeline, PipelineResult

# Create pipeline
pipeline = Pipeline(
    store=store,
    worker=provider.create_account,
    delay_base=8.0,
    delay_jitter=2.0,
    max_retries=2,
)

# Run
result = pipeline.run(
    count=10,
    resume=False,
    on_progress=lambda cur, total: print(f"{cur}/{total}"),
)

print(f"Success: {result.success}, Failed: {result.failed}")
```

#### `Pipeline`

```python
class Pipeline:
    def __init__(
        self,
        store: AccountStore,
        worker: Callable[[dict], Account],
        delay_base: float = 8.0,
        delay_jitter: float = 2.0,
        max_retries: int = 2,
        checkpoint_file: Optional[str] = None,
    )

    def run(
        self,
        count: int = 1,
        resume: bool = False,
        on_success: Optional[Callable[[Account], None]] = None,
        on_failure: Optional[Callable[[Account, Exception], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> PipelineResult
```

#### `PipelineResult`

```python
@dataclass
class PipelineResult:
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    elapsed: float = 0.0
    errors: list[str] = []
```

---

## Email

### `src.email.base`

Abstract email provider interface.

```python
from src.email.base import EmailProvider, Inbox

class EmailProvider(ABC):
    @abstractmethod
    def create_inbox(self, username: str, domain: Optional[str] = None) -> Inbox

    @abstractmethod
    def poll_otp(self, address: str, sender_contains: Optional[str] = None, timeout: int = 120) -> str

    @abstractmethod
    def delete_inbox(self, address: str, token: str) -> None
```

---

### `src.email.lewattok`

LewatTok temp email provider.

```python
from src.email.lewattok import LewatTokClient

# Initialize
client = LewatTokClient(api_key="your_api_key")

# Create inbox
inbox = client.create_inbox("username", domain="lewattok.web.id")
print(inbox.address)  # "username@lewattok.web.id"

# Poll OTP
code = client.poll_otp(inbox.address, sender_contains="github", timeout=120)

# Delete inbox
client.delete_inbox(inbox.address, inbox.inbox_token)
```

---

### `src.email.supabase`

Supabase temp email provider.

```python
from src.email.supabase import SupabaseEmailProvider

# Initialize
provider = SupabaseEmailProvider(
    supabase_url="https://your-project.supabase.co",
    anon_key="your_anon_key",
)

# Create inbox
inbox = provider.create_inbox("username")
print(inbox.address)  # "username@openfile.my.id"

# Poll OTP
code = provider.poll_otp(inbox.address, timeout=120)

# Extract OTP from message
otp = SupabaseEmailProvider.extract_otp(
    subject="Verify your account",
    text_body="Your code is 123456",
)
```

---

### `src.email.manager`

Email manager with fallback chain.

```python
from src.email.manager import EmailManager

# Initialize with automatic fallback
manager = EmailManager(primary="lewattok")

# Create inbox (tries primary, falls back to Supabase)
inbox = manager.create_inbox("username")

# Poll OTP
code = manager.poll_otp(inbox.address, timeout=120)

# Delete inbox
manager.delete_inbox(inbox.address, inbox.token)
```

---

## Browser

### `src.browser.base`

Abstract browser driver interface.

```python
from src.browser.base import BrowserDriver

class BrowserDriver(ABC):
    @abstractmethod
    def launch(self, headless: bool = False, proxy: Optional[str] = None) -> BrowserContext

    @abstractmethod
    def close(self) -> None
```

---

### `src.browser.camoufox`

Camoufox browser driver (Firefox-based).

```python
from src.browser.camoufox import CamoufoxBrowser

# Initialize
browser = CamoufoxBrowser()

# Launch
ctx = browser.launch(headless=False, proxy="socks5://user:pass@host:1080")
page = ctx.new_page()

# Use page
page.goto("https://github.com/signup")

# Close
page.close()
ctx.close()
browser.close()
```

---

### `src.browser.patchright`

Patchright browser driver (Chromium-based).

```python
from src.browser.patchright import PatchrightBrowser

# Initialize
browser = PatchrightBrowser()

# Launch
ctx = browser.launch(headless=False)
page = ctx.new_page()

# Use page
page.goto("https://github.com/signup")

# Close
browser.close()
```

---

### `src.browser.stealth`

Anti-detection stealth injection.

```python
from src.browser.stealth import apply_stealth, get_stealth_script, CHROME_ARGS

# Apply to page
apply_stealth(page, country_code="US")

# Get script for manual injection
script = get_stealth_script(country_code="ID", user_agent="...")
page.add_init_script(script)

# Get Chrome launch args
args = CHROME_ARGS  # ["--disable-blink-features=AutomationControlled", ...]
```

---

### `src.browser.human`

Human behavior simulation.

```python
from src.browser.human import (
    type_human,
    fill_human,
    human_mouse_move,
    human_scroll,
    get_recent_chrome_user_agent,
)

# Type with human delays
type_human(page, "#email", "user@example.com")

# Fill input
fill_human(page, page.locator("#password"), "SecurePass123")

# Mouse movement
human_mouse_move(page, start_x=100, start_y=100, end_x=500, end_y=300)

# Scroll
human_scroll(page, times=3)

# Generate user agent
ua = get_recent_chrome_user_agent()
```

---

## CAPTCHA

### `src.captcha.base`

Abstract CAPTCHA solver interface.

```python
from src.captcha.base import CaptchaSolver

class CaptchaSolver(ABC):
    @abstractmethod
    def solve(self, page: Page, url: Optional[str] = None) -> Optional[str]
```

---

### `src.captcha.recaptcha`

reCAPTCHA audio ASR solver.

```python
from src.captcha.recaptcha import RecaptchaAudioSolver

# Initialize
solver = RecaptchaAudioSolver(groq_api_key="gsk_your_key")

# Solve
token = solver.solve(page)
# Returns: "already_solved", "solved_instantly", "audio_solved", or None
```

---

### `src.captcha.turnstile`

Cloudflare Turnstile solver.

```python
from src.captcha.turnstile import TurnstileSolver

# Initialize
solver = TurnstileSolver(timeout=180)

# Solve
token = solver.solve(page)
# Returns: token string or None
```

---

## GitHub

### `src.github.signup`

GitHub signup flow.

```python
from src.github.signup import GithubSignup, SignupResult

# Initialize
signup = GithubSignup(
    page=page,
    email_address="user@temp.com",
    password="SecurePass123",
    debug_screenshots=True,
)

# Register
result = signup.register()

if result.success:
    print(f"Username: {result.username}")
    print(f"Password: {result.password}")
else:
    print(f"Error: {result.error}")
```

---

### `src.github.verify`

Email/device verification.

```python
from src.github.verify import (
    enter_otp_code,
    wait_for_otp_from_email,
    handle_device_verification,
    is_challenge_page,
    needs_otp,
)

# Wait for OTP
code = wait_for_otp_from_email(email_manager, "user@temp.com", timeout=120)

# Enter OTP
enter_otp_code(page, code)

# Handle device verification
handle_device_verification(page, email_manager, "user@temp.com")

# Check page state
if is_challenge_page(page.inner_text("body")):
    print("Challenge detected")

if needs_otp(page.content()):
    print("OTP required")
```

---

### `src.github.session`

Session management.

```python
from src.github.session import (
    save_cookies,
    load_cookies,
    save_session,
    load_session,
    is_logged_in,
    get_username,
)

# Save/load cookies
save_cookies(context, "data/sessions/user.json")
load_cookies(context, "data/sessions/user.json")

# Save/load full session
save_session(page, "gh_user1")
load_session(context, "gh_user1")

# Check auth state
if is_logged_in(page):
    username = get_username(page)
```

---

### `src.github.api`

GitHub REST API client.

```python
from src.github.api import GithubApiClient

# Initialize
client = GithubApiClient(token="ghp_your_token")

# Get user
user = client.get_user()  # Authenticated user
user = client.get_user("octocat")  # Specific user

# Rate limit
limit = client.get_rate_limit()

# Repos
repos = client.get_repos(per_page=10)
repo = client.create_repo("my-repo", private=True)
```

---

## Proxy

### `src.proxy.manager`

Proxy rotation and management.

```python
from src.proxy.manager import ProxyManager

# Initialize from file
manager = ProxyManager(proxy_file="config/proxies.txt")

# Or single proxy
manager = ProxyManager(static_proxy="socks5://user:pass@host:1080")

# Get next proxy
proxy = manager.next()  # "socks5://user:pass@host:1080"

# Mark failed
manager.mark_failed(proxy)

# Stats
print(f"Total: {manager.count}")
print(f"Available: {manager.available}")
```

---

### `src.proxy.detect`

Country/latency detection.

```python
from src.proxy.detect import detect_proxy_country, ProxyInfo

# Detect
info = detect_proxy_country("socks5://user:pass@host:1080")
print(f"Country: {info.country_code}")
print(f"Latency: {info.latency_ms}ms")
print(f"Factor: {info.latency_factor}")
```

---

## Utils

### `src.utils.http`

curl_cffi HTTP wrapper.

```python
from src.utils.http import HttpClient

# Initialize
client = HttpClient(impersonate="chrome131", proxy="socks5://...")

# Request
response = client.get("https://api.github.com/user")
response = client.post("https://api.github.com/user/repos", json={"name": "test"})
```

---

### `src.utils.identity`

Hardware identity spoofing.

```python
from src.utils.identity import generate_identity

# Generate macOS identity
identity = generate_identity("seed-string", platform="macos")
print(identity["machine_id"])
print(identity["mac"])
print(identity["hostname"])

# Generate Linux identity
identity = generate_identity("seed-string", platform="linux")
```

---

### `src.utils.logging`

Structured logging.

```python
from src.utils.logging import get_logger

logger = get_logger("my_module")
logger.info("Processing account %s", username)
logger.warning("OTP timeout")
logger.error("Signup failed: %s", exc)
```

---

## Providers

### `providers.github`

High-level GitHub provider.

```python
from providers.github import GithubProvider

# Initialize
provider = GithubProvider(
    email_manager=email_mgr,
    proxy_manager=proxy_mgr,
    driver="camoufox",
    headless=False,
)

# Create account
account = provider.create_account({"index": 0, "attempt": 0})
print(f"Username: {account.username}")
print(f"Status: {account.status}")
```

---

## CLI

### Commands

```bash
# Register accounts
python cli.py register -n 5 --driver camoufox --proxy socks5://...

# Check status
python cli.py status

# Export
python cli.py export -f creds -o output.txt

# Config
python cli.py config
```

### Options

| Command | Option | Description |
|---------|--------|-------------|
| `register` | `-n, --count` | Number of accounts |
| `register` | `--proxy` | Single proxy URL |
| `register` | `--proxy-file` | Proxy list file |
| `register` | `--driver` | Browser driver |
| `register` | `--headless` | Run headless |
| `register` | `--email-provider` | Email provider |
| `register` | `--delay` | Delay between accounts |
| `register` | `--debug` | Debug screenshots |
| `register` | `--resume` | Resume from checkpoint |
| `export` | `-o, --output` | Output file |
| `export` | `-f, --format` | Export format |
