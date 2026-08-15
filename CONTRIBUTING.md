# Contributing Guide

Thank you for your interest in contributing to github-auto!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Commit Messages](#commit-messages)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Accept constructive criticism gracefully
- Help others learn and grow

## Getting Started

1. **Fork** the repository
2. **Clone** your fork
3. **Create** a feature branch
4. **Make** your changes
5. **Test** thoroughly
6. **Submit** a pull request

```bash
# Fork and clone
git clone https://github.com/yourusername/github-auto.git
cd github-auto

# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ...

# Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# Create pull request
```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust toolchain (for Tauri)

### Setup

```bash
# Clone
git clone https://github.com/yourusername/github-auto.git
cd github-auto

# Python setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
camoufox fetch

# Frontend setup
cd frontend
npm install
cd ..

# Environment
cp .env.example .env
# Edit .env with test API keys

# Run tests
pytest tests/ -v
cd frontend && npx tsc --noEmit && npm run build
```

## Code Style

### Python

- **PEP 8** compliant
- **Type hints** mandatory
- **Docstrings** for public functions
- **100-300 LOC** per file (max 400)

```python
from __future__ import annotations

from typing import Optional
from loguru import logger


def create_inbox(
    username: str,
    domain: Optional[str] = None,
) -> Inbox:
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
    return Inbox(address=f"{username}@{domain}")
```

### TypeScript/React

- **Strict TypeScript**
- **Functional components**
- **50-150 LOC** per file (max 300)
- **shadcn/ui** pattern

```tsx
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
      <Badge variant={status === "created" ? "success" : "destructive"}>
        {status}
      </Badge>
    </div>
  );
}
```

### Rust

- **Rust 2021 edition**
- **Serde** for serialization
- **100-300 LOC** per file

```rust
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

## Pull Request Process

### Before Submitting

1. **Run tests:**
   ```bash
   pytest tests/ -v
   cd frontend && npx tsc --noEmit && npm run build
   ```

2. **Check code style:**
   ```bash
   # Python
   flake8 src/ tests/
   black src/ tests/

   # TypeScript
   cd frontend && npm run lint
   ```

3. **Update documentation:**
   ```bash
   python scripts/update_docs.py
   ```

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style
- [ ] Self-reviewed code
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. **Automated checks** must pass
2. **At least 1 review** required
3. **No merge conflicts**
4. **Documentation updated** if needed

## Issue Guidelines

### Bug Reports

```markdown
**Describe the bug**
Clear description of the bug.

**To reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., Windows 11]
- Python: [e.g., 3.12]
- Node.js: [e.g., 20]
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
Clear description of the problem.

**Describe the solution you'd like**
Your proposed solution.

**Describe alternatives you've considered**
Alternative solutions.

**Additional context**
Any other context or screenshots.
```

## Commit Messages

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

### Examples

```
feat(email): add Gmail provider support

fix(proxy): handle connection timeout gracefully

docs(readme): update installation instructions

refactor(browser): extract stealth utilities

test(email): add unit tests for LewatTok provider

chore(deps): update dependencies
```

## Testing

### Python Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_email.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Type check
npx tsc --noEmit

# Build
npm run build

# Unit tests (if configured)
npm test
```

### Test Structure

```python
# tests/test_email.py
import pytest
from src.email.supabase import SupabaseEmailProvider


class TestSupabaseOTPExtraction:
    """Test OTP extraction patterns."""

    def test_keyword_before_digits(self):
        code = SupabaseEmailProvider.extract_otp(
            "Verify your account",
            "Your OTP code is 123456.",
        )
        assert code == "123456"

    def test_no_code_returns_none(self):
        code = SupabaseEmailProvider.extract_otp(
            "Subject",
            "No verification code here.",
        )
        assert code is None
```

## Documentation

### Updating Docs

```bash
# Auto-update CLAUDE.md and AGENTS.md
python scripts/update_docs.py
```

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start |
| `ARCHITECTURE.md` | Detailed architecture |
| `API.md` | API reference |
| `CONTRIBUTING.md` | This file |
| `DEPLOYMENT.md` | Deployment guide |
| `CHANGELOG.md` | Version history |
| `CLAUDE.md` | Claude Code instructions |
| `AGENTS.md` | AI agent instructions |

### Writing Documentation

- Use clear, concise language
- Include code examples
- Keep examples up-to-date
- Document both API and usage

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/yourusername/github-auto/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/github-auto/discussions)
- **Code:** Read the code and existing docs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
