import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations_if_enabled(enabled: bool, service_root: str | Path = ".") -> None:
    """Run Alembic on startup only when explicitly enabled.

    Production deployments usually run migrations as a separate release step.
    Local Docker can enable this to keep first-run setup painless without
    falling back to SQLAlchemy create_all.
    """

    if not enabled:
        return

    root = Path(service_root)
    config_path = root / "alembic.ini"
    if not config_path.exists():
        raise RuntimeError(f"Alembic config not found: {config_path}")

    logger.info("Running Alembic migrations from %s", config_path)
    command.upgrade(Config(str(config_path)), "head")
