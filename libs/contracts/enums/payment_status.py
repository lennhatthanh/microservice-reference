from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
