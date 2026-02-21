"""
Starlette AuthenticationBackend for fastapi-keycloak-rbac.

Provides AuthBackend, which validates Bearer tokens against Keycloak and
populates request.user with a UserModel on every authenticated request.

Optionally integrates Redis token caching and Prometheus metrics when the
corresponding extras are installed and configured.
"""

import logging
import time
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
from fastapi_keycloak_rbac.metrics import (
    record_auth_attempt,
    record_cache_hit,
    record_cache_miss,
    record_keycloak_duration,
    record_token_validation,
)
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

    When ``settings.redis_url`` is set and the ``redis`` extra is installed,
    decoded token claims are cached in Redis to reduce Keycloak round-trips.
    Redis failures are fail-open (authentication falls back to Keycloak).

    When ``settings.metrics_enabled`` is ``True`` and the ``metrics`` extra is
    installed, Prometheus counters and histograms are recorded automatically.

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
        self._cache = self._build_cache()

    def _build_cache(self) -> Any:
        """Return a TokenCache if redis_url is configured, else None."""
        if not self.settings.redis_url:
            return None
        try:
            from fastapi_keycloak_rbac.cache import TokenCache

            return TokenCache(
                redis_url=self.settings.redis_url,
                ttl_buffer=self.settings.redis_cache_ttl_buffer,
            )
        except ImportError:
            logger.warning(
                "redis_url is set but the 'redis' extra is not installed. "
                "Token caching is disabled. "
                "Install it with: pip install fastapi-keycloak-rbac[redis]"
            )
            return None

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

        # --- Cache lookup ---
        if self._cache is not None:
            cached = await self._cache.get_cached_claims(access_token)
            if cached is not None:
                record_cache_hit()
                record_auth_attempt("success")
                user = UserModel(**cached)
                return AuthCredentials(user.roles), user
            record_cache_miss()

        # --- Keycloak validation ---
        t0 = time.monotonic()
        try:
            user_data: dict[str, Any] = await self.manager.decode_token(
                access_token
            )
            record_keycloak_duration("validate_token", time.monotonic() - t0)
            record_token_validation("valid")
            record_auth_attempt("success")

            if self._cache is not None:
                await self._cache.set_cached_claims(access_token, user_data)

            user = UserModel(**user_data)
            return AuthCredentials(user.roles), user

        except JWTExpired as ex:
            record_keycloak_duration("validate_token", time.monotonic() - t0)
            record_token_validation("expired")
            record_auth_attempt("expired")
            logger.error("JWT token expired: %s", ex)
            raise AuthenticationError(f"token_expired: {ex}")

        except KeycloakAuthenticationError as ex:
            record_keycloak_duration("validate_token", time.monotonic() - t0)
            record_token_validation("invalid")
            record_auth_attempt("invalid")
            logger.error("Invalid credentials: %s", ex)
            raise AuthenticationError(f"invalid_credentials: {ex}")

        except ValueError as ex:
            record_keycloak_duration("validate_token", time.monotonic() - t0)
            record_token_validation("error")
            record_auth_attempt("error")
            logger.error("Error decoding auth token: %s", ex)
            raise AuthenticationError(f"token_decode_error: {ex}")
