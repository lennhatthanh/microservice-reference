from fastapi import FastAPI

from app.api.v1 import auth_routes, user_routes
from app.core.config import settings
from app.infrastructure.broker.workers import start_mq_workers
from app.infrastructure.database.session import engine
from libs.common.database import check_database_ready, run_migrations_if_enabled
from libs.common.exceptions import AppError
from libs.common.logging import CorrelationIdMiddleware, configure_logging
from libs.common.response import app_error_handler, unhandled_error_handler


configure_logging()

app = FastAPI(title="user-service")
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)


@app.on_event("startup")
def on_startup():
    run_migrations_if_enabled(settings.RUN_MIGRATIONS_ON_STARTUP)
    # User service currently publishes UserRegistered through outbox when MQ
    # mode is enabled; in SQLite mode this no-ops.
    start_mq_workers()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "user-service"}


@app.get("/readyz")
def readyz():
    check_database_ready(engine)
    return {"status": "ready", "service": "user-service"}


app.include_router(auth_routes.router)
app.include_router(user_routes.router)
