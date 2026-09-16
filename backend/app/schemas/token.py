from pydantic import BaseModel


class Token(BaseModel):
    """Schema for returning authentication tokens to client."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access tokens."""

    refresh_token: str


class TokenPayload(BaseModel):
    """Schema representing decoded JWT payload."""

    sub: str | None = None
    exp: int | None = None
    jti: str | None = None
    type: str | None = None
