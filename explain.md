# Project Explain

Tài liệu này giải thích skeleton repo theo cách dễ đọc cho người mới học
microservices. Hãy xem đây là "bản đồ đường đi" trước khi bắt đầu code.

## Big Picture

Repo này là một ecommerce microservices monorepo:

- `apps/`: source code từng microservice.
- `libs/`: code dùng chung nhưng không chứa business logic.
- `infrastructure/`: local runtime bằng Docker Compose.
- `deploy/`: Kubernetes, ArgoCD, Helm values.
- `terraform/`: AWS infrastructure as code.
- `observability/`: Prometheus và Grafana assets.
- `docs/`: tài liệu kiến trúc, API, event, database.

Rule quan trọng nhất:

```text
Mỗi service tự sở hữu code, database, migration, business logic của nó.
Service khác muốn giao tiếp thì dùng REST hoặc event qua RabbitMQ.
Không import code business trực tiếp từ service khác.
```

## Root Files

| Path | Dùng để làm gì |
| --- | --- |
| `README.md` | Tài liệu chính: goal, boundary, pattern, flow, team split. |
| `explain.md` | File bạn đang đọc: giải thích skeleton và pseudocode mẫu. |
| `.gitignore` | Chặn commit file local/secrets/cache/build/state. |
| `.env.example` | Mẫu biến môi trường. Commit file này, không commit `.env`. |
| `docker-compose.yml` | Chạy local services và dependencies sau này. |
| `Makefile` | Gom lệnh tiện ích như run/test/lint/migrate sau này. |
| `gpt.md` | Draft/notes ban đầu. Có thể giữ nếu team muốn trace ý tưởng. |

## Apps

`apps/` chứa từng microservice. Mỗi folder bên trong nên được xem như một app
riêng, có thể chạy/test/deploy độc lập.

| Path | Boundary |
| --- | --- |
| `apps/api-gateway` | Cửa vào HTTP, route request tới service phù hợp. |
| `apps/user-service` | User, auth, JWT, profile, role. |
| `apps/product-service` | Product, category, stock, stock reservation. |
| `apps/order-service` | Order lifecycle, CQRS, saga orchestration. |
| `apps/payment-service` | Fake payment processing và payment events. |
| `apps/notification-service` | Consume events và gửi fake notification/log. |

## Standard Service Layout

Ví dụ với `apps/order-service`, các service khác cũng theo cùng ý tưởng.

| Path | Ý nghĩa |
| --- | --- |
| `app/main.py` | Tạo FastAPI app, include routes, setup startup/shutdown. |
| `app/api/v1/*.py` | HTTP route/controller. Nhận request, gọi application layer. |
| `app/schemas/` | DTO request/response cho API. Không đặt business rule phức tạp ở đây. |
| `app/core/config.py` | Đọc env/config như DB URL, RabbitMQ URL, JWT secret. |
| `app/core/security.py` | Auth/JWT/password helper nếu service cần. |
| `app/core/logger.py` | Logger setup. |
| `app/domain/entities/` | Entity business cốt lõi: `Order`, `Product`, `User`, ... |
| `app/domain/events/` | Domain event service tạo ra: `OrderCreated`, `PaymentFailed`, ... |
| `app/domain/repositories.py` | Interface/contract repository. Domain biết "cần lưu", không biết SQL. |
| `app/domain/exceptions/` | Lỗi business như `OutOfStock`, `OrderAlreadyCancelled`. |
| `app/domain/value_objects/` | Kiểu nhỏ bất biến như Money, Email, Address nếu cần. |
| `app/application/commands/` | Use case ghi dữ liệu: create/cancel/complete. |
| `app/application/queries/` | Use case đọc dữ liệu: get/list. |
| `app/application/handlers/` | Xử lý command/event message. |
| `app/application/services/` | Điều phối use case, gọi repo, tạo event. |
| `app/application/sagas/` | Điều phối workflow dài, chủ yếu ở `order-service`. |
| `app/infrastructure/database/base.py` | SQLAlchemy `Base`. |
| `app/infrastructure/database/session.py` | Tạo DB engine/session dependency. |
| `app/infrastructure/database/models.py` | SQLAlchemy ORM models/tables. |
| `app/infrastructure/repositories/` | Repository implement thật bằng SQLAlchemy. |
| `app/infrastructure/broker/` | RabbitMQ publisher/consumer adapter. |
| `app/infrastructure/outbox/` | Lưu/publish event theo Outbox Pattern. |
| `alembic/` | Migration riêng của service. |
| `tests/` | Test riêng của service. |
| `Dockerfile` | Build image riêng cho service. |
| `pyproject.toml` | Dependencies/tool config riêng cho service. |
| `README.md` | Note riêng của service. |

