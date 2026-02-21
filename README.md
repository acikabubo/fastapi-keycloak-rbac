# fastapi-keycloak-rbac

Keycloak authentication for FastAPI — role-based access control, type-safe, zero project-specific dependencies.

> 📢 **Hobby Project Notice:** This is a research and learning project exploring FastAPI and Keycloak integration best practices. Feel free to use it as a reference, report issues, or suggest improvements! Contributions and feedback are always welcome.

## ✨ Features

- 🔐 **HTTP Authentication** — Starlette `AuthenticationMiddleware` integration
- 🛡️ **Role-Based Access Control (RBAC)** — `require_roles()` FastAPI dependency
- ⚙️ **Configurable** — env vars or explicit settings via `KeycloakAuthSettings`
- ✅ **Type-Safe** — full `mypy --strict` compliance, `py.typed` marker
- 🔌 **Extensible** — bring your own caching, metrics, and circuit breaker

## 📦 Installation

```bash
pip install fastapi-keycloak-rbac
```

Or in development mode from source:

```bash
git clone https://github.com/acikabubo/fastapi-keycloak-rbac
cd fastapi-keycloak-rbac
pip install -e ".[dev]"
```

## 🚀 Quick Start

```python
from fastapi import Depends, FastAPI, Request
from starlette.middleware.authentication import AuthenticationMiddleware

from fastapi_keycloak_rbac.backend import AuthBackend
from fastapi_keycloak_rbac.dependencies import require_roles
from fastapi_keycloak_rbac.models import UserModel

app = FastAPI()

# Add Keycloak authentication middleware
# Reads KEYCLOAK_AUTH_* environment variables automatically
app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())


@app.get("/me")
async def me(request: Request):
    user: UserModel = request.user
    return {"username": user.username, "roles": user.roles}


@app.get("/admin", dependencies=[Depends(require_roles("admin"))])
async def admin_only(request: Request):
    user: UserModel = request.user
    return {"message": f"Hello, {user.username}!"}
```

## ⚙️ Configuration

### Environment Variables

All settings use the `KEYCLOAK_AUTH_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `KEYCLOAK_AUTH_SERVER_URL` | `http://localhost:8080/` | Keycloak base URL |
| `KEYCLOAK_AUTH_REALM` | `master` | Realm name |
| `KEYCLOAK_AUTH_CLIENT_ID` | _(empty)_ | Client ID for token validation |
| `KEYCLOAK_AUTH_ADMIN_USERNAME` | _(empty)_ | Admin username (optional) |
| `KEYCLOAK_AUTH_ADMIN_PASSWORD` | _(empty)_ | Admin password (optional) |
| `KEYCLOAK_AUTH_EXCLUDED_PATHS` | `^(/docs\|/openapi.json\|/health\|/metrics)$` | Regex of paths that skip auth |
| `KEYCLOAK_AUTH_DEBUG` | `false` | Enable debug logging |

```bash
export KEYCLOAK_AUTH_SERVER_URL=http://keycloak:8080/
export KEYCLOAK_AUTH_REALM=myrealm
export KEYCLOAK_AUTH_CLIENT_ID=myapp
```

### Explicit Settings

```python
from fastapi_keycloak_rbac.backend import AuthBackend
from fastapi_keycloak_rbac.config import KeycloakAuthSettings

settings = KeycloakAuthSettings(
    server_url="http://keycloak:8080/",
    realm="myrealm",
    client_id="myapp",
    excluded_paths=r"^(/docs|/openapi.json|/health)$",
)

app.add_middleware(AuthenticationMiddleware, backend=AuthBackend(settings=settings))
```

## 📖 API Reference

### `AuthBackend`

Starlette `AuthenticationBackend` that validates Keycloak Bearer tokens.

- HTTP: reads `Authorization: Bearer <token>` header
- Paths matching `excluded_paths` are passed through unauthenticated
- Raises `AuthenticationError` on expired/invalid tokens

### `require_roles(*roles)`

FastAPI dependency that enforces role-based access control.

```python
from fastapi import Depends
from fastapi_keycloak_rbac.dependencies import require_roles

@router.get("/reports", dependencies=[Depends(require_roles("analyst", "admin"))])
async def get_reports(): ...
```

Raises `HTTP 401` if unauthenticated, `HTTP 403` if missing any required role.

### `UserModel`

Pydantic model populated from Keycloak JWT claims, available as `request.user`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Keycloak subject UUID (`sub` claim) |
| `username` | `str` | Preferred username |
| `roles` | `list[str]` | Client roles from `resource_access` |
| `expired_in` | `int` | Token expiry Unix timestamp |
| `expired_seconds` | `int` | Seconds until expiry (property) |

### `KeycloakAuthSettings`

Pydantic-settings class for all auth configuration. See env vars table above.

### `RBACManager`

Lower-level RBAC for custom permission checking:

```python
from fastapi_keycloak_rbac.rbac import rbac_manager

has_perm, missing = rbac_manager.check_user_has_roles(user, ["admin"])
```

### ⚠️ Exceptions

| Exception | Status | Description |
|-----------|--------|-------------|
| `AuthenticationError` | 401 | Base auth failure |
| `TokenExpiredError` | 401 | JWT past expiry |
| `InvalidTokenError` | 401 | Malformed / invalid signature |
| `AuthorizationError` | 403 | Base authorization failure |
| `PermissionDeniedError` | 403 | Missing required roles |

## 💡 Examples

See [examples/basic_http.py](examples/basic_http.py) for a full working example.

## 🛠️ Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy fastapi_keycloak_rbac/

# Lint
ruff check fastapi_keycloak_rbac/
ruff format fastapi_keycloak_rbac/
```

## 📊 Status

**Phase 1-2 complete** — core extraction done, 100% test coverage, mypy strict clean.

| Module | Description |
|--------|-------------|
| `exceptions.py` | Auth exceptions |
| `models.py` | `UserModel`, `TokenClaims`, NewTypes, `AuthResult` |
| `config.py` | `KeycloakAuthSettings` |
| `manager.py` | `KeycloakManager` (Keycloak OpenID client) |
| `rbac.py` | `RBACManager` (permission checking) |
| `backend.py` | `AuthBackend` (Starlette middleware) |
| `dependencies.py` | `require_roles()` FastAPI dependency |

See [Issue #1](../../issues/1) for the full roadmap.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🔗 Related Projects

- [fastapi-keycloak-middleware](https://github.com/waza-ari/fastapi-keycloak-middleware) — Alternative Keycloak middleware
- [fastapi-http-websocket](https://github.com/acikabubo/fastapi-http-websocket) — Source project
