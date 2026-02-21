"""
FastAPI dependencies for fastapi-keycloak-rbac.

Convenience wrappers around RBACManager for use with FastAPI's Depends().
"""

from collections.abc import Awaitable, Callable

from fastapi import Request

from fastapi_keycloak_rbac.rbac import rbac_manager


def require_roles(*roles: str) -> Callable[[Request], Awaitable[None]]:
    """
    Create a FastAPI dependency that requires ALL specified roles.

    Convenience wrapper around ``rbac_manager.require_roles()``.

    Args:
        *roles: Role names the authenticated user must have.

    Returns:
        An async dependency function for use with ``Depends()``.

    Raises:
        HTTPException: 401 if not authenticated, 403 if missing roles.

    Example::

        from fastapi import APIRouter, Depends
        from fastapi_keycloak_rbac.dependencies import require_roles

        router = APIRouter()

        @router.get(
            "/authors",
            dependencies=[Depends(require_roles("get-authors"))],
        )
        async def get_authors():
            return {"authors": []}
    """
    return rbac_manager.require_roles(*roles)