## How A REST Request Should Flow

Ví dụ create order:

```text
Client
  -> API Gateway
  -> order-service route
  -> schema validate
  -> application command/service
  -> domain entity/business rule
  -> repository
  -> database
  -> response schema
```

Pseudocode:

```py
# app/api/v1/order_routes.py
@router.post("/orders")
def create_order(payload: CreateOrderRequest, service: OrderService = Depends()):
    command = CreateOrderCommand(
        user_id=payload.user_id,
        items=payload.items,
    )
    order = service.create_order(command)
    return OrderResponse.from_entity(order)
```

```py
# app/application/services/order_service.py
class OrderService:
    def create_order(self, command):
        order = Order.create(
            user_id=command.user_id,
            items=command.items,
        )

        self.order_repo.save(order)
        self.outbox_repo.add(OrderCreated.from_order(order))
        self.unit_of_work.commit()

        return order
```

## Command vs Query

Command là hành động làm thay đổi state.

```text
CreateOrderCommand
CancelOrderCommand
CompleteOrderCommand
ReserveStockCommand
ProcessPaymentCommand
```

Query là hành động đọc dữ liệu, không thay đổi state.

```text
GetOrderQuery
ListUserOrdersQuery
ListProductsQuery
GetProductQuery
```

Pseudocode query:

```py
# app/application/queries/list_user_orders.py
class ListUserOrdersQuery:
    def __init__(self, user_id, page, page_size):
        self.user_id = user_id
        self.page = page
        self.page_size = page_size


class ListUserOrdersHandler:
    def __init__(self, read_repo):
        self.read_repo = read_repo

    def handle(self, query):
        return self.read_repo.list_by_user(
            user_id=query.user_id,
            page=query.page,
            page_size=query.page_size,
        )
```

## Repository Pattern

Domain định nghĩa interface, infrastructure implement chi tiết DB.

```py
# app/domain/repositories.py
class OrderRepository:
    def save(self, order):
        raise NotImplementedError

    def get_by_id(self, order_id):
        raise NotImplementedError
```

```py
# app/infrastructure/repositories/order_repository.py
class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, db):
        self.db = db

    def save(self, order):
        model = OrderModel.from_entity(order)
        self.db.add(model)

    def get_by_id(self, order_id):
        model = self.db.query(OrderModel).filter_by(id=order_id).first()
        return model.to_entity() if model else None
```

## RabbitMQ Event Flow

RabbitMQ dùng cho workflow giữa service.

```text
order-service publishes OrderCreated
product-service consumes OrderCreated
product-service publishes StockReserved or StockReservationFailed
order-service consumes stock result
payment-service processes payment
payment-service publishes PaymentSucceeded or PaymentFailed
order-service completes/cancels order
notification-service sends fake notification
```

Pseudocode consumer:

```py
# product-service/app/application/handlers/order_created_handler.py
class OrderCreatedHandler:
    def handle(self, event):
        reservation = self.stock_service.reserve(
            order_id=event.order_id,
            items=event.items,
        )

        if reservation.ok:
            self.outbox.add(StockReserved(order_id=event.order_id))
        else:
            self.outbox.add(StockReservationFailed(order_id=event.order_id))

        self.unit_of_work.commit()
```

## Outbox Pattern

Không publish event trực tiếp ngay giữa transaction business. Hãy lưu event vào
`outbox_events`, commit DB, rồi publisher job đọc ra publish RabbitMQ.

Vì sao cần vậy:

```text
Nếu DB commit thành công nhưng publish RabbitMQ fail,
event vẫn còn trong outbox để retry.
```

