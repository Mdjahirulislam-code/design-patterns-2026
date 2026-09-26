"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the Smart Greenhouse backend.

    Values come from the process environment or a local .env file.
    """

    database_url: str = (
        "postgresql+psycopg://greenhouse:greenhouse@localhost:5432/greenhouse"
    )

    api_host: str = "0.0.0.0"

    api_port: int = 8000

    # Allow both localhost and 127.0.0.1 frontend origins
    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )


    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            "../.env",
            "../../.env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


    @property
    def cors_origin_list(self) -> list[str]:
        """
        Convert comma separated CORS origins into a list.
        Example:
        "http://localhost:5173,http://127.0.0.1:5173"
        becomes:
        [
          "http://localhost:5173",
          "http://127.0.0.1:5173"
        ]
        """

        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]



@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()



settings = get_settings()