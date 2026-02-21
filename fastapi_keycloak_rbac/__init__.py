"""
FastAPI Keycloak Authentication

A FastAPI authentication library with Keycloak integration, featuring:
- HTTP and WebSocket authentication support
- Redis-based token caching
- Prometheus metrics
- Role-based access control (RBAC)
- Type-safe implementation
"""

__version__ = "0.1.1"

from fastapi_keycloak_rbac.backend import AuthBackend
from fastapi_keycloak_rbac.config import KeycloakAuthSettings, get_settings
from fastapi_keycloak_rbac.dependencies import require_roles
from fastapi_keycloak_rbac.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    PermissionDeniedError,
    TokenExpiredError,
)
from fastapi_keycloak_rbac.manager import KeycloakManager, keycloak_manager
from fastapi_keycloak_rbac.models import (
    AuthResult,
    TokenClaims,
    TokenStr,
    UserId,
    UserModel,
    Username,
)
from fastapi_keycloak_rbac.rbac import RBACManager, rbac_manager

__all__ = [
    "__version__",
    "AuthenticationError",
    "AuthorizationError",
    "InvalidTokenError",
    "PermissionDeniedError",
    "TokenExpiredError",
    "AuthResult",
    "TokenClaims",
    "TokenStr",
    "UserId",
    "UserModel",
    "Username",
    "KeycloakAuthSettings",
    "get_settings",
    "KeycloakManager",
    "keycloak_manager",
    "RBACManager",
    "rbac_manager",
    "AuthBackend",
    "require_roles",
]
