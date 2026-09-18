"""Lightweight in-memory flood control. Not a distributed rate limiter —
this is a single-process bot, so a plain dict is enough to stop
button-mashing / spam-command abuse without adding a Redis dependency."""
import time

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

_last_seen: dict[int, float] = {}
MIN_INTERVAL_SECONDS = 0.4  # ~2.5 actions/sec ceiling per user


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            last = _last_seen.get(user.id, 0.0)
            if now - last < MIN_INTERVAL_SECONDS:
                return  # silently drop — no answer, no handler call
            _last_seen[user.id] = now
        return await handler(event, data)
