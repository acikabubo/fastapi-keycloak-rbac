"""
Keycloak manager for fastapi-keycloak-rbac.

Provides KeycloakManager for OpenID Connect authentication and token
management against a Keycloak server.
"""

import logging
from typing import Any

from keycloak import KeycloakOpenID

from fastapi_keycloak_rbac.config import KeycloakAuthSettings, get_settings

logger = logging.getLogger(__name__)


class KeycloakManager:
    """
    Manager for Keycloak authentication operations.

    Provides OpenID Connect authentication and token management using the
    python-keycloak library.

    Can be used as an explicit instance (passing settings directly) or via
    the module-level singleton ``keycloak_manager``.

    Example::

        # Explicit instance
        manager = KeycloakManager(settings=KeycloakAuthSettings(
            server_url="http://keycloak:8080/",
            realm="myrealm",
            client_id="myapp",
        ))

        # Module-level singleton (uses env vars / defaults)
        from fastapi_keycloak_rbac.manager import keycloak_manager
    """

    def __init__(self, settings: KeycloakAuthSettings | None = None) -> None:
        """
        Initialize KeycloakManager.

        Args:
            settings: Optional settings instance. If not provided, settings
                      are loaded from environment variables via get_settings().
        """
        self.settings = settings or get_settings()
        self.openid = KeycloakOpenID(
            server_url=self.settings.server_url,
            client_id=self.settings.client_id,
            realm_name=self.settings.realm,
        )
        logger.info(
            "KeycloakManager initialized "
            f"(server_url={self.settings.server_url}, realm={self.settings.realm})"
        )

    async def login_async(
        self, username: str, password: str
    ) -> dict[str, Any]:
        """
        Authenticate a user asynchronously and obtain tokens.

        Uses the native async method from python-keycloak to avoid blocking
        the async event loop.

        Args:
            username: Keycloak username.
            password: Keycloak password.

        Returns:
            Token dict containing ``access_token``, ``refresh_token``,
            ``expires_in``, etc.

        Raises:
            KeycloakAuthenticationError: If authentication fails.

        Example::

            token = await manager.login_async("user", "pass")
            access_token = token["access_token"]
        """
        return await self.openid.a_token(username=username, password=password)

    async def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate a Keycloak access token asynchronously.

        Args:
            token: Raw JWT access token string.

        Returns:
            Decoded token claims dict.

        Raises:
            JWTExpired: If the token has expired.
            KeycloakAuthenticationError: If the token is invalid.
            ValueError: If the token cannot be decoded.
        """
        return await self.openid.a_decode_token(token)


# Module-level singleton — initialized lazily on first import
keycloak_manager = KeycloakManager()
