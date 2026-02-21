"""
Configuration for fastapi-keycloak-rbac.

Provides KeycloakAuthSettings, loadable from environment variables or explicit
instantiation. Use get_settings() to get a cached singleton instance.
"""

import re
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakAuthSettings(BaseSettings):
    """
    Settings for Keycloak authentication.

    Can be configured via environment variables (prefixed with KEYCLOAK_AUTH_)
    or by passing values explicitly on instantiation.

    Environment variables:
        KEYCLOAK_AUTH_SERVER_URL     - Keycloak base URL (e.g. http://keycloak:8080/)
        KEYCLOAK_AUTH_REALM          - Realm name
        KEYCLOAK_AUTH_CLIENT_ID      - Client ID for token validation
        KEYCLOAK_AUTH_ADMIN_USERNAME - Admin username (optional, for admin API)
        KEYCLOAK_AUTH_ADMIN_PASSWORD - Admin password (optional, for admin API)
        KEYCLOAK_AUTH_EXCLUDED_PATHS - Regex pattern for paths that skip auth
        KEYCLOAK_AUTH_DEBUG          - Enable debug logging (default: False)

    Example::

        # From env vars
        settings = KeycloakAuthSettings()

        # Explicit
        settings = KeycloakAuthSettings(
            server_url="http://keycloak:8080/",
            realm="myrealm",
            client_id="myapp",
        )
    """

    model_config = SettingsConfigDict(
        env_prefix="KEYCLOAK_AUTH_",
        case_sensitive=False,
    )

    server_url: str = "http://localhost:8080/"
    realm: str = "master"
    client_id: str = ""
    admin_username: str = ""
    admin_password: str = ""
    excluded_paths: str = r"^(/docs|/openapi.json|/health|/metrics)$"
    debug: bool = False

    # Redis token cache (requires fastapi-keycloak-rbac[redis])
    # Leave empty to disable caching.
    redis_url: str = ""
    redis_cache_ttl_buffer: int = 30

    # Prometheus metrics (requires fastapi-keycloak-rbac[metrics])
    metrics_enabled: bool = False

    @field_validator("excluded_paths")
    @classmethod
    def compile_excluded_paths(cls, v: str) -> str:
        """Validate that excluded_paths is a valid regex pattern."""
        re.compile(v)  # raises re.error if invalid
        return v

    @property
    def excluded_paths_pattern(self) -> re.Pattern[str]:
        """Compiled regex pattern for excluded paths."""
        return re.compile(self.excluded_paths)


@lru_cache
def get_settings() -> KeycloakAuthSettings:
    """Return a cached KeycloakAuthSettings instance loaded from environment."""
    return KeycloakAuthSettings()
