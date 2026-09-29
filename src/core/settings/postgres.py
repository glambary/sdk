from pydantic import computed_field
from pydantic_settings import SettingsConfigDict

from core.settings.env import EnvSettings


class ContainerSettings(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    VERSION: str = "18-alpine"


class DatabaseSettings(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    HOST: str
    PORT: int
    NAME: str
    USER: str
    PASSWORD: str

    @computed_field(return_type=str)  # type: ignore[prop-decorator]
    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
