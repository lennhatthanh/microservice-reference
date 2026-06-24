# Clone and Run Instructions

This guide is for a fresh clone on Windows PowerShell. It starts the full local
microservices runtime with PostgreSQL, RabbitMQ, API Gateway, Swagger, and the
optional React demo UI.

## 1. Requirements

Install these first:

- Git
- Docker Desktop
- Node.js 20+ and npm

Check versions:

```powershell
git --version
docker --version
docker compose version
node --version
npm --version
```

## 2. Clone

```powershell
git clone https://github.com/lennhatthanh/microservice-reference.git
cd microservice-reference
```

## 3. Create Local Environment File

```powershell
Copy-Item .env.example .env
```

For local learning, the default `.env.example` values are enough.

## 4. Start Full Local Stack

This starts:

- PostgreSQL
- RabbitMQ
- API Gateway
- user/product/order/payment/notification services
- Alembic migrations on startup
- MQ workers for async saga

```powershell
docker compose up -d --build
```

If images were already built:

```powershell
docker compose up -d
```

## 5. Check Containers

```powershell
docker compose ps
```

Expected important statuses:

- `postgres` is `healthy`
- backend services are `healthy`
- `rabbitmq` is `Up`
- `api-gateway` is `Up`

## 6. Check Readiness

```powershell
Invoke-RestMethod http://localhost:8001/readyz
Invoke-RestMethod http://localhost:8002/readyz
Invoke-RestMethod http://localhost:8003/readyz
Invoke-RestMethod http://localhost:8004/readyz
Invoke-RestMethod http://localhost:8005/readyz
```

Each service should return `status: ready`.

## 7. Open Useful URLs

| Component | URL |
| --- | --- |
| API Gateway | `http://localhost:8080` |
| RabbitMQ UI | `http://localhost:15672` |
| User Swagger | `http://localhost:8001/docs` |
| Product Swagger | `http://localhost:8002/docs` |
| Order Swagger | `http://localhost:8003/docs` |
| Payment Swagger | `http://localhost:8004/docs` |
| Notification Swagger | `http://localhost:8005/docs` |

RabbitMQ login:

```text
username: ecommerce
password: ecommerce_password
```

## 8. Run React Demo UI

Open a second PowerShell terminal:

```powershell
cd frontend/react-app
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The React app calls the API Gateway at `http://localhost:8080`.

## 9. Smoke Test Sync Order Flow

Run this from the repo root:

```powershell
$base = "http://localhost:8080"
$suffix = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

$user = Invoke-RestMethod -Method Post -Uri "$base/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body (@{
    email = "sync$suffix@example.com"
    password = "Password123!"
    full_name = "Sync User"
  } | ConvertTo-Json)

$category = Invoke-RestMethod -Method Post -Uri "$base/api/v1/categories" `
  -ContentType "application/json" `
  -Body (@{ name = "Sync Category $suffix" } | ConvertTo-Json)

$product = Invoke-RestMethod -Method Post -Uri "$base/api/v1/products" `
  -ContentType "application/json" `
  -Body (@{
    name = "Sync Product $suffix"
    price = 12.5
    stock = 3
    category_id = $category.data.id
  } | ConvertTo-Json)

$order = Invoke-RestMethod -Method Post -Uri "$base/api/v1/orders" `
  -ContentType "application/json" `
  -Body (@{
    user_id = $user.data.id
    items = @(@{
      product_id = $product.data.id
      quantity = 1
    })
  } | ConvertTo-Json -Depth 5)

$order.data.status
```

Expected:

```text
COMPLETED
```

## 10. Smoke Test Async MQ Saga

This validates RabbitMQ, Outbox, Inbox, and the async saga.

```powershell
$base = "http://localhost:8080"
$suffix = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

$user = Invoke-RestMethod -Method Post -Uri "$base/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body (@{
    email = "mq$suffix@example.com"
    password = "Password123!"
    full_name = "MQ User"
  } | ConvertTo-Json)

$category = Invoke-RestMethod -Method Post -Uri "$base/api/v1/categories" `
  -ContentType "application/json" `
  -Body (@{ name = "MQ Category $suffix" } | ConvertTo-Json)

$product = Invoke-RestMethod -Method Post -Uri "$base/api/v1/products" `
  -ContentType "application/json" `
  -Body (@{
    name = "MQ Product $suffix"
    price = 15
    stock = 5
    category_id = $category.data.id
  } | ConvertTo-Json)

$created = Invoke-RestMethod -Method Post -Uri "$base/api/v1/orders/async" `
  -ContentType "application/json" `
  -Body (@{
    user_id = $user.data.id
    items = @(@{
      product_id = $product.data.id
      quantity = 2
    })
  } | ConvertTo-Json -Depth 5)

$orderId = $created.data.id
$status = $created.data.status

for ($i = 0; $i -lt 15; $i++) {
  Start-Sleep -Seconds 2
  $current = Invoke-RestMethod -Method Get -Uri "$base/api/v1/orders/$orderId"
  $status = $current.data.status
  if ($status -ne "PENDING") { break }
}

$status
```

Expected:

```text
COMPLETED
```

## 11. Check RabbitMQ Queues and DLQ

```powershell
docker compose exec rabbitmq rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
```

Expected after successful processing:

```text
product-service.order-created           0
payment-service.stock-reserved          0
order-service.saga-events               0
notification-service.events             0
*.dlq                                   0
```

## 12. View Logs

All services:

```powershell
docker compose logs -f
```

One service:

```powershell
docker compose logs -f order-service
docker compose logs -f product-service
docker compose logs -f payment-service
docker compose logs -f notification-service
```

## 13. Stop Stack

Keep database/RabbitMQ volumes:

```powershell
docker compose down
```

Delete volumes and reset all local data:

```powershell
docker compose down -v
```

## 14. SQLite Fallback

Use this only if Docker Hub cannot pull PostgreSQL or RabbitMQ images.

```powershell
docker compose build
docker compose -f docker-compose.sqlite.yml up -d --force-recreate
```

SQLite fallback is good for REST smoke tests, but it disables the full RabbitMQ
runtime. Use the default `docker-compose.yml` for the real local microservices
flow.

## 15. Common Problems

If a port is already used, stop the old container stack:

```powershell
docker compose down
```

If a service is not healthy:

```powershell
docker compose ps
docker compose logs --tail=120 <service-name>
```

If RabbitMQ messages are stuck:

```powershell
docker compose exec rabbitmq rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
docker compose logs --tail=200 order-service product-service payment-service notification-service
```

If you want a clean retry:

```powershell
docker compose down -v
docker compose up -d --build
```
