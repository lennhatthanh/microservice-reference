from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime
