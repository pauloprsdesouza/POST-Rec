"""Auth, notifications, observability, and application URL settings."""

from pydantic_settings import BaseSettings

from apps.api.shared.settings._common import SHARED_SETTINGS_CONFIG


class PlatformSettings(BaseSettings):
    model_config = SHARED_SETTINGS_CONFIG

    app_env: str = "development"
    app_name: str = "post-rec"
    app_display_name: str = "Researchly"

    log_level: str = "INFO"
    log_format: str = "json"

    otel_service_name: str = "postrec-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_protocol: str = "grpc"
    otel_enabled: bool = False

    auth_enabled: bool = True
    jwt_secret: str = "dev-jwt-secret-change-in-production"
    admin_bootstrap_emails: str = ""

    api_base_url: str = "http://localhost:8000"
    frontend_app_url: str = "http://localhost:5173"
    cors_allowed_origins: str = ""

    evolution_api_url: str = "http://localhost:8080"
    evolution_api_key: str = ""
    evolution_instance_name: str = ""

    phone_default_country_code: str = "55"

    otp_length: int = 6
    otp_ttl_minutes: int = 5
    otp_resend_seconds: int = 60
    otp_max_attempts: int = 5
    whatsapp_notifications_enabled: bool = True

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = "noreply@paulorobertosouza.com.br"
    email_from_name: str = ""

    api_rate_limit_enabled: bool = True
    api_rate_limit_per_minute: int = 120
    auth_rate_limit_per_minute: int = 20
    metrics_token: str = ""