Pseudocode:

```py
def create_order(command):
    order = Order.create(command)
    db.save(order)
    db.save_outbox_event(OrderCreated(order.id))
    db.commit()


def outbox_publisher_loop():
    events = db.get_pending_outbox_events()

    for event in events:
        rabbitmq.publish(event.type, event.payload)
        event.mark_as_published()

    db.commit()
```

## Saga Pattern

`order-service` là saga orchestrator. Nó không tự trừ stock hoặc charge tiền,
nó ra lệnh bằng event và phản ứng theo event trả về.

```text
Create Order
  -> OrderCreated
  -> Product reserves stock
  -> StockReserved
  -> Payment processes payment
  -> PaymentSucceeded
  -> OrderCompleted
```

Failure flow:

```text
Create Order
  -> StockReserved
  -> PaymentFailed
  -> OrderCancelled
  -> Product releases stock
```

Pseudocode:

```py
class OrderSaga:
    def on_stock_reserved(self, event):
        self.outbox.add(ProcessPaymentRequested(order_id=event.order_id))
        self.unit_of_work.commit()

    def on_stock_reservation_failed(self, event):
        order = self.order_repo.get_by_id(event.order_id)
        order.cancel(reason="OUT_OF_STOCK")
        self.outbox.add(OrderCancelled(order_id=order.id))
        self.unit_of_work.commit()

    def on_payment_succeeded(self, event):
        order = self.order_repo.get_by_id(event.order_id)
        order.complete()
        self.outbox.add(OrderCompleted(order_id=order.id))
        self.unit_of_work.commit()

    def on_payment_failed(self, event):
        order = self.order_repo.get_by_id(event.order_id)
        order.cancel(reason="PAYMENT_FAILED")
        self.outbox.add(OrderCancelled(order_id=order.id))
        self.unit_of_work.commit()
```

## Libs

| Path | Dùng để làm gì |
| --- | --- |
| `libs/common/config` | Helper config chung nếu thật sự cần. |
| `libs/common/logging` | Logger setup dùng lại. |
| `libs/common/exceptions` | Base exception chung. |
| `libs/common/pagination` | Pagination helper. |
| `libs/common/response` | Response envelope chung. |
| `libs/contracts/events` | Event schema dùng giữa service. |
| `libs/contracts/dto` | DTO dùng chung ở contract boundary. |
| `libs/contracts/enums` | Enum chung như event type/status. |

Không để business logic trong `libs/`.

```text
OK: Event schema, enum, response helper.
Not OK: OrderService, ProductRepository, User business rules.
```

Response APIs should reuse `ApiResponse[T]`:

```py
from libs.common.response import ApiResponse


return ApiResponse[OrderResponse].ok(data=order_response)
```

FastAPI services should also reuse the shared setup:

```py
from fastapi import FastAPI

from libs.common.exceptions import AppError
from libs.common.logging import CorrelationIdMiddleware, configure_logging
from libs.common.response import app_error_handler, unhandled_error_handler


configure_logging()

app = FastAPI(title="user-service")
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
```

Common exceptions:

```py
from libs.common.exceptions import NotFoundError, ValidationError


raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
raise ValidationError("Quantity must be greater than zero", code="INVALID_QUANTITY")
```

Pagination:

```py
from libs.common.pagination import PaginationParams, build_page_meta


params = PaginationParams(page=1, page_size=20)
items, total = repo.list(offset=params.offset, limit=params.limit)
meta = build_page_meta(params.page, params.page_size, total)
```

## Infrastructure

`infrastructure/` dùng cho local Docker Compose support.

| Path | Dùng để làm gì |
| --- | --- |
| `infrastructure/nginx/nginx.conf` | Local gateway/reverse proxy config. |
| `infrastructure/postgres/init.sql` | Init database/users/schema cho local Postgres. |
| `infrastructure/rabbitmq/definitions.json` | RabbitMQ exchange/queue/binding definitions. |
| `infrastructure/scripts/create-dbs.sql` | Script tạo DB riêng cho từng service. |
| `infrastructure/scripts/wait-for-it.sh` | Helper đợi dependency sẵn sàng. |

## Terraform

