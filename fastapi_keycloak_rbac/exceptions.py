"""
Auth exception classes for fastapi-keycloak-rbac.

Defines authentication and authorization exceptions that integrate with
Starlette's authentication middleware.
"""


class AuthenticationError(Exception):
    """
    Authentication failed.

    Raised when user authentication fails (invalid credentials, expired token, etc.).

    HTTP Status: 401 Unauthorized
    """

    status_code: int = 401

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """
    Token has expired.

    Raised when a JWT/access token is past its expiry time.

    HTTP Status: 401 Unauthorized
    """


class InvalidTokenError(AuthenticationError):
    """
    Token is invalid or malformed.

    Raised when a token cannot be decoded or its signature is invalid.

    HTTP Status: 401 Unauthorized
    """


class AuthorizationError(Exception):
    """
    Authorization failed.

    Raised when a user lacks required permissions for an operation.

    HTTP Status: 403 Forbidden
    """

    status_code: int = 403

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PermissionDeniedError(AuthorizationError):
    """
    Permission denied.

    Raised when a user does not have the required role(s) for an operation.

    HTTP Status: 403 Forbidden
    """
