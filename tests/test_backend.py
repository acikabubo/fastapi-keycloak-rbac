"""Tests for src/backend.py"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jwcrypto.jwt import JWTExpired
from keycloak.exceptions import KeycloakAuthenticationError
from starlette.authentication import AuthCredentials

from fastapi_keycloak_rbac.backend import AuthBackend
from fastapi_keycloak_rbac.config import KeycloakAuthSettings
from fastapi_keycloak_rbac.exceptions import AuthenticationError
from fastapi_keycloak_rbac.manager import KeycloakManager
from fastapi_keycloak_rbac.models import UserModel

SAMPLE_CLAIMS: dict[str, Any] = {
    "sub": "user-uuid-123",
    "exp": 9999999999,
    "preferred_username": "testuser",
    "azp": "my-client",
    "resource_access": {
        "my-client": {"roles": ["admin", "viewer"]},
    },
}


@pytest.fixture
def settings() -> KeycloakAuthSettings:
    return KeycloakAuthSettings(
        server_url="http://keycloak:8080/",
        realm="testrealm",
        client_id="testclient",
        excluded_paths=r"^(/health|/metrics)$",
    )


@pytest.fixture
def mock_manager() -> KeycloakManager:
    with patch("fastapi_keycloak_rbac.manager.KeycloakOpenID"):
        mgr = KeycloakManager(
            settings=KeycloakAuthSettings(
                server_url="http://keycloak:8080/",
                realm="testrealm",
                client_id="testclient",
            )
        )
    return mgr


@pytest.fixture
def backend(
    settings: KeycloakAuthSettings, mock_manager: KeycloakManager
) -> AuthBackend:
    return AuthBackend(settings=settings, manager=mock_manager)


def make_http_conn(path: str, token: str = "Bearer mytoken") -> MagicMock:
    conn = MagicMock()
    conn.scope = {"type": "http"}
    conn.url.path = path
    conn.headers = {"authorization": token}
    return conn


def make_ws_conn(token: str = "mytoken") -> MagicMock:
    qs = f"Authorization=Bearer+{token}".encode()
    conn = MagicMock()
    conn.scope = {"type": "websocket", "query_string": qs}
    return conn


class TestAuthBackendInit:
    def test_uses_provided_settings_and_manager(
        self,
        settings: KeycloakAuthSettings,
        mock_manager: KeycloakManager,
    ) -> None:
        backend = AuthBackend(settings=settings, manager=mock_manager)
        assert backend.settings is settings
        assert backend.manager is mock_manager

    def test_falls_back_to_defaults(self) -> None:
        mock_settings = KeycloakAuthSettings()
        with (
            patch(
                "fastapi_keycloak_rbac.backend.get_settings",
                return_value=mock_settings,
            ),
            patch(
                "fastapi_keycloak_rbac.backend.keycloak_manager"
            ) as mock_mgr,
        ):
            backend = AuthBackend()
            assert backend.settings is mock_settings
            assert backend.manager is mock_mgr


class TestAuthenticateHTTP:
    @pytest.mark.asyncio
    async def test_returns_none_for_excluded_path(
        self, backend: AuthBackend
    ) -> None:
        conn = make_http_conn("/health")
        result = await backend.authenticate(conn)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_credentials_and_user_on_success(
        self, backend: AuthBackend, mock_manager: KeycloakManager
    ) -> None:
        mock_manager.decode_token = AsyncMock(return_value=SAMPLE_CLAIMS)
        conn = make_http_conn("/api/data")

        result = await backend.authenticate(conn)

        assert result is not None
        creds, user = result
        assert isinstance(creds, AuthCredentials)
        assert isinstance(user, UserModel)
        assert user.username == "testuser"
        assert "admin" in creds.scopes

    @pytest.mark.asyncio
    async def test_raises_on_expired_token(
        self, backend: AuthBackend, mock_manager: KeycloakManager
    ) -> None:
        mock_manager.decode_token = AsyncMock(side_effect=JWTExpired())
        conn = make_http_conn("/api/data")

        with pytest.raises(AuthenticationError, match="token_expired"):
            await backend.authenticate(conn)

    @pytest.mark.asyncio
    async def test_raises_on_invalid_credentials(
        self, backend: AuthBackend, mock_manager: KeycloakManager
    ) -> None:
        mock_manager.decode_token = AsyncMock(
            side_effect=KeycloakAuthenticationError("bad")
        )
        conn = make_http_conn("/api/data")

        with pytest.raises(AuthenticationError, match="invalid_credentials"):
            await backend.authenticate(conn)

    @pytest.mark.asyncio
    async def test_raises_on_decode_error(
        self, backend: AuthBackend, mock_manager: KeycloakManager
    ) -> None:
        mock_manager.decode_token = AsyncMock(
            side_effect=ValueError("cannot decode")
        )
        conn = make_http_conn("/api/data")

        with pytest.raises(AuthenticationError, match="token_decode_error"):
            await backend.authenticate(conn)


class TestAuthenticateWebSocket:
    @pytest.mark.asyncio
    async def test_extracts_token_from_query_string(
        self, backend: AuthBackend, mock_manager: KeycloakManager
    ) -> None:
        mock_manager.decode_token = AsyncMock(return_value=SAMPLE_CLAIMS)
        conn = make_ws_conn("mytoken")

        result = await backend.authenticate(conn)

        assert result is not None
        _, user = result
        assert user.username == "testuser"
        mock_manager.decode_token.assert_called_once_with("mytoken")

    @pytest.mark.asyncio
    async def test_ws_does_not_check_excluded_paths(
        self, backend: AuthBackend, mock_manager: KeycloakManager
    ) -> None:
        mock_manager.decode_token = AsyncMock(return_value=SAMPLE_CLAIMS)
        # WebSocket with a "health" path — should still authenticate
        qs = b"Authorization=Bearer+mytoken"
        conn = MagicMock()
        conn.scope = {"type": "websocket", "query_string": qs}

        result = await backend.authenticate(conn)
        assert result is not None