`terraform/` dùng để tạo AWS infrastructure.

| Path | Dùng để làm gì |
| --- | --- |
| `terraform/envs/dev` | Entry point Terraform cho môi trường dev. |
| `terraform/envs/prod` | Entry point Terraform cho môi trường prod. |
| `terraform/modules/vpc` | Network: VPC, subnet, route table. |
| `terraform/modules/security-groups` | Firewall rules. |
| `terraform/modules/ec2-k8s-node` | EC2 node cho self-hosted Kubernetes. |
| `terraform/modules/iam` | IAM roles/policies. |
| `terraform/modules/route53` | DNS records nếu dùng domain. |

Rule:

```text
Terraform tạo infra.
Terraform không deploy app business trực tiếp.
App deploy nên do ArgoCD sync từ deploy/.
```

## Deploy

`deploy/` là desired state cho Kubernetes/GitOps.

| Path | Dùng để làm gì |
| --- | --- |
| `deploy/k8s/base` | Manifest gốc dùng chung cho service. |
| `deploy/k8s/overlays/dev` | Patch/config riêng cho dev. |
| `deploy/k8s/overlays/prod` | Patch/config riêng cho prod. |
| `deploy/argocd/projects` | ArgoCD AppProject. |
| `deploy/argocd/applications` | ArgoCD Application/App of Apps. |
| `deploy/helm-values/*` | Values cho ingress, cert-manager, Prometheus, Grafana, RabbitMQ, Postgres. |

Pseudocode GitOps:

```text
Developer pushes code
CI builds Docker image
CI updates image tag in deploy/k8s overlay
ArgoCD sees Git change
ArgoCD syncs Kubernetes cluster
```

## Observability

| Path | Dùng để làm gì |
| --- | --- |
| `observability/prometheus/rules` | Recording rules: tính metric tổng hợp. |
| `observability/prometheus/alerts` | Alert rules: service down, high error, queue stuck. |
| `observability/grafana/datasources` | Datasource config, ví dụ Prometheus. |
| `observability/grafana/dashboards` | Dashboard JSON sau này. |

Pseudocode monitoring mindset:

```text
Service exposes /metrics
Prometheus scrapes /metrics
Prometheus evaluates alerts
Grafana reads Prometheus
Team watches dashboard and alerts
```

## Docs

| Path | Dùng để làm gì |
| --- | --- |
| `docs/architecture.md` | Kiến trúc tổng quan. |
| `docs/api-contracts.md` | API endpoints/request/response. |
| `docs/event-catalog.md` | Danh sách event, payload, publisher, consumer. |
| `docs/saga-flow.md` | Chi tiết order saga. |
| `docs/db-schema.md` | Database schema từng service. |
| `docs/sequence-diagrams.md` | Sequence diagram cho request/event flow. |
| `docs/platform.md` | AWS/K8s platform notes. |
| `docs/gitops.md` | ArgoCD/GitOps notes. |
| `docs/observability.md` | Prometheus/Grafana notes. |

## Newbie Checklist

Khi bắt đầu implement một feature, đi theo thứ tự này:

```text
1. Xác định feature thuộc service nào.
2. Thêm/sửa schema request/response trong app/schemas.
3. Thêm route trong app/api/v1.
4. Thêm command hoặc query trong app/application.
5. Viết business rule trong app/domain.
6. Lưu DB qua repository interface.
7. Implement repository ở app/infrastructure.
8. Nếu cần event, định nghĩa contract trong libs/contracts/events.
9. Ghi event vào outbox, không publish trực tiếp trong transaction.
10. Update docs liên quan.
```

Nếu chưa chắc code nên nằm ở đâu, hỏi câu này:

```text
Nó là business rule, API shape, DB detail, hay deployment config?
```

Sau đó đặt file theo câu trả lời:

- Business rule -> `domain/`
- Use case -> `application/`
- HTTP input/output -> `api/` và `schemas/`
- DB/RabbitMQ detail -> `infrastructure/`
- Shared contract -> `libs/contracts/`
- Local runtime -> `infrastructure/`
- Kubernetes/GitOps -> `deploy/`
- AWS infra -> `terraform/`
- Monitoring -> `observability/`
