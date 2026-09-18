"""Settings menu — currently just language selection, structured so more
preferences (notifications, theme, etc.) can be added the same way."""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.queries import get_or_create_user, set_user_language
from locales.strings import SUPPORTED_LANGUAGES
from utils.i18n import t
from utils.keyboards import language_picker_kb, settings_menu_kb

router = Router(name="settings")


@router.callback_query(F.data == "menu:settings")
async def open_settings(callback: CallbackQuery) -> None:
    user = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    lang_label = SUPPORTED_LANGUAGES.get(user.get("language", "bn"), "🇧🇩 বাংলা")
    await callback.message.edit_text(
        f"⚙️ <b>Settings</b>\n\nCurrent language: {lang_label}",
        reply_markup=settings_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings:language")
async def pick_language(callback: CallbackQuery) -> None:
    user = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    await callback.message.edit_text(
        t("language_prompt", user.get("language", "bn")),
        reply_markup=language_picker_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:lang:"))
async def set_language(callback: CallbackQuery) -> None:
    lang = callback.data.split(":")[2]
    if lang not in SUPPORTED_LANGUAGES:
        await callback.answer("Unsupported language.", show_alert=True)
        return
    await set_user_language(callback.from_user.id, lang)
    await callback.answer(t("language_saved", lang, lang=SUPPORTED_LANGUAGES[lang]), show_alert=True)
    await open_settings(callback)
