"""
Starlette AuthenticationBackend for fastapi-keycloak-rbac.

Provides AuthBackend, which validates Bearer tokens against Keycloak and
populates request.user with a UserModel on every authenticated request.
"""

import logging
from typing import Any
from urllib.parse import parse_qsl

from fastapi.security.utils import get_authorization_scheme_param
from jwcrypto.jwt import JWTExpired  # type: ignore[import-untyped]
from keycloak.exceptions import KeycloakAuthenticationError
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
)
from starlette.requests import HTTPConnection

from fastapi_keycloak_rbac.config import KeycloakAuthSettings, get_settings
from fastapi_keycloak_rbac.exceptions import AuthenticationError
from fastapi_keycloak_rbac.manager import KeycloakManager, keycloak_manager
from fastapi_keycloak_rbac.models import UserModel

logger = logging.getLogger(__name__)


class AuthBackend(AuthenticationBackend):
    """
    Starlette authentication backend for Keycloak Bearer tokens.

    Validates JWT access tokens on every request using KeycloakManager,
    then populates ``request.user`` with a ``UserModel``.

    HTTP requests with paths matching ``excluded_paths`` are passed through
    without authentication. WebSocket requests extract the token from the
    ``Authorization`` query parameter instead of the header.

    Args:
        settings: Optional settings instance. Falls back to ``get_settings()``.
        manager: Optional ``KeycloakManager`` instance. Falls back to the
                 module-level ``keycloak_manager`` singleton.

    Example::

        from starlette.middleware.authentication import AuthenticationMiddleware
        from fastapi_keycloak_rbac.backend import AuthBackend

        app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())
    """

    def __init__(
        self,
        settings: KeycloakAuthSettings | None = None,
        manager: KeycloakManager | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.manager = manager or keycloak_manager

    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, BaseUser] | None:
        """
        Authenticate an incoming HTTP or WebSocket connection.

        Args:
            conn: The incoming connection (HTTP request or WebSocket).

        Returns:
            ``(AuthCredentials, UserModel)`` on success, ``None`` for excluded
            paths (HTTP only).

        Raises:
            AuthenticationError: On token expiry, invalid credentials, or
                                 decode errors.
        """
        logger.debug("Request type -> %s", conn.scope["type"])

        if conn.scope["type"] == "websocket":
            qs = dict(parse_qsl(conn.scope["query_string"].decode("utf8")))
            auth_header = qs.get("Authorization", "")
        else:
            if self.settings.excluded_paths_pattern.match(conn.url.path):
                return None
            auth_header = conn.headers.get("authorization", "")

        _, access_token = get_authorization_scheme_param(auth_header)

        try:
            user_data: dict[str, Any] = await self.manager.decode_token(
                access_token
            )
            user = UserModel(**user_data)
            return AuthCredentials(user.roles), user

        except JWTExpired as ex:
            logger.error("JWT token expired: %s", ex)
            raise AuthenticationError(f"token_expired: {ex}")

        except KeycloakAuthenticationError as ex:
            logger.error("Invalid credentials: %s", ex)
            raise AuthenticationError(f"invalid_credentials: {ex}")

        except ValueError as ex:
            logger.error("Error decoding auth token: %s", ex)
            raise AuthenticationError(f"token_decode_error: {ex}")
