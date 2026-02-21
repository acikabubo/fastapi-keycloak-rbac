"""
Data models for fastapi-keycloak-rbac.

Defines UserModel (parsed from Keycloak JWT claims) and TokenClaims TypedDict.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, NewType

from pydantic import BaseModel, Field
from starlette.authentication import AuthCredentials, BaseUser

# ---------------------------------------------------------------------------
# NewTypes
# ---------------------------------------------------------------------------

UserId = NewType("UserId", str)
"""Keycloak subject identifier (UUID string)."""

Username = NewType("Username", str)
"""Keycloak preferred_username value."""

TokenStr = NewType("TokenStr", str)
"""Raw JWT access token string."""


# ---------------------------------------------------------------------------
# AuthResult
# ---------------------------------------------------------------------------


@dataclass
class AuthResult:
    """
    Result of a successful authentication attempt.

    Returned by helpers that authenticate a user and want to carry both
    the Starlette credentials and the parsed user in a single value.

    Attributes:
        credentials: Starlette AuthCredentials (scopes = user roles).
        user: Parsed UserModel instance.
    """

    credentials: AuthCredentials
    user: "UserModel"


# ---------------------------------------------------------------------------
# Token claims
# ---------------------------------------------------------------------------


class TokenClaims(dict[str, Any]):
    """
    Raw token claims dict returned by Keycloak.

    A plain dict subclass used as a type alias for raw JWT payload data.
    """


class UserModel(BaseModel, BaseUser):
    """
    Authenticated user parsed from Keycloak JWT claims.

    Attributes:
        id: Subject identifier (Keycloak user UUID).
        expired_in: Token expiry as a Unix timestamp.
        username: Preferred username from Keycloak.
        roles: Client roles extracted from resource_access claims.
    """

    id: str = Field(..., alias="sub")
    expired_in: int = Field(..., alias="exp")
    username: str = Field(..., alias="preferred_username")
    roles: list[str] = []

    def __init__(self, **kwargs: Any) -> None:
        kwargs["roles"] = (
            kwargs.get("resource_access", {})
            .get(kwargs.get("azp", ""), {})
            .get("roles", [])
        )
        super().__init__(**kwargs)

    @property
    def expired_seconds(self) -> int:
        """Seconds remaining until token expiry (may be negative if expired)."""
        return self.expired_in - int(datetime.now().timestamp())

    def __hash__(self) -> int:
        return hash(self.id)
