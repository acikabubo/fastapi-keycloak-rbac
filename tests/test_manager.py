"""Tests for src/manager.py"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi_keycloak_rbac.config import KeycloakAuthSettings
from fastapi_keycloak_rbac.manager import KeycloakManager


@pytest.fixture
def settings() -> KeycloakAuthSettings:
    return KeycloakAuthSettings(
        server_url="http://keycloak:8080/",
        realm="testrealm",
        client_id="testclient",
    )


@pytest.fixture
def manager(settings: KeycloakAuthSettings) -> KeycloakManager:
    with patch("fastapi_keycloak_rbac.manager.KeycloakOpenID"):
        return KeycloakManager(settings=settings)


class TestKeycloakManagerInit:
    def test_uses_provided_settings(
        self, settings: KeycloakAuthSettings
    ) -> None:
        with patch(
            "fastapi_keycloak_rbac.manager.KeycloakOpenID"
        ) as mock_openid_cls:
            manager = KeycloakManager(settings=settings)
            assert manager.settings is settings
            mock_openid_cls.assert_called_once_with(
                server_url="http://keycloak:8080/",
                client_id="testclient",
                realm_name="testrealm",
            )

    def test_uses_get_settings_when_none_provided(self) -> None:
        mock_settings = KeycloakAuthSettings(
            server_url="http://default:8080/",
            realm="defaultrealm",
            client_id="defaultclient",
        )
        with (
            patch(
                "fastapi_keycloak_rbac.manager.get_settings",
                return_value=mock_settings,
            ),
            patch("fastapi_keycloak_rbac.manager.KeycloakOpenID"),
        ):
            manager = KeycloakManager()
            assert manager.settings is mock_settings

    def test_openid_attribute_set(
        self, settings: KeycloakAuthSettings
    ) -> None:
        with patch(
            "fastapi_keycloak_rbac.manager.KeycloakOpenID"
        ) as mock_openid_cls:
            mock_instance = MagicMock()
            mock_openid_cls.return_value = mock_instance
            manager = KeycloakManager(settings=settings)
            assert manager.openid is mock_instance


class TestLoginAsync:
    @pytest.mark.asyncio
    async def test_returns_token_dict(self, manager: KeycloakManager) -> None:
        expected: dict[str, Any] = {
            "access_token": "abc123",
            "refresh_token": "ref456",
            "expires_in": 300,
        }
        manager.openid.a_token = AsyncMock(return_value=expected)  # type: ignore[attr-defined]

        result = await manager.login_async("user", "pass")

        assert result == expected
        manager.openid.a_token.assert_called_once_with(  # type: ignore[attr-defined]
            username="user", password="pass"
        )

    @pytest.mark.asyncio
    async def test_propagates_exception(
        self, manager: KeycloakManager
    ) -> None:
        from keycloak.exceptions import KeycloakAuthenticationError

        manager.openid.a_token = AsyncMock(  # type: ignore[attr-defined]
            side_effect=KeycloakAuthenticationError("bad credentials")
        )

        with pytest.raises(KeycloakAuthenticationError):
            await manager.login_async("user", "wrong")


class TestDecodeToken:
    @pytest.mark.asyncio
    async def test_returns_claims(self, manager: KeycloakManager) -> None:
        expected: dict[str, Any] = {
            "sub": "user-uuid",
            "exp": 9999999999,
            "preferred_username": "testuser",
        }
        manager.openid.a_decode_token = AsyncMock(return_value=expected)  # type: ignore[attr-defined]

        result = await manager.decode_token("sometoken")

        assert result == expected
        manager.openid.a_decode_token.assert_called_once_with("sometoken")  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_propagates_exception(
        self, manager: KeycloakManager
    ) -> None:
        manager.openid.a_decode_token = AsyncMock(  # type: ignore[attr-defined]
            side_effect=ValueError("token decode error")
        )

        with pytest.raises(ValueError, match="token decode error"):
            await manager.decode_token("badtoken")
