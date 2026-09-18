from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database.queries import get_setting
from handlers.force_join import missing_channels
from utils.keyboards import force_join_kb


class AccessMiddleware(BaseMiddleware):
    """Applies maintenance mode and force-join rules to all user updates."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if not user or user.id in ADMIN_IDS:
            return await handler(event, data)

        if isinstance(event, Message) and (event.text or "").startswith("/start"):
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == "forcejoin:check":
            return await handler(event, data)

        if await get_setting("maintenance_mode", "0") == "1":
            if isinstance(event, CallbackQuery):
                await event.answer("বট maintenance mode-এ আছে।", show_alert=True)
            else:
                await event.answer("🛠️ বট আপডেট করা হচ্ছে। কিছুক্ষণ পরে চেষ্টা করুন।")
            return None

        bot: Bot = data["bot"]
        channels = await missing_channels(bot, user.id)
        if channels:
            if isinstance(event, CallbackQuery):
                await event.answer("আগে Required Channel-এ Join করুন।", show_alert=True)
                await event.message.answer(
                    "📢 বট ব্যবহার করতে নিচের Channel-গুলোতে Join করুন।",
                    reply_markup=force_join_kb(channels),
                )
            else:
                await event.answer(
                    "📢 বট ব্যবহার করতে আগে Required Channel-এ Join করুন।",
                    reply_markup=force_join_kb(channels),
                )
            return None

        return await handler(event, data)