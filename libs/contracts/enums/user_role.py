from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
