"""Referral verification/activation engine.

Centralises everything about a referral's lifecycle — activation,
leave-detection (revalidation), anti-abuse signal, and milestone rewards —
in one module instead of scattering the logic across handlers. Handlers
should call into this module rather than touching referral status columns
directly.
"""
import logging

from aiogram import Bot

from config import (
    REFERRAL_LEVEL2_REWARD_COIN,
    REFERRAL_REMINDER_HOURS,
    REFERRAL_REMINDER_MAX_COUNT,
    REFERRAL_REWARD_COIN,
)
from database.models import get_conn
from database.queries import (
    active_referral_count,
    adjust_coins,
    all_active_referred_ids,
    bump_referral_reminder,
    claim_milestone,
    claimed_milestone_ids,
    get_referral_status,
    get_setting,
    get_user,
    list_milestones,
    mark_referral_rewarded,
    pending_referrals_for_reminder,
    recent_referrals_count,
    set_referral_status,
)

log = logging.getLogger("referral_engine")

# A referrer who suddenly brings in an unusual number of new accounts in a
# short window gets flagged for the admin stats view — this does not block
# the referral itself (a real viral share happens too), it's a signal only.
ANTI_ABUSE_WINDOW_MINUTES = 60
ANTI_ABUSE_MAX_NEW_REFERRALS = 10


async def is_suspicious_referrer(referrer_id: int) -> bool:
    count = await recent_referrals_count(referrer_id, ANTI_ABUSE_WINDOW_MINUTES)
    return count > ANTI_ABUSE_MAX_NEW_REFERRALS


