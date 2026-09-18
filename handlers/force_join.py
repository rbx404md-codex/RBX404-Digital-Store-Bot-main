"""Force Join gate.

Supports multiple channels AND groups at once, each independently marked
required (mandatory) or optional (shown but not blocking). Membership is
cached briefly to avoid hammering the Bot API, and admins can flip a
global kill-switch to pause the whole gate without deleting the config.
"""
import time

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from database.queries import get_setting, list_force_join_channels
from services import referral_engine
from utils.keyboards import force_join_kb, main_menu

router = Router(name="force_join")
_membership_cache: dict[tuple[int, int], tuple[float, bool]] = {}
MEMBERSHIP_CACHE_SECONDS = 120


async def force_join_enabled() -> bool:
    return await get_setting("force_join_disabled", "0") != "1"


async def _is_member(bot: Bot, channel_id: int, user_id: int) -> bool:
    cache_key = (channel_id, user_id)
    cached = _membership_cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < MEMBERSHIP_CACHE_SECONDS:
        return cached[1]
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        joined = member.status not in {"left", "kicked"}
    except Exception:
        joined = False
    _membership_cache[cache_key] = (time.monotonic(), joined)
    return joined


async def missing_channels(bot: Bot, user_id: int) -> list[dict]:
    """Required (mandatory) channels/groups the user has NOT joined yet.
    Returns an empty list if the force-join gate is globally disabled."""
    if not await force_join_enabled():
        return []
    missing = []
    for channel in await list_force_join_channels(required_only=True):
        if not await _is_member(bot, channel["channel_id"], user_id):
            missing.append(channel)
    return missing


async def missing_optional_channels(bot: Bot, user_id: int) -> list[dict]:
    """Optional channels/groups not yet joined — shown for encouragement,
    never block bot usage."""
    if not await force_join_enabled():
        return []
    all_channels = await list_force_join_channels(required_only=False)
    optional = [c for c in all_channels if not c["is_required"]]
    missing = []
    for channel in optional:
        if not await _is_member(bot, channel["channel_id"], user_id):
            missing.append(channel)
    return missing


async def sync_referral_membership(bot: Bot, user_id: int, channels: list[dict] | None = None) -> bool:
    """Re-check required membership and activate/leave the referral record
    accordingly. Returns True if fully verified."""
    channels = await missing_channels(bot, user_id) if channels is None else channels
    if channels:
        await referral_engine.revoke_referral(bot, user_id, "required membership missing")
        return False
    await referral_engine.activate_referral(bot, user_id)
    return True


async def send_join_prompt(callback: CallbackQuery, channels: list[dict]) -> None:
    await callback.message.answer(
        "📢 বট ব্যবহার করতে আগে নিচের Channel/Group-এ Join করুন।",
        reply_markup=force_join_kb(channels),
    )


@router.callback_query(F.data == "forcejoin:check")
async def check_force_join(callback: CallbackQuery, bot: Bot) -> None:
    # Drop this user's cache entries so a fresh join reflects immediately.
    for key in [k for k in _membership_cache if k[1] == callback.from_user.id]:
        _membership_cache.pop(key, None)

    channels = await missing_channels(bot, callback.from_user.id)
    if channels:
        await callback.answer("সব প্রয়োজনীয় Channel/Group-এ Join করা হয়নি।", show_alert=True)
        await send_join_prompt(callback, channels)
        return

    await sync_referral_membership(bot, callback.from_user.id, channels=[])
    await callback.message.answer(
        "✅ Join verify হয়েছে। এখন বট ব্যবহার করতে পারবেন।",
        reply_markup=main_menu(),
    )
    await callback.answer()
