"""Tests for src/dependencies.py"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from starlette.authentication import UnauthenticatedUser

from fastapi_keycloak_rbac.dependencies import require_roles
from fastapi_keycloak_rbac.models import UserModel

SAMPLE_CLAIMS = {
    "sub": "user-uuid-123",
    "exp": 9999999999,
    "preferred_username": "testuser",
    "azp": "my-client",
    "resource_access": {
        "my-client": {"roles": ["admin", "viewer"]},
    },
}


@pytest.fixture
def user() -> UserModel:
    return UserModel(**SAMPLE_CLAIMS)


class TestRequireRoles:
    def test_returns_callable(self) -> None:
        dep = require_roles("admin")
        assert callable(dep)

    @pytest.mark.asyncio
    async def test_grants_access_when_user_has_role(
        self, user: UserModel
    ) -> None:
        request = MagicMock()
        request.user = user

        dep = require_roles("admin")
        await dep(request)  # should not raise

    @pytest.mark.asyncio
    async def test_raises_403_when_missing_role(self, user: UserModel) -> None:
        request = MagicMock()
        request.user = user

        dep = require_roles("superuser")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_401_when_unauthenticated(self) -> None:
        request = MagicMock()
        request.user = UnauthenticatedUser()

        dep = require_roles("admin")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_grants_access_with_no_roles_required(
        self, user: UserModel
    ) -> None:
        request = MagicMock()
        request.user = user

        dep = require_roles()
        await dep(request)  # should not raise

    @pytest.mark.asyncio
    async def test_requires_all_roles(self, user: UserModel) -> None:
        request = MagicMock()
        request.user = user  # has admin, viewer — not superuser

        dep = require_roles("admin", "superuser")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request)

        assert exc_info.value.status_code == 403
