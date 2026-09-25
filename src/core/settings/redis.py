from pydantic import Field

from core.settings.env import EnvSettings


class RedisSettings(EnvSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = Field(default=6379, gt=0, le=65535)
    REDIS_PASSWORD: str
