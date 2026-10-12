from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8080
    agent_profile: str = Field(default="document-chatbot", validation_alias="AGENT_PROFILE")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

    postgres_url: str = Field(
        default="postgresql+psycopg://agent:agent@postgres:5432/agent",
        validation_alias="POSTGRES_URL",
    )
    checkpoint_pool_size: int = Field(default=10, validation_alias="CHECKPOINT_POOL_SIZE")

    ingest_path: Path = Field(default=Path("/ingest"), validation_alias="INGEST_PATH")
    workspace_path: Path = Field(default=Path("/workspace"), validation_alias="WORKSPACE_PATH")

    script_timeout_seconds: int = Field(default=120, validation_alias="SCRIPT_TIMEOUT_SECONDS")
    max_tool_output_chars: int = Field(default=12_000, validation_alias="MAX_TOOL_OUTPUT_CHARS")
    max_write_bytes: int = Field(default=524_288, validation_alias="MAX_WRITE_BYTES")
    max_read_bytes: int = Field(default=524_288, validation_alias="MAX_READ_BYTES")

    config_yaml_path: Path = Field(
        default=Path("config.yaml"),
        validation_alias="CONFIG_YAML_PATH",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_agent_profile(settings: Settings) -> dict:
    """Load examples/<profile>/config.yaml merged with optional runtime override path."""
    path = settings.config_yaml_path
    if not path.is_file():
        repo_root = Path(__file__).resolve().parents[2]
        path = repo_root / "examples" / settings.agent_profile / "config.yaml"
    if not path.is_file():
        return {"name": settings.agent_profile, "graph": "react", "tools": []}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
