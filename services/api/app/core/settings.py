from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV, env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql+psycopg://kursu:kursu_local@127.0.0.1:5432/kursu"
    jwt_secret: SecretStr = SecretStr("")
    app_env: str = "development"
    app_origin: str = "http://localhost:8081"

    @property
    def production(self) -> bool:
        return self.app_env.strip().lower() == "production"
