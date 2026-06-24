from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    STOCK_RESERVED = "STOCK_RESERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
