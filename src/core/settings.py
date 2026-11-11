from functools import cache as cache_func
from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT: str = Field(..., env="BOT")
    EXTERNAL_API_URL: str = Field("http://web_app:8000/", env="EXTERNAL_API_URL")
    EXTERNAL_API_CHECK_ACCESS: str = Field(
        "http://web_app:8000/v1/check_access", env="EXTERNAL_API_CHECK_ACCESS"
    )
    # Сервисная учётка бота для v1/auth/login (кука __Host-cookie-jwt)
    BACKEND_LOGIN: str = Field(default="")
    BACKEND_PASSWORD: str = Field(default="")
    # Кука живёт сутки — обновляем заранее (по умолчанию раз в 23 часа)
    BACKEND_AUTH_REFRESH_SECONDS: int = Field(default=23 * 60 * 60)
    # Имя куки авторизации, которую отдаёт v1/auth/login
    BACKEND_AUTH_COOKIE_NAME: str = Field(default="__Host-cookie-jwt")
    # Пауза перед повторным логином после неудачи (и шаг фонового повтора)
    BACKEND_AUTH_RETRY_SECONDS: int = Field(default=60)
    # Таймаут запросов к бэкенду
    BACKEND_REQUEST_TIMEOUT_SECONDS: int = Field(default=30)

    class Config:
        env_file = ".env"


@cache_func
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
