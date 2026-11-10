from pathlib import Path
from urllib.parse import quote_plus
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
_base_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_ignore_empty=True,
        extra="ignore",
    )


class DatasSettings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    REDIS_URL:str

    @property
    def POSTGRES_URL(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config=_base_config


class SecuritySettings(BaseSettings):
    JWT_SECRET: str = Field(validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"))
    JWT_ALGORITHM: str = Field(validation_alias=AliasChoices("JWT_ALGORITHM", "ALGORITHM"))

    model_config = _base_config



db_settings = DatasSettings()
security_settings = SecuritySettings()
settings = db_settings

if __name__ == "__main__":
    print(db_settings.model_dump())
    print(security_settings.model_dump())
    print(db_settings.POSTGRES_URL)
