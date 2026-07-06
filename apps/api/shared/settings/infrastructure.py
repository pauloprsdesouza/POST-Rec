"""Database, messaging, object storage, and cache settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings

from apps.api.shared.settings._common import SHARED_SETTINGS_CONFIG


class InfrastructureSettings(BaseSettings):
    model_config = SHARED_SETTINGS_CONFIG

    database_url: str = "postgresql+psycopg://postrec:postrec@localhost:5432/postrec"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 1800

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "postrec"
    rabbitmq_password: str = ""
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    redis_url: str = ""

    cache_enabled: bool = True
    cache_redis_db: int = 2
    cache_key_prefix: str = "postrec:cache:v1"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_use_ssl: bool = False
    minio_bucket: str = "postrec-artifacts"

    @field_validator("database_url", "redis_url", "celery_broker_url", "celery_result_backend", mode="before")
    @classmethod
    def strip_connection_urls(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value
