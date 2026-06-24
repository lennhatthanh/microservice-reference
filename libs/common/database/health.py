from sqlalchemy import text
from sqlalchemy.engine import Engine


def check_database_ready(engine: Engine) -> None:
    """Run a tiny DB query for readiness probes.

    Liveness answers "is the process up"; readiness answers "can this service
    serve traffic safely right now".
    """

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
