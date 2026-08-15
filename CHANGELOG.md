# Changelog

All notable changes to github-auto will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Current Stats

- **Python LOC:** 2898
- **Frontend LOC:** 815
- **Modules:** 7
- **Features:** 8
## [0.1.0] - 2026-08-15

### Added

#### Core
- Account data model with Pydantic
- Dual JSON + SQLite persistence
- Batch pipeline with retry/checkpoint
- CLI entry point (Typer)

#### Email
- LewatTok temp email provider
- Supabase temp email provider
- Email manager with fallback chain
- Multi-pattern OTP extraction
- Adaptive polling intervals

#### Browser
- Camoufox driver (Firefox-based)
- Patchright driver (Chromium-based)
- 25+ anti-fingerprint measures
- Human behavior simulation
- Dynamic Chrome user-agent

#### CAPTCHA
- reCAPTCHA audio ASR solver (Groq Whisper)
- Cloudflare Turnstile solver

#### GitHub
- GitHub signup flow
- Email/device verification
- OTP entry (single + multi-input)
- Session persistence (cookies)
- GitHub REST API client

#### Proxy
- Proxy rotation with health tracking
- Country/latency detection
- Sticky per-account proxy support

#### Utils
- curl_cffi HTTP wrapper (TLS impersonation)
- Hardware identity spoofing
- Structured logging (loguru)
- Rich terminal UI

#### Configuration
- Centralized config (frozen dataclasses)
- Environment variable support
- Proxy file management
- Email domain configuration

#### Tests
- Email module tests
- Browser module tests
- GitHub module tests
- Proxy module tests

#### Documentation
- README.md
- CLAUDE.md (Claude Code instructions)
- AGENTS.md (AI agent instructions)
- Auto-update script for docs

### Source Attribution
- **qoderush** — GitHub signup flow, HTTP client, proxy rotation
- **autoregister-account** — Stealth suite, temp email, reCAPTCHA ASR
- **tokenharbor** — Turnstile solver, email detection
- **aerolink** — Turnstile API, Patchright integration

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-08-15 | Initial release with Python backend |
| 0.2.0 | - | Desktop UI (planned) |
| 0.3.0 | - | Multi-account parallel processing (planned) |
| 1.0.0 | - | Production release (planned) |

## Roadmap

### v0.2.0 — Desktop UI
- [x] Tauri + React setup
- [x] Glassmorphism design
- [x] Dashboard page
- [x] Account management
- [x] Register page
- [x] Log viewer
- [x] Settings page
- [ ] Real-time progress updates
- [ ] Account detail drawer
- [ ] Bulk actions

### v0.3.0 — Parallel Processing
- [ ] Multi-account parallel creation
- [ ] Worker pool management
- [ ] Distributed proxy rotation
- [ ] Progress aggregation

### v1.0.0 — Production
- [ ] Docker deployment
- [ ] CI/CD pipeline
- [ ] Web dashboard (optional)
- [ ] Account rotation management
- [ ] Advanced analytics
- [ ] API server mode

## Breaking Changes

None yet.

## Deprecations

None yet.

## Security

### v0.1.0
- API keys stored in environment variables
- Proxy credentials in gitignored files
- Session data in gitignored directory
- No hardcoded secrets in source code

## Contributors

- Initial development and architecture
