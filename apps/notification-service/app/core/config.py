from libs.common.config import get_bool_env, get_env, get_required_env


class Settings:
    SERVICE_NAME = "notification-service"
    DATABASE_URL = get_required_env("DATABASE_URL")
    RABBITMQ_URL = get_env("RABBITMQ_URL", "")
    ENABLE_MQ = get_bool_env("ENABLE_MQ", False)
    RUN_MIGRATIONS_ON_STARTUP = get_bool_env("RUN_MIGRATIONS_ON_STARTUP", False)


settings = Settings()
