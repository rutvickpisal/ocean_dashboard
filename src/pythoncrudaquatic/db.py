"""Database connection pool and small query helpers."""

from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Read DATABASE_URL from the environment or the .env file."""

    database_url: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)


def fetch_all(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Execute a query and return all rows as dictionaries."""
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Execute a query and return the first row, if present."""
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchone()


def where(conditions: list[str]) -> str:
    """Build a WHERE clause from trusted SQL condition fragments."""
    return "WHERE " + " AND ".join(conditions) if conditions else ""
