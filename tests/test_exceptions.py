"""Tests for src/exceptions.py"""

import pytest

from fastapi_keycloak_rbac.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    PermissionDeniedError,
    TokenExpiredError,
)


class TestAuthenticationError:
    def test_message(self) -> None:
        error = AuthenticationError("Invalid token")
        assert str(error) == "Invalid token"
        assert error.message == "Invalid token"

    def test_status_code(self) -> None:
        assert AuthenticationError.status_code == 401

    def test_is_exception(self) -> None:
        assert isinstance(AuthenticationError("x"), Exception)

    def test_can_be_raised(self) -> None:
        with pytest.raises(AuthenticationError, match="Invalid token"):
            raise AuthenticationError("Invalid token")


class TestTokenExpiredError:
    def test_is_authentication_error(self) -> None:
        assert isinstance(TokenExpiredError("expired"), AuthenticationError)

    def test_status_code(self) -> None:
        assert TokenExpiredError.status_code == 401

    def test_message(self) -> None:
        error = TokenExpiredError("Token has expired")
        assert error.message == "Token has expired"

    def test_can_be_caught_as_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            raise TokenExpiredError("expired")


class TestInvalidTokenError:
    def test_is_authentication_error(self) -> None:
        assert isinstance(InvalidTokenError("bad"), AuthenticationError)

    def test_status_code(self) -> None:
        assert InvalidTokenError.status_code == 401

    def test_message(self) -> None:
        error = InvalidTokenError("Malformed token")
        assert error.message == "Malformed token"

    def test_can_be_caught_as_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            raise InvalidTokenError("bad token")


class TestAuthorizationError:
    def test_message(self) -> None:
        error = AuthorizationError("Permission denied")
        assert str(error) == "Permission denied"
        assert error.message == "Permission denied"

    def test_status_code(self) -> None:
        assert AuthorizationError.status_code == 403

    def test_is_exception(self) -> None:
        assert isinstance(AuthorizationError("x"), Exception)

    def test_can_be_raised(self) -> None:
        with pytest.raises(AuthorizationError, match="Permission denied"):
            raise AuthorizationError("Permission denied")


class TestPermissionDeniedError:
    def test_is_authorization_error(self) -> None:
        assert isinstance(PermissionDeniedError("denied"), AuthorizationError)

    def test_status_code(self) -> None:
        assert PermissionDeniedError.status_code == 403

    def test_message(self) -> None:
        error = PermissionDeniedError("Insufficient roles")
        assert error.message == "Insufficient roles"

    def test_can_be_caught_as_authorization_error(self) -> None:
        with pytest.raises(AuthorizationError):
            raise PermissionDeniedError("denied")
