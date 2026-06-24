# Event Catalog

Business workflow between services should use events from `libs/contracts/events`.

## Base Event Fields

Every integration event extends `IntegrationEvent`.

| Field | Meaning |
| --- | --- |
| `event_id` | Unique event id for tracing and idempotency. |
| `event_type` | Event name, for example `OrderCreated`. |
| `version` | Contract version. Start with `1`. |
| `occurred_at` | UTC time when the event was created. |
| `source` | Service that published the event. |
| `correlation_id` | Request/workflow id shared across events. |
| `causation_id` | Event/message id that caused this event. |

## Events

| Event | Publisher | Consumer | Purpose |
| --- | --- | --- | --- |
| `UserRegistered` | `user-service` | `notification-service` | Send welcome notification or audit log. |
| `OrderCreated` | `order-service` | `product-service`, `payment-service` | Start order workflow. |
| `StockReserved` | `product-service` | `order-service` | Continue order saga after stock is reserved. |
| `StockReservationFailed` | `product-service` | `order-service` | Cancel order when inventory is unavailable. |
| `PaymentSucceeded` | `payment-service` | `order-service`, `notification-service` | Complete order and notify user. |
| `PaymentFailed` | `payment-service` | `order-service`, `product-service`, `notification-service` | Cancel order and release stock. |
| `OrderCompleted` | `order-service` | `notification-service` | Send success notification. |
| `OrderCancelled` | `order-service` | `product-service`, `notification-service` | Release stock if needed and notify user. |

## Example

```py
from libs.contracts.events import OrderCreated, OrderItemPayload


event = OrderCreated(
    order_id=order.id,
    user_id=order.user_id,
    items=[
        OrderItemPayload(
            product_id=item.product_id,
            product_name=item.product_name,
            price=item.price,
            quantity=item.quantity,
        )
    ],
    total_amount=order.total_amount,
    correlation_id=request_id,
)
```

## Rules

- Event contracts live in `libs/contracts/events`.
- Services publish events through outbox, not directly inside business methods.
- Consumers must be idempotent because RabbitMQ messages can be retried.
- Use `event_id` to deduplicate consumed events.
- Add a new event version instead of silently changing payload meaning.
