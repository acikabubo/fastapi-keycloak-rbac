"""Tests for src/config.py"""

import re

import pytest

from fastapi_keycloak_rbac.config import KeycloakAuthSettings, get_settings


class TestKeycloakAuthSettings:
    def test_defaults(self) -> None:
        settings = KeycloakAuthSettings()
        assert settings.server_url == "http://localhost:8080/"
        assert settings.realm == "master"
        assert settings.client_id == ""
        assert settings.admin_username == ""
        assert settings.admin_password == ""
        assert settings.debug is False

    def test_explicit_values(self) -> None:
        settings = KeycloakAuthSettings(
            server_url="http://keycloak:8080/",
            realm="myrealm",
            client_id="myapp",
            admin_username="admin",
            admin_password="secret",
            debug=True,
        )
        assert settings.server_url == "http://keycloak:8080/"
        assert settings.realm == "myrealm"
        assert settings.client_id == "myapp"
        assert settings.admin_username == "admin"
        assert settings.admin_password == "secret"
        assert settings.debug is True

    def test_excluded_paths_default(self) -> None:
        settings = KeycloakAuthSettings()
        pattern = settings.excluded_paths_pattern
        assert pattern.match("/docs")
        assert pattern.match("/health")
        assert pattern.match("/metrics")
        assert pattern.match("/openapi.json")
        assert not pattern.match("/api/users")

    def test_excluded_paths_custom(self) -> None:
        settings = KeycloakAuthSettings(excluded_paths=r"^/public.*$")
        pattern = settings.excluded_paths_pattern
        assert pattern.match("/public/info")
        assert not pattern.match("/private/data")

    def test_excluded_paths_invalid_regex_raises(self) -> None:
        import re

        with pytest.raises(re.error):
            KeycloakAuthSettings(excluded_paths="[invalid")

    def test_excluded_paths_pattern_returns_compiled_regex(self) -> None:
        settings = KeycloakAuthSettings()
        assert isinstance(settings.excluded_paths_pattern, re.Pattern)

    def test_env_var_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KEYCLOAK_AUTH_REALM", "testrealm")
        monkeypatch.setenv("KEYCLOAK_AUTH_CLIENT_ID", "testclient")
        settings = KeycloakAuthSettings()
        assert settings.realm == "testrealm"
        assert settings.client_id == "testclient"


class TestGetSettings:
    def test_returns_settings_instance(self) -> None:
        # Clear lru_cache to avoid state leaking between tests
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, KeycloakAuthSettings)

    def test_returns_same_instance(self) -> None:
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
