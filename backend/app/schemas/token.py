from pydantic import BaseModel


class Token(BaseModel):
    """Schema for returning access token to client."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema representing decoded JWT payload."""

    sub: str | None = None
    exp: int | None = None
    type: str | None = None
