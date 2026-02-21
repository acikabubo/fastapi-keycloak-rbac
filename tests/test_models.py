"""Tests for src/models.py"""

from starlette.authentication import AuthCredentials

from fastapi_keycloak_rbac.models import (
    AuthResult,
    TokenClaims,
    TokenStr,
    UserId,
    UserModel,
    Username,
)

SAMPLE_CLAIMS = {
    "sub": "user-uuid-123",
    "exp": 9999999999,
    "preferred_username": "testuser",
    "azp": "my-client",
    "resource_access": {
        "my-client": {
            "roles": ["admin", "viewer"],
        }
    },
}


class TestUserModel:
    def test_basic_fields(self) -> None:
        user = UserModel(**SAMPLE_CLAIMS)
        assert user.id == "user-uuid-123"
        assert user.expired_in == 9999999999
        assert user.username == "testuser"

    def test_roles_extracted_from_resource_access(self) -> None:
        user = UserModel(**SAMPLE_CLAIMS)
        assert user.roles == ["admin", "viewer"]

    def test_roles_empty_when_azp_missing(self) -> None:
        claims = {**SAMPLE_CLAIMS, "azp": "other-client"}
        user = UserModel(**claims)
        assert user.roles == []

    def test_roles_empty_when_resource_access_missing(self) -> None:
        claims = {k: v for k, v in SAMPLE_CLAIMS.items() if k != "resource_access"}
        user = UserModel(**claims)
        assert user.roles == []

    def test_expired_seconds_positive(self) -> None:
        user = UserModel(**SAMPLE_CLAIMS)
        assert user.expired_seconds > 0

    def test_expired_seconds_negative_when_expired(self) -> None:
        claims = {**SAMPLE_CLAIMS, "exp": 1000}  # far in the past
        user = UserModel(**claims)
        assert user.expired_seconds < 0

    def test_hash_based_on_id(self) -> None:
        user = UserModel(**SAMPLE_CLAIMS)
        assert hash(user) == hash("user-uuid-123")

    def test_two_users_same_id_same_hash(self) -> None:
        user1 = UserModel(**SAMPLE_CLAIMS)
        user2 = UserModel(**SAMPLE_CLAIMS)
        assert hash(user1) == hash(user2)


class TestTokenClaims:
    def test_is_dict_subclass(self) -> None:
        claims: TokenClaims = TokenClaims({"sub": "abc"})
        assert isinstance(claims, dict)

    def test_stores_values(self) -> None:
        claims: TokenClaims = TokenClaims({"sub": "abc", "exp": 123})
        assert claims["sub"] == "abc"
        assert claims["exp"] == 123


class TestNewTypes:
    def test_user_id_is_str(self) -> None:
        uid = UserId("user-uuid-123")
        assert isinstance(uid, str)
        assert uid == "user-uuid-123"

    def test_username_is_str(self) -> None:
        uname = Username("testuser")
        assert isinstance(uname, str)
        assert uname == "testuser"

    def test_token_str_is_str(self) -> None:
        token = TokenStr("eyJhbGciOiJSUzI1NiJ9...")
        assert isinstance(token, str)


class TestAuthResult:
    def test_stores_credentials_and_user(self) -> None:
        user = UserModel(**SAMPLE_CLAIMS)
        creds = AuthCredentials(["admin", "viewer"])
        result = AuthResult(credentials=creds, user=user)
        assert result.credentials is creds
        assert result.user is user

    def test_credentials_scopes(self) -> None:
        user = UserModel(**SAMPLE_CLAIMS)
        creds = AuthCredentials(user.roles)
        result = AuthResult(credentials=creds, user=user)
        assert "admin" in result.credentials.scopes
        assert "viewer" in result.credentials.scopes
