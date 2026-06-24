from enum import Enum


class StockReservationStatus(str, Enum):
    RESERVED = "RESERVED"
    FAILED = "FAILED"
    RELEASED = "RELEASED"
