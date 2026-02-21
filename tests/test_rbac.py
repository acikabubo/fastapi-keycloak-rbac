"""Tests for src/rbac.py"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from starlette.authentication import UnauthenticatedUser

from fastapi_keycloak_rbac.models import UserModel
from fastapi_keycloak_rbac.rbac import RBACManager, rbac_manager

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


@pytest.fixture
def rbac() -> RBACManager:
    return RBACManager()


class TestCheckUserHasRoles:
    def test_no_roles_required_grants_access(self, rbac: RBACManager, user: UserModel) -> None:
        has_perm, missing = rbac.check_user_has_roles(user, [])
        assert has_perm is True
        assert missing == []

    def test_user_has_all_roles(self, rbac: RBACManager, user: UserModel) -> None:
        has_perm, missing = rbac.check_user_has_roles(user, ["admin", "viewer"])
        assert has_perm is True
        assert missing == []

    def test_user_missing_one_role(self, rbac: RBACManager, user: UserModel) -> None:
        has_perm, missing = rbac.check_user_has_roles(user, ["admin", "superuser"])
        assert has_perm is False
        assert missing == ["superuser"]

    def test_user_missing_all_roles(self, rbac: RBACManager, user: UserModel) -> None:
        has_perm, missing = rbac.check_user_has_roles(user, ["editor", "superuser"])
        assert has_perm is False
        assert set(missing) == {"editor", "superuser"}

    def test_is_static_method(self) -> None:
        # Can be called without an instance
        user = UserModel(**SAMPLE_CLAIMS)
        has_perm, _ = RBACManager.check_user_has_roles(user, ["admin"])
        assert has_perm is True


class TestCheckWsPermission:
    def test_grants_when_no_roles_required(self, rbac: RBACManager, user: UserModel) -> None:
        registry: dict[int, list[str]] = {1: []}
        assert rbac.check_ws_permission(1, user, registry) is True

    def test_grants_when_pkg_id_not_in_registry(self, rbac: RBACManager, user: UserModel) -> None:
        registry: dict[int, list[str]] = {}
        assert rbac.check_ws_permission(99, user, registry) is True

    def test_grants_when_user_has_roles(self, rbac: RBACManager, user: UserModel) -> None:
        registry: dict[int, list[str]] = {10: ["admin"]}
        assert rbac.check_ws_permission(10, user, registry) is True

    def test_denies_when_user_missing_role(self, rbac: RBACManager, user: UserModel) -> None:
        registry: dict[int, list[str]] = {10: ["superuser"]}
        assert rbac.check_ws_permission(10, user, registry) is False


class TestRequireRoles:
    @pytest.mark.asyncio
    async def test_grants_when_user_has_roles(self, rbac: RBACManager, user: UserModel) -> None:
        request = MagicMock()
        request.user = user

        dep = rbac.require_roles("admin")
        await dep(request)  # should not raise

    @pytest.mark.asyncio
    async def test_raises_403_when_missing_role(self, rbac: RBACManager, user: UserModel) -> None:
        request = MagicMock()
        request.user = user

        dep = rbac.require_roles("superuser")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request)

        assert exc_info.value.status_code == 403
        assert "superuser" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_401_when_unauthenticated(self, rbac: RBACManager) -> None:
        request = MagicMock()
        request.user = UnauthenticatedUser()

        dep = rbac.require_roles("admin")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_grants_when_no_roles_required(self, rbac: RBACManager, user: UserModel) -> None:
        request = MagicMock()
        request.user = user

        dep = rbac.require_roles()
        await dep(request)  # should not raise

    @pytest.mark.asyncio
    async def test_requires_all_roles(self, rbac: RBACManager, user: UserModel) -> None:
        request = MagicMock()
        request.user = user  # has admin, viewer

        dep = rbac.require_roles("admin", "superuser")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request)

        assert exc_info.value.status_code == 403


class TestModuleSingleton:
    def test_rbac_manager_is_rbac_manager_instance(self) -> None:
        assert isinstance(rbac_manager, RBACManager)
