from fastapi import FastAPI

from app.api.v1 import order_routes
from app.core.config import settings
from app.infrastructure.broker.workers import start_mq_workers
from app.infrastructure.database.session import engine
from libs.common.database import check_database_ready, run_migrations_if_enabled
from libs.common.exceptions import AppError
from libs.common.logging import CorrelationIdMiddleware, configure_logging
from libs.common.response import app_error_handler, unhandled_error_handler


configure_logging()

app = FastAPI(title="order-service")
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)


@app.on_event("startup")
def on_startup():
    run_migrations_if_enabled(settings.RUN_MIGRATIONS_ON_STARTUP)
    # Starts background outbox/consumer threads only when ENABLE_MQ=true.
    # SQLite local mode keeps this disabled, while default Compose enables it.
    start_mq_workers()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "order-service"}


@app.get("/readyz")
def readyz():
    check_database_ready(engine)
    return {"status": "ready", "service": "order-service"}


app.include_router(order_routes.router)
