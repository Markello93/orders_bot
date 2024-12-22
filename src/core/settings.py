from functools import cache as cache_func
from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT: str = Field(..., env="BOT")
    EXTERNAL_API_URL: str = Field("http://web_app:8000", env="EXTERNAL_API_URL")
    EXTERNAL_API_CHECK_ACCESS: str = Field(
        "http://web_app:8000/v1/check_access", env="EXTERNAL_API_URL"
    )

    class Config:
        env_file = ".env"


@cache_func
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
