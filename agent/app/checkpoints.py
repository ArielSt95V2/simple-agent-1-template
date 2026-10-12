from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from agent.app.config import Settings


def psycopg_conninfo(postgres_url: str) -> str:
    """Turn the SQLAlchemy Postgres URL into a psycopg connection string."""
    url = postgres_url.strip()
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    return url


def open_checkpoint_pool(settings: Settings) -> ConnectionPool:
    """Pool for LangGraph chat checkpoints. Caller must close it on shutdown."""
    pool = ConnectionPool(
        psycopg_conninfo(settings.postgres_url),
        min_size=1,
        max_size=max(1, settings.checkpoint_pool_size),
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        open=False,
    )
    try:
        pool.open(wait=True, timeout=30.0)
    except Exception:
        pool.close()
        raise
    return pool
