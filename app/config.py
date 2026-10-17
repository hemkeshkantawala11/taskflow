"""All runtime settings come from environment variables (12-factor style).

In Kubernetes, non-secret values come from a ConfigMap, the database password
from a Secret, and build metadata (version, git SHA) is baked into the image at
build time by CI.
"""

import os
from dataclasses import dataclass

from psycopg.conninfo import make_conninfo


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "taskflow")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_pool_max: int = int(os.getenv("DB_POOL_MAX", "5"))
    db_timeout_seconds: float = float(os.getenv("DB_TIMEOUT_SECONDS", "3"))

    app_version: str = os.getenv("APP_VERSION", "dev")
    git_sha: str = os.getenv("GIT_SHA", "unknown")
    build_time: str = os.getenv("BUILD_TIME", "unknown")
    pod_name: str = os.getenv("POD_NAME", os.getenv("HOSTNAME", "local"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    otel_enabled: bool = _env_bool("OTEL_ENABLED", False)

    # Fraction (0.0-1.0) of /api requests that deliberately fail with HTTP 500.
    # Used only to demonstrate alerting and recovery. Must be 0 in normal use.
    chaos_error_rate: float = float(os.getenv("CHAOS_ERROR_RATE", "0"))

    @property
    def conninfo(self) -> str:
        # make_conninfo quotes values safely (e.g. passwords with spaces).
        return make_conninfo(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            connect_timeout=max(1, int(self.db_timeout_seconds)),
            application_name="taskflow",
        )


settings = Settings()
