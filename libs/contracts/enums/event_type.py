from enum import Enum


class EventType(str, Enum):
    USER_REGISTERED = "UserRegistered"
    ORDER_CREATED = "OrderCreated"
    ORDER_COMPLETED = "OrderCompleted"
    ORDER_CANCELLED = "OrderCancelled"
    STOCK_RESERVED = "StockReserved"
    STOCK_RESERVATION_FAILED = "StockReservationFailed"
    PAYMENT_SUCCEEDED = "PaymentSucceeded"
    PAYMENT_FAILED = "PaymentFailed"