async def _referrer_of(referred_id: int) -> int | None:
    async with get_conn() as db:
        cur = await db.execute(
            "SELECT referrer_id FROM referrals WHERE referred_id=?", (referred_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def check_and_award_milestones(bot: Bot, referrer_id: int) -> list[dict]:
    """Called after a referral turns active. Pays out any milestone reward
    thresholds the referrer just crossed for the first time."""
    milestones = await list_milestones(active_only=True)
    if not milestones:
        return []
    current = await active_referral_count(referrer_id)
    already = await claimed_milestone_ids(referrer_id)
    newly_awarded = []
    for m in milestones:
        if m["milestone_id"] in already or current < m["threshold"]:
            continue
        if not await claim_milestone(referrer_id, m["milestone_id"]):
            continue  # already claimed by a concurrent check
        await adjust_coins(referrer_id, m["reward_coin"], f"Referral milestone x{m['threshold']}")
        newly_awarded.append(m)

    for m in newly_awarded:
        try:
            await bot.send_message(
                referrer_id,
                "🏆 <b>Milestone Unlocked!</b>\n"
                f"আপনার {m['threshold']} জন Active Referral হয়েছে।\n"
                f"🪙 +{m['reward_coin']} কয়েন বোনাস যোগ হয়েছে।",
            )
        except Exception:  # noqa: BLE001 — user may have blocked the bot
            pass
    return newly_awarded


async def activate_referral(bot: Bot, referred_id: int) -> None:
    """Mark a referral 'active' (all required force-join checks passed)
    and trigger milestone evaluation for the referrer. Notifies the
    referrer, but only on the actual pending/left → active transition —
    this gets called on every /start, so a status check keeps that a
    one-time ping instead of spam."""
    referrer_id = await _referrer_of(referred_id)
    previous_status = await get_referral_status(referred_id)
    await set_referral_status(referred_id, "active")

    if referrer_id and previous_status != "active":
        try:
            await bot.send_message(
                referrer_id,
                "✅ আপনার একজন রেফারেল ভেরিফাই হয়েছে — সে প্রয়োজনীয় সব Channel/Group-এ Join করেছে!\n"
                "সে প্রথম কেনাকাটা করলেই আপনি রিওয়ার্ড পাবেন।",
            )
        except Exception:  # noqa: BLE001 — user may have blocked the bot
            pass

    if referrer_id:
        await check_and_award_milestones(bot, referrer_id)


async def reward_referrer_chain(bot: Bot, buyer_id: int) -> None:
    """Called on a referred user's FIRST purchase. Pays the direct (level-1)
    referrer the standard reward, then — if the admin has multi-level
    referrals turned on — a smaller level-2 bonus to that referrer's OWN
    referrer. Both only ever fire once per buyer, piggybacking on
    mark_referral_rewarded's one-shot reward_given flag."""
    referrer_id = await mark_referral_rewarded(buyer_id)
    if not referrer_id:
        return

    await adjust_coins(referrer_id, REFERRAL_REWARD_COIN, "Referral reward")
    try:
        await bot.send_message(
            referrer_id,
            "🎉 আপনার রেফার করা একজন ইউজার প্রথম কেনাকাটা করেছেন!\n"
            f"🪙 +{REFERRAL_REWARD_COIN} কয়েন যোগ হয়েছে।",
        )
    except Exception:  # noqa: BLE001
        pass

    if REFERRAL_LEVEL2_REWARD_COIN <= 0 or await get_setting("referral_level2_enabled", "1") != "1":
        return
    referrer = await get_user(referrer_id)
    level2_id = referrer.get("referred_by") if referrer else None
    if not level2_id:
        return
    await adjust_coins(level2_id, REFERRAL_LEVEL2_REWARD_COIN, "Level-2 referral reward")
    try:
        await bot.send_message(
            level2_id,
            "🎉 আপনার নেটওয়ার্কে একজন ইউজার (আপনার রেফারের রেফার) প্রথম কেনাকাটা করেছেন!\n"
            f"🪙 +{REFERRAL_LEVEL2_REWARD_COIN} বোনাস কয়েন যোগ হয়েছে।",
        )
    except Exception:  # noqa: BLE001
        pass


async def revoke_referral(bot: Bot, referred_id: int, reason: str) -> None:
    """The referred user no longer satisfies required membership.
    Downgrades the referral to 'left' and — if the admin enabled
    referral_revoke_on_leave — claws back the one-time referral reward."""
    await set_referral_status(referred_id, "left", reason)

    if await get_setting("referral_revoke_on_leave", "0") != "1":
        return

    async with get_conn() as db:
        cur = await db.execute(
            "SELECT referrer_id, reward_given FROM referrals WHERE referred_id=?",
            (referred_id,),
        )
        row = await cur.fetchone()
    if not row or not row[1]:
        return
    referrer_id = row[0]
    try:
        await adjust_coins(referrer_id, -REFERRAL_REWARD_COIN, "Referral reward revoked (referred user left)")
    except ValueError:
        return  # balance already below the reward amount; nothing to claw back
    try:
        await bot.send_message(
            referrer_id,
            "⚠️ আপনার একজন Referral প্রয়োজনীয় Channel/Group থেকে Leave করায় "
            f"রিওয়ার্ড 🪙 {REFERRAL_REWARD_COIN} ফেরত নেওয়া হয়েছে।",
        )
    except Exception:  # noqa: BLE001
        pass


async def revalidate_all_active(bot: Bot) -> tuple[int, int]:
    """Periodic leave-detection sweep: re-checks every 'active' referral's
    required-channel membership and downgrades anyone who left. Returns
    (checked_count, revoked_count) for logging."""
    from handlers.force_join import missing_channels  # local import avoids a circular import at module load

    referred_ids = await all_active_referred_ids()
    revoked = 0
    for referred_id in referred_ids:
        try:
            missing = await missing_channels(bot, referred_id)
        except Exception as exc:  # noqa: BLE001 — one bad lookup shouldn't stop the sweep
            log.warning("Revalidation check failed for %s: %s", referred_id, exc)
            continue
        if missing:
            await revoke_referral(bot, referred_id, "required membership missing (periodic recheck)")
            revoked += 1
    return len(referred_ids), revoked


async def send_pending_reminders(bot: Bot) -> tuple[int, int]:
    """Nudges referred users who signed up but never finished joining the
    required channels/groups. Re-checks live membership first — someone may
    have joined without reopening the bot — and activates them silently
    instead of nagging; only genuine stragglers get a reminder, capped at
    REFERRAL_REMINDER_MAX_COUNT per person. Returns (reminded, auto_activated)."""
    if await get_setting("referral_reminder_enabled", "1") != "1":
        return 0, 0

    from handlers.force_join import missing_channels  # local import avoids a circular import at module load
    from utils.keyboards import force_join_kb

    rows = await pending_referrals_for_reminder(REFERRAL_REMINDER_HOURS, REFERRAL_REMINDER_MAX_COUNT)
    reminded = 0
    auto_activated = 0
    for row in rows:
        referred_id = row["referred_id"]
        try:
            channels = await missing_channels(bot, referred_id)
        except Exception as exc:  # noqa: BLE001 — one bad lookup shouldn't stop the sweep
            log.warning("Reminder check failed for %s: %s", referred_id, exc)
            continue

        if not channels:
            # They already joined since last check but never reopened the
            # bot to trigger the normal /start verification — activate now.
            await activate_referral(bot, referred_id)
            auto_activated += 1
            continue

        try:
            await bot.send_message(
                referred_id,
                "👋 আপনার রেফারেল এখনো সম্পূর্ণ হয়নি!\n"
                "নিচের Channel/Group-এ Join করুন — তাহলেই আপনার রেফারার তার রিওয়ার্ড পাবেন।",
                reply_markup=force_join_kb(channels),
            )
            reminded += 1
        except Exception:  # noqa: BLE001 — user may have blocked the bot
            pass
        await bump_referral_reminder(referred_id)
    return reminded, auto_activated
