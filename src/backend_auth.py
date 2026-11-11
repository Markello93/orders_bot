"""Авторизация бота в бэкенде book-eat и смена статуса заказа с кукой.

POST {EXTERNAL_API_URL}v1/auth/login {"username", "password"} отдаёт куку
BACKEND_AUTH_COOKIE_NAME (живёт сутки). Кука хранится в памяти процесса,
обновляется фоновой задачей раз в BACKEND_AUTH_REFRESH_SECONDS и
перезапрашивается при 401/403. Все параметры — в settings.
"""

from __future__ import annotations

import asyncio
import json as json_lib
import logging
import time
from typing import Any

import aiohttp

from src.core.settings import settings

logger = logging.getLogger(__name__)


class BackendAuthError(RuntimeError):
    pass


def _parse_body(text: str) -> Any:
    if not text:
        return None
    try:
        return json_lib.loads(text)
    except ValueError:
        return text


class BackendAuthClient:
    """Держит куку авторизации и выполняет авторизованные запросы."""

    def __init__(
        self,
        base_url: str | None = None,
        login: str | None = None,
        password: str | None = None,
        refresh_seconds: int | None = None,
    ):
        self.base_url = base_url if base_url is not None else settings.EXTERNAL_API_URL
        self.login = login if login is not None else settings.BACKEND_LOGIN
        self.password = password if password is not None else settings.BACKEND_PASSWORD
        self.refresh_seconds = (
            refresh_seconds
            if refresh_seconds is not None
            else settings.BACKEND_AUTH_REFRESH_SECONDS
        )
        self.cookie_name = settings.BACKEND_AUTH_COOKIE_NAME
        self.retry_seconds = settings.BACKEND_AUTH_RETRY_SECONDS
        self.timeout_seconds = settings.BACKEND_REQUEST_TIMEOUT_SECONDS
        self._cookie: str | None = None
        self._lock = asyncio.Lock()
        self._refresh_task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None
        self._closed = False
        self._login_failed_at: float | None = None
        self._warned_no_creds = False

    @property
    def configured(self) -> bool:
        return bool(self.login and self.password)

    def _url(self, path: str) -> str:
        return f"{(self.base_url or '').rstrip('/')}/{path.lstrip('/')}"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._closed:
            raise BackendAuthError("клиент авторизации закрыт")
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.DummyCookieJar(),
                timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
            )
        return self._session

    async def _login(self) -> str:
        """POST v1/auth/login; вызывать под self._lock."""
        if not self.configured:
            raise BackendAuthError("BACKEND_LOGIN / BACKEND_PASSWORD не заданы")

        session = await self._get_session()
        async with session.post(
            self._url("v1/auth/login"),
            json={"username": self.login, "password": self.password},
            headers={"Accept": "application/json"},
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise BackendAuthError(f"login failed: HTTP {resp.status} {body[:300]}")
            morsel = resp.cookies.get(self.cookie_name)
            if morsel is None or not morsel.value:
                raise BackendAuthError(
                    f"login ответил 200, но куки {self.cookie_name} нет"
                )
            self._cookie = morsel.value
            logger.info("Кука %s получена", self.cookie_name)
            return self._cookie

    async def _login_tracked(self) -> str:
        """_login с запоминанием времени неудачи (для паузы между попытками)."""
        try:
            cookie = await self._login()
        except Exception:
            self._login_failed_at = time.monotonic()
            raise
        self._login_failed_at = None
        return cookie

    async def authenticate(self) -> str:
        """Принудительно логинится и сохраняет новую куку."""
        async with self._lock:
            return await self._login_tracked()

    async def _ensure_cookie(self) -> str:
        async with self._lock:
            if self._cookie:
                return self._cookie
            if self._login_failed_at is not None:
                left = self.retry_seconds - (time.monotonic() - self._login_failed_at)
                if left > 0:
                    raise BackendAuthError(
                        f"логин недавно не удался, повтор через {int(left) + 1} с"
                    )
            return await self._login_tracked()

    def _invalidate(self, cookie: str) -> None:
        if self._cookie == cookie:
            self._cookie = None

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> tuple[int, Any]:
        """Запрос с кукой; при 401/403 один раз перелогинивается и повторяет.

        Если логин/пароль не заданы — запрос уходит без куки (как раньше).
        """
        for attempt in range(2):
            headers = {"Accept": "application/json"}
            cookie = None
            if self.configured:
                cookie = await self._ensure_cookie()
                headers["Cookie"] = f"{self.cookie_name}={cookie}"
            elif not self._warned_no_creds:
                self._warned_no_creds = True
                logger.warning(
                    "Запросы к бэкенду идут без куки: нет BACKEND_LOGIN/PASSWORD"
                )
            session = await self._get_session()
            async with session.request(
                method,
                self._url(path),
                params=params,
                json=json,
                headers=headers,
            ) as resp:
                if resp.status in (401, 403) and attempt == 0 and cookie:
                    logger.warning(
                        "%s %s → HTTP %s, обновляем куку", method, path, resp.status
                    )
                    self._invalidate(cookie)
                    continue
                return resp.status, _parse_body(await resp.text())
        raise BackendAuthError("unreachable")

    async def update_order_status(self, order_id: str, status: str) -> tuple[int, Any]:
        """PUT v1/orders/{id}/status?status=... → (HTTP-статус, тело)."""
        code, body = await self.request(
            "PUT", f"v1/orders/{order_id}/status", params={"status": status}
        )
        if code == 200:
            logger.info("Статус заказа %s обновлён на %s", order_id, status)
        else:
            logger.error(
                "Статус заказа %s → %s: HTTP %s %s",
                order_id,
                status,
                code,
                str(body)[:300],
            )
        return code, body

    async def _refresh_loop(self) -> None:
        while True:
            try:
                await self.authenticate()
                delay = self.refresh_seconds
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Не удалось получить куку авторизации: %s", exc)
                delay = self.retry_seconds
            await asyncio.sleep(delay)

    def start(self) -> None:
        """Запускает фоновое обновление куки (если заданы логин и пароль)."""
        if not self.configured:
            logger.warning(
                "BACKEND_LOGIN / BACKEND_PASSWORD не заданы — "
                "запросы к бэкенду уходят без куки авторизации"
            )
            return
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def close(self) -> None:
        self._closed = True
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None


backend_auth = BackendAuthClient()
