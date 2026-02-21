"""
Role-Based Access Control (RBAC) manager for fastapi-keycloak-rbac.

Provides RBACManager for unified permission checking on both HTTP and
WebSocket endpoints.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.authentication import UnauthenticatedUser

from fastapi_keycloak_rbac.models import UserModel

logger = logging.getLogger(__name__)


class RBACManager:
    """
    Manager for Role-Based Access Control (RBAC).

    Provides unified role-based permission checking for both HTTP and
    WebSocket endpoints.

    Can be used via the module-level singleton ``rbac_manager`` or as an
    explicit instance.

    Example::

        from fastapi_keycloak_rbac.rbac import rbac_manager
        from fastapi import APIRouter, Depends

        router = APIRouter()

        @router.get(
            "/authors",
            dependencies=[Depends(rbac_manager.require_roles("get-authors"))],
        )
        async def get_authors():
            return {"authors": []}
    """

    @staticmethod
    def check_user_has_roles(
        user: UserModel, required_roles: list[str]
    ) -> tuple[bool, list[str]]:
        """
        Check if a user has ALL of the required roles.

        Args:
            user: The user to check.
            required_roles: Role names the user must have.

        Returns:
            Tuple of ``(has_permission, missing_roles)``.
        """
        if not required_roles:
            return True, []

        missing_roles = [r for r in required_roles if r not in user.roles]
        return len(missing_roles) == 0, missing_roles

    def check_ws_permission(
        self,
        pkg_id: int,
        user: UserModel,
        permissions_registry: dict[Any, list[str]],
    ) -> bool:
        """
        Check if a user has the required roles for a WebSocket endpoint.

        Args:
            pkg_id: Package ID of the WebSocket handler being accessed.
            user: The authenticated user.
            permissions_registry: Mapping of pkg_id → required role names.

        Returns:
            True if the user has all required roles (or none are required).
        """
        required_roles = permissions_registry.get(pkg_id, [])
        has_permission, missing_roles = self.check_user_has_roles(
            user, required_roles
        )

        if not has_permission:
            logger.info(
                "Permission denied for user %s on pkg_id %s",
                user.username,
                pkg_id,
                extra={
                    "required_roles": required_roles,
                    "user_roles": user.roles,
                    "missing_roles": missing_roles,
                    "pkg_id": pkg_id,
                },
            )

        return has_permission

    def require_roles(
        self, *roles: str
    ) -> Callable[[Request], Awaitable[None]]:
        """
        Create a FastAPI dependency that requires ALL specified roles.

        Args:
            *roles: Role names the authenticated user must have.

        Returns:
            An async dependency function for use with ``Depends()``.

        Raises:
            HTTPException: 401 if user is not authenticated.
            HTTPException: 403 if user lacks required roles.

        Example::

            @router.get(
                "/reports",
                dependencies=[Depends(rbac_manager.require_roles("analyst"))],
            )
            async def get_reports():
                ...
        """

        async def check_roles(request: Request) -> None:
            if (
                isinstance(request.user, UnauthenticatedUser)
                or not request.user
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user: UserModel = request.user
            has_permission, missing_roles = self.check_user_has_roles(
                user, list(roles)
            )

            if not has_permission:
                logger.info(
                    "HTTP permission denied for user %s on %s %s",
                    user.username,
                    request.method,
                    request.url.path,
                    extra={
                        "required_roles": list(roles),
                        "user_roles": user.roles,
                        "missing_roles": missing_roles,
                        "http_method": request.method,
                        "endpoint": str(request.url.path),
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required roles: {', '.join(missing_roles)}",
                )

        return check_roles


# Module-level singleton instance
rbac_manager = RBACManager()
