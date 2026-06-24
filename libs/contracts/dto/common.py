from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Money(BaseModel):
    amount: Decimal
    currency: str = "USD"


class Address(BaseModel):
    line1: str
    city: str
    country: str
    line2: Optional[str] = None
    postal_code: Optional[str] = None
