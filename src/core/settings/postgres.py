from pydantic import computed_field

from core.settings.env import EnvSettings


class DatabaseSettings(EnvSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    @computed_field(return_type=str)  # type: ignore[prop-decorator]
    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg:"
            f"//{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
