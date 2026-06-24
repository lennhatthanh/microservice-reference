from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ..enums import UserRole


class TokenClaims(BaseModel):
    sub: str
    user_id: UUID
    email: str
    role: UserRole
    exp: int
    iat: Optional[int] = None


class AuthUser(BaseModel):
    user_id: UUID
    email: str
    role: UserRole
