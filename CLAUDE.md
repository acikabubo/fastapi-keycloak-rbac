# CLAUDE.md

This file provides guidance to Claude Code when working on the fastapi-keycloak-auth package.

## 📚 Documentation

- **DEVELOPMENT.md** - Extraction workflow, refactoring patterns, step-by-step guide
- **README.md** - Package overview, features, installation
- **Issue #1** - Main extraction roadmap with checklist

## 🎯 Project Goal

Extract authentication code from [fastapi-http-websocket](https://github.com/acikabubo/fastapi-http-websocket) into a standalone, reusable Python package.

## 📦 Package Structure

```
fastapi-keycloak-auth/
├── src/                   # Package source (import: from src import ...)
│   ├── __init__.py        # Public API exports
│   ├── backend.py         # AuthBackend for Starlette
│   ├── manager.py         # KeycloakManager singleton
│   ├── rbac.py            # RBACManager for permissions
│   ├── dependencies.py    # FastAPI dependencies (require_roles)
│   ├── models.py          # UserModel, TokenClaims
│   ├── exceptions.py      # Auth exceptions
│   ├── config.py          # KeycloakAuthSettings
│   └── py.typed           # PEP 561 marker
├── tests/
│   ├── conftest.py        # Pytest fixtures
│   ├── test_*.py          # Unit tests
│   └── mocks/             # Test mock factories
├── docs/
│   └── quickstart.md      # Usage examples
└── examples/
    ├── basic_http.py      # Basic HTTP auth example
    └── websocket_auth.py  # WebSocket auth example
```

## ⚠️ CRITICAL: Core Principles

### 1. Minimize Dependencies

**DO:**
- Use standard library where possible (logging, typing)
- Keep core dependencies minimal (FastAPI, python-keycloak, pydantic)
- Make extensions optional (caching, metrics)

**DON'T:**
- Add project-specific dependencies
- Include utility libraries unless absolutely necessary
- Copy entire modules from main project

### 2. Make Everything Configurable

**Pattern to follow:**
```python
# ❌ BAD: Hardcoded
if app_settings.DEBUG_AUTH:
    logger.debug("Auth bypassed")

# ✅ GOOD: Configurable via settings
from src.config import KeycloakAuthSettings

def __init__(self, settings: KeycloakAuthSettings | None = None):
    self.settings = settings or KeycloakAuthSettings()

if self.settings.debug_auth:
    logger.debug("Auth bypassed")
```

### 3. Keep It Generic

**Remove project specifics:**
```python
# ❌ BAD: Project-specific
from app.logging import logger
from app.settings import app_settings
from app.utils.metrics import auth_metric

# ✅ GOOD: Generic
import logging
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
```

## 📋 Extraction Workflow

Follow this order (see DEVELOPMENT.md for details):

1. **exceptions.py** (5 mins) - Auth exceptions
2. **models.py** (10 mins) - UserModel, TokenClaims
3. **config.py** (15 mins) - KeycloakAuthSettings with pydantic-settings
4. **backend.py** (45 mins) - AuthBackend refactoring
5. **manager.py** (30 mins) - KeycloakManager refactoring
6. **rbac.py** (30 mins) - RBACManager refactoring
7. **dependencies.py** (15 mins) - require_roles() extraction

## 🔧 Key Refactoring Tasks

### Remove Project Dependencies

Files from main project that need refactoring:

| Source | Action |
|--------|--------|
| `app.logging.logger` | Replace with `logging.getLogger(__name__)` |
| `app.settings.app_settings` | Replace with `src.config.get_settings()` |
| `app.utils.metrics.*` | Remove (will be optional extension) |
| `app.utils.token_cache.*` | Remove (will be optional extension) |
| `app.exceptions.AuthenticationError` | Move to `src.exceptions` |
| `app.schemas.user.UserModel` | Move to `src.models` |

### Decouple from PackageRouter

The RBACManager currently ties to PackageRouter for WebSocket handlers. Refactor to:
- Use generic permission registry (dict-based)
- Support both decorator and manual registration
- Make storage pluggable

### Make Singleton Optional

KeycloakManager uses singleton pattern. Refactor to:
- Support both singleton and instance usage
- Add async context manager support
- Make initialization explicit

## 🧪 Testing Requirements

For each extracted module:

1. **Create unit tests** - `tests/test_<module>.py`
2. **Extract test mocks** - Reuse from `tests/mocks/`
3. **Ensure type safety** - All code must pass `mypy --strict`
4. **Target coverage** - Aim for >80% test coverage

**Test structure:**
```python
# tests/test_exceptions.py
def test_authentication_error():
    error = AuthenticationError("Invalid token")
    assert str(error) == "Invalid token"
    assert error.status_code == 401
```

## 📝 Commit Message Format

```bash
git commit -m "$(cat <<'EOF'
<type>: <description>

<body with details if needed>

Relates to #<issue_number>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

**Types:** `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`

## 🚀 Quick Commands

```bash
# Development
cd ~/development/private/fastapi-keycloak-auth

# Install in editable mode
pip install -e ".[dev]"

# Test
pytest
pytest -v tests/test_specific.py

# Type check
mypy src/

# Lint
ruff check src/
ruff format src/

# Coverage
pytest --cov=src --cov-report=html
```

## 📊 Progress Tracking

Track extraction progress in:
- **Issue #1**: https://github.com/acikabubo/fastapi-keycloak-auth/issues/1
- **DEVELOPMENT.md**: Update status column as modules are completed

## 🔗 Source Project

All code is extracted from:
- **Repository**: https://github.com/acikabubo/fastapi-http-websocket
- **Source issue**: https://github.com/acikabubo/fastapi-http-websocket/issues/139

## ⚡ MVP Scope (Phase 1-2)

Focus on **core authentication only** for MVP:
- ✅ Extract core modules (backend, manager, rbac, dependencies)
- ✅ Create configuration system
- ✅ Add basic tests
- ✅ Type checking with mypy --strict
- ❌ Skip optional extensions (caching, metrics) for now
- ❌ Skip WebSocket support for now (add in Phase 3)

## 🎓 Learning Resources

If unfamiliar with concepts:
- **Starlette AuthenticationBackend**: https://www.starlette.io/authentication/
- **python-keycloak**: https://python-keycloak.readthedocs.io/
- **pydantic-settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **PEP 561 (typed packages)**: https://peps.python.org/pep-0561/

## 💡 Tips for Claude

1. **Read before writing** - Always read source files before extracting
2. **Start simple** - Begin with exceptions.py (easiest module)
3. **Test incrementally** - Run tests after each module extraction
4. **Ask when unsure** - If refactoring approach is unclear, ask for guidance
5. **Follow DEVELOPMENT.md** - It has detailed patterns and examples
6. **Update Issue #1** - Check off items as completed

## 🚫 What NOT to Do

- Don't add new features (just extract existing code)
- Don't optimize prematurely (keep original patterns)
- Don't skip type hints (strict mypy compliance required)
- Don't forget tests (every module needs tests)
- Don't commit broken code (tests must pass)

## 📞 Need Help?

Check existing documentation:
- Review DEVELOPMENT.md for detailed patterns
- Check Issue #1 for extraction checklist
- Look at source files in main project for reference
