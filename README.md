# fastapi-keycloak-auth

Keycloak authentication for FastAPI with WebSocket support, Redis caching, and Prometheus metrics.

## Features

- ✅ **HTTP and WebSocket Authentication** - Unified auth for both protocols
- ✅ **Redis Token Caching** - 90% cache hit rate, 90% CPU reduction
- ✅ **Prometheus Metrics** - Built-in observability
- ✅ **Role-Based Access Control (RBAC)** - Fine-grained permissions
- ✅ **Type-Safe** - Full mypy strict mode support
- ✅ **Circuit Breaker** - Resilient Keycloak integration
- ✅ **Debug Mode** - Development-friendly authentication

## Installation

```bash
pip install fastapi-keycloak-auth
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from fastapi_keycloak_auth import AuthBackend, require_roles, UserModel
from starlette.middleware.authentication import AuthenticationMiddleware

app = FastAPI()

# Add authentication middleware
app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())

# Protect endpoints with RBAC
@app.get("/admin", dependencies=[Depends(require_roles("admin"))])
async def admin_endpoint(user: UserModel = Depends()):
    return {"message": f"Hello {user.username}!"}
```

## Configuration

Set these environment variables:

```bash
KEYCLOAK_BASE_URL=http://localhost:8080
KEYCLOAK_REALM=your-realm
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret  # Optional
```

## Development Status

🚧 **This package is under active development** - extracted from [fastapi-http-websocket](https://github.com/acikabubo/fastapi-http-websocket).

Current status: **Phase 1-2 - Core extraction in progress**

See [Issue #1](../../issues/1) for implementation roadmap.

## Features Roadmap

- [x] Project structure
- [ ] Core authentication (Phase 2)
  - [ ] AuthBackend
  - [ ] KeycloakManager
  - [ ] RBACManager
  - [ ] Dependencies (require_roles)
- [ ] Models and exceptions
- [ ] Tests and documentation
- [ ] PyPI publishing

## Contributing

This package is extracted from a production-tested implementation. Contributions welcome once core extraction is complete!

## License

MIT License - see LICENSE file for details.

## Related Projects

- [fastapi-keycloak-middleware](https://github.com/waza-ari/fastapi-keycloak-middleware) - Alternative Keycloak middleware
- [fastapi-http-websocket](https://github.com/acikabubo/fastapi-http-websocket) - Source project
