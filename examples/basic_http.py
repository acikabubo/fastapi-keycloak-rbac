"""
Basic HTTP authentication example for fastapi-keycloak-rbac.

Shows how to:
- Add AuthenticationMiddleware with AuthBackend
- Access the authenticated user via request.user
- Protect endpoints with require_roles()
- Provide explicit settings instead of relying on env vars

Run with:
    uvicorn examples.basic_http:app --reload

Then set env vars (or pass settings explicitly):
    export KEYCLOAK_AUTH_SERVER_URL=http://localhost:8080/
    export KEYCLOAK_AUTH_REALM=myrealm
    export KEYCLOAK_AUTH_CLIENT_ID=myapp
"""

from fastapi import Depends, FastAPI, Request
from starlette.middleware.authentication import AuthenticationMiddleware

from fastapi_keycloak_rbac.backend import AuthBackend
from fastapi_keycloak_rbac.dependencies import require_roles
from fastapi_keycloak_rbac.models import UserModel

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="fastapi-keycloak-rbac example")

# Option A: settings from environment variables (KEYCLOAK_AUTH_* prefix)
app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())

# Option B: explicit settings (useful for testing / multiple tenants)
# settings = KeycloakAuthSettings(
#     server_url="http://localhost:8080/",
#     realm="myrealm",
#     client_id="myapp",
#     excluded_paths=r"^(/docs|/openapi.json|/health)$",
# )
# app.add_middleware(AuthenticationMiddleware, backend=AuthBackend(settings=settings))


# ---------------------------------------------------------------------------
# Public endpoint — no authentication required (path is excluded by default)
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Authenticated endpoint — any valid token is accepted
# ---------------------------------------------------------------------------


@app.get("/me")
async def me(request: Request) -> dict[str, object]:
    """Return the authenticated user's profile."""
    user: UserModel = request.user  # type: ignore[assignment]
    return {
        "id": user.id,
        "username": user.username,
        "roles": user.roles,
        "token_expires_in": user.expired_seconds,
    }


# ---------------------------------------------------------------------------
# Role-protected endpoint — requires the "admin" role
# ---------------------------------------------------------------------------


@app.get(
    "/admin",
    dependencies=[Depends(require_roles("admin"))],
)
async def admin_only(request: Request) -> dict[str, str]:
    """Only accessible to users with the 'admin' role."""
    user: UserModel = request.user  # type: ignore[assignment]
    return {"message": f"Welcome, admin {user.username}!"}


# ---------------------------------------------------------------------------
# Multi-role endpoint — requires BOTH "admin" AND "reports" roles
# ---------------------------------------------------------------------------


@app.get(
    "/reports",
    dependencies=[Depends(require_roles("admin", "reports"))],
)
async def reports(request: Request) -> dict[str, str]:
    """Requires both 'admin' and 'reports' roles."""
    user: UserModel = request.user  # type: ignore[assignment]
    return {"message": f"Reports for {user.username}"}
