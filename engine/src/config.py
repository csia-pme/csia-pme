from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///../engine.db"
    database_connect_args: dict[str, bool | str | int] = {"check_same_thread": False}

    class Config:
        env_file = "../.env"


@lru_cache()
def get_settings():
    return Settings()
