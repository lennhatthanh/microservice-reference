from libs.common.config import get_bool_env, get_env, get_int_env, get_required_env


class Settings:
    SERVICE_NAME = "user-service"
    DATABASE_URL = get_required_env("DATABASE_URL")
    JWT_SECRET_KEY = get_required_env("JWT_SECRET_KEY")
    JWT_EXPIRE_MINUTES = get_int_env("JWT_EXPIRE_MINUTES", 1440)
    RABBITMQ_URL = get_env("RABBITMQ_URL", "")
    ENABLE_MQ = get_bool_env("ENABLE_MQ", False)
    RUN_MIGRATIONS_ON_STARTUP = get_bool_env("RUN_MIGRATIONS_ON_STARTUP", False)


settings = Settings()
