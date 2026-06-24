# API Contracts

This project should use one response envelope across services so frontend and
service clients do not need to handle five different response shapes.

## Standard Response

Use `ApiResponse[T]` from `libs/common/response`.

```py
from libs.common.response import ApiResponse


@router.get("/orders/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order(order_id: UUID):
    order = service.get_order(order_id)
    return ApiResponse[OrderResponse].ok(data=OrderResponse.from_entity(order))
```

JSON shape:

```json
{
  "success": true,
  "message": "OK",
  "data": {},
  "errors": [],
  "meta": null
}
```

## Error Response

```py
from libs.common.response import ApiResponse, ErrorDetail


return ApiResponse.fail(
    message="Validation failed",
    errors=[
        ErrorDetail(
            code="INVALID_ORDER_STATUS",
            message="Order cannot be cancelled after completion",
            field="status",
        )
    ],
)
```

JSON shape:

```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": [
    {
      "code": "INVALID_ORDER_STATUS",
      "message": "Order cannot be cancelled after completion",
      "field": "status"
    }
  ],
  "meta": null
}
```

## Paginated Response

```py
from libs.common.response import ApiResponse, PageMeta


return ApiResponse[list[OrderResponse]].ok(
    data=orders,
    meta=PageMeta(
        page=1,
        page_size=20,
        total_items=120,
        total_pages=6,
    ),
)
```

## Rules

- Route files return `ApiResponse[T]`.
- `data` contains the real payload.
- `errors` contains machine-readable error details.
- `meta` is used for pagination or response-level metadata.
- Do not return raw ORM models from APIs.
- Do not expose internal domain entities directly if the public API needs a
  stable shape. Convert to schemas first.
- Shared auth payloads such as `TokenClaims` and `AuthUser` live in
  `libs/contracts/dto/auth.py`; JWT issuing/verification logic still belongs to
  `user-service` or gateway/security code.

## Standard FastAPI Setup

Each service can wire the shared middleware and handlers in `app/main.py`.

```py
from fastapi import FastAPI

from libs.common.exceptions import AppError
from libs.common.logging import CorrelationIdMiddleware, configure_logging
from libs.common.response import app_error_handler, unhandled_error_handler


configure_logging()

app = FastAPI(title="order-service")
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
```

Then application code can raise shared errors:

```py
from libs.common.exceptions import NotFoundError


raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
```

The HTTP response still follows the same `ApiResponse` shape.
