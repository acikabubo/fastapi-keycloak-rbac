# Development Guide

This guide helps you work on extracting authentication code from the main project.

## Quick Start

```bash
# Navigate to package directory
cd ~/development/private/fastapi-keycloak-rbac

# Install in development mode
pip install -e ".[dev]"

# Run tests (when we have them)
pytest

# Type check
mypy fastapi_keycloak_rbac/

# Lint and format
ruff check fastapi_keycloak_rbac/
ruff format fastapi_keycloak_rbac/
```

## Project Structure

```
fastapi-keycloak-rbac/
├── src/                          # Package source
│   ├── __init__.py               # Public API exports
│   ├── backend.py                # AuthBackend (from app/auth.py)
│   ├── manager.py                # KeycloakManager (from app/managers/keycloak_manager.py)
│   ├── rbac.py                   # RBACManager (from app/managers/rbac_manager.py)
│   ├── dependencies.py           # require_roles() (from app/dependencies/permissions.py)
│   ├── models.py                 # UserModel, TokenClaims (from app/schemas/user.py)
│   ├── exceptions.py             # Auth exceptions (from app/exceptions.py)
│   ├── config.py                 # KeycloakAuthSettings (from app/settings.py)
│   └── py.typed                  # PEP 561 marker
├── tests/
│   ├── conftest.py               # Test fixtures
│   ├── test_*.py                 # Unit tests
│   └── mocks/                    # Test mocks (from tests/mocks/)
└── docs/
    └── quickstart.md             # Usage examples
```

## Source Files Mapping

| Main Project File | Package File | Lines | Status |
|-------------------|--------------|-------|--------|
| `app/auth.py` | `src/backend.py` | 220 | ⏳ TODO |
| `app/managers/keycloak_manager.py` | `src/manager.py` | 144 | ⏳ TODO |
| `app/managers/rbac_manager.py` | `src/rbac.py` | 168 | ⏳ TODO |
| `app/dependencies/permissions.py` | `src/dependencies.py` | 51 | ⏳ TODO |
| `app/schemas/user.py` | `src/models.py` | — | ⏳ TODO |
| `app/exceptions.py` (auth) | `src/exceptions.py` | — | ⏳ TODO |
| `app/settings.py` (auth config) | `src/config.py` | — | ⏳ TODO |

## Extraction Workflow

Follow this order (easiest to hardest):

### 1. Exceptions (Simplest)
```bash
# Read source
cat ~/development/private/fastapi-http-websocket/app/exceptions.py

# Create package file
vim src/fastapi_keycloak_rbac/exceptions.py

# Extract only auth-related exceptions:
# - AuthenticationError
# - PermissionDeniedError
```

### 2. Models
```bash
# Read source
cat ~/development/private/fastapi-http-websocket/app/schemas/user.py

# Extract UserModel and related types
vim src/models.py
```

### 3. Config
```bash
# Read settings
cat ~/development/private/fastapi-http-websocket/app/settings.py

# Extract Keycloak-related settings
vim src/config.py
```

### 4. Backend
```bash
# Read auth backend
cat ~/development/private/fastapi-http-websocket/app/auth.py

# Refactor to remove project dependencies
vim src/backend.py
```

### 5. Manager
```bash
# Read Keycloak manager
cat ~/development/private/fastapi-http-websocket/app/managers/keycloak_manager.py

# Refactor singleton pattern
vim src/manager.py
```

### 6. RBAC
```bash
# Read RBAC manager
cat ~/development/private/fastapi-http-websocket/app/managers/rbac_manager.py

# Decouple from PackageRouter
vim src/rbac.py
```

### 7. Dependencies
```bash
# Read dependencies
cat ~/development/private/fastapi-http-websocket/app/dependencies/permissions.py

# Extract require_roles()
vim src/dependencies.py
```

## Key Refactoring Patterns

### Remove Project-Specific Imports

❌ **Before** (project-specific):
```python
from app.logging import logger
from app.settings import app_settings
from app.utils.metrics import auth_metric
```

✅ **After** (package-generic):
```python
import logging
from fastapi_keycloak_rbac.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
```

### Make Settings Configurable

❌ **Before** (hardcoded):
```python
if app_settings.DEBUG_AUTH:
    logger.debug("Auth bypassed")
```

✅ **After** (configurable):
```python
from fastapi_keycloak_rbac.config import KeycloakAuthSettings

def __init__(self, settings: KeycloakAuthSettings | None = None):
    self.settings = settings or get_settings()

if self.settings.debug_auth:
    logger.debug("Auth bypassed")
```

### Extract Type Definitions

Create `types.py` for NewTypes:
```python
from typing import NewType

UserId = NewType("UserId", str)
Username = NewType("Username", str)
TokenStr = NewType("TokenStr", str)
```

## Testing Strategy

For each module, create corresponding test:

```bash
# Example: after creating exceptions.py
vim tests/test_exceptions.py

# Example test structure
"""
def test_authentication_error():
    error = AuthenticationError("Invalid token")
    assert str(error) == "Invalid token"
    assert error.status_code == 401
"""
```

## Checking Progress

Track your work in:
- **Main checklist**: https://github.com/acikabubo/fastapi-keycloak-rbac/issues/1
- **This file**: Update status column as you complete modules

## Integration Testing

Once core modules are extracted:

```bash
# In main project directory
cd ~/development/private/fastapi-http-websocket

# Install local package
pip install -e ~/development/private/fastapi-keycloak-rbac

# Test import
python -c "from fastapi_keycloak_rbac import AuthBackend; print('Success!')"
```

## Tips

1. **Start small**: Do one module per session
2. **Test frequently**: Run `mypy` and `pytest` after each change
3. **Keep it simple**: Don't add features, just extract existing code
4. **Document changes**: Update this file as you progress
5. **Commit often**: Small commits make it easier to track progress

## Need Help?

Check the source project for context:
```bash
cd ~/development/private/fastapi-http-websocket
gh issue view 139
```

Or the extraction roadmap:
```bash
cd ~/development/private/fastapi-keycloak-rbac
gh issue view 1
```
