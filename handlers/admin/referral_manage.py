"""Admin controls for the referral engine: top-referrer stats (with a
suspicious-activity flag), milestone rewards, and the revoke-on-leave
toggle. Kept separate from advanced.py so the referral engine's admin
surface can grow without bloating an already-large file."""
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import REFERRAL_LEVEL2_REWARD_COIN, REFERRAL_REMINDER_HOURS
from database.queries import (
    create_milestone,
    delete_milestone,
    get_setting,
    list_milestones,
    set_setting,
    top_referrers,
)
from services.referral_engine import is_suspicious_referrer
from utils.filters import IsAdmin
from utils.keyboards import milestone_list_kb, referral_admin_kb
from utils.states import AdminMilestone

router = Router(name="admin_referral")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin:referral_settings")
async def referral_settings(callback: CallbackQuery) -> None:
    revoke_on_leave = await get_setting("referral_revoke_on_leave", "0") == "1"
    level2_on = await get_setting("referral_level2_enabled", "1") == "1"
    reminder_on = await get_setting("referral_reminder_enabled", "1") == "1"
    text = (
        "🎁 <b>Referral Engine Settings</b>\n\n"
        "Valid referral = referred user + প্রয়োজনীয় membership verified + সেই membership বজায় থাকা।\n"
        f"Revoke reward if referred user leaves later: <b>{'ON' if revoke_on_leave else 'OFF'}</b>\n"
        f"Level-2 bonus (রেফারের রেফার): <b>{'ON' if level2_on else 'OFF'}</b> "
        f"(🪙{REFERRAL_LEVEL2_REWARD_COIN})\n"
        f"Join reminder (যারা এখনো join করেনি): <b>{'ON' if reminder_on else 'OFF'}</b> "
        f"({REFERRAL_REMINDER_HOURS}h পরপর)"
    )
    await callback.message.edit_text(text, reply_markup=referral_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:referral:toggle_revoke")
async def toggle_revoke(callback: CallbackQuery) -> None:
    current = await get_setting("referral_revoke_on_leave", "0")
    await set_setting("referral_revoke_on_leave", "0" if current == "1" else "1")
    await callback.answer("Revoke-on-leave সেটিং আপডেট হয়েছে।", show_alert=True)
    await referral_settings(callback)


@router.callback_query(F.data == "admin:referral:toggle_level2")
async def toggle_level2(callback: CallbackQuery) -> None:
    current = await get_setting("referral_level2_enabled", "1")
    await set_setting("referral_level2_enabled", "0" if current == "1" else "1")
    await callback.answer("Level-2 bonus সেটিং আপডেট হয়েছে।", show_alert=True)
    await referral_settings(callback)


@router.callback_query(F.data == "admin:referral:toggle_reminder")
async def toggle_reminder(callback: CallbackQuery) -> None:
    current = await get_setting("referral_reminder_enabled", "1")
    await set_setting("referral_reminder_enabled", "0" if current == "1" else "1")
    await callback.answer("Join reminder সেটিং আপডেট হয়েছে।", show_alert=True)
    await referral_settings(callback)


@router.callback_query(F.data == "admin:referral:top")
async def top_referrers_view(callback: CallbackQuery) -> None:
    rows = await top_referrers(15)
    if not rows:
        await callback.answer("এখনো কোনো Active referral নেই।", show_alert=True)
        return
    lines = ["🏆 <b>Top Referrers</b>\n"]
    for i, row in enumerate(rows, 1):
        username = f"@{escape(row['username'])}" if row.get("username") else str(row["referrer_id"])
        flag = ""
        if await is_suspicious_referrer(row["referrer_id"]):
            flag = " ⚠️"
        lines.append(f"{i}. {username} — {row['active_count']} active{flag}")
    lines.append("\n⚠️ = অস্বাভাবিক গতিতে নতুন referral আসছে, ম্যানুয়ালি চেক করুন।")
    await callback.message.edit_text("\n".join(lines), reply_markup=referral_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:referral:milestones")
async def milestones_view(callback: CallbackQuery) -> None:
    milestones = await list_milestones()
    text = (
        "🎯 <b>Referral Milestones</b>\n\n"
        "নির্দিষ্ট সংখ্যক Active referral হলে referrer-কে বাড়তি বোনাস কয়েন দিন।"
        if milestones else
        "🎯 <b>Referral Milestones</b>\n\nএখনো কোনো milestone সেট করা নেই।"
    )
    await callback.message.edit_text(text, reply_markup=milestone_list_kb(milestones), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:referral:milestone_add")
async def milestone_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminMilestone.waiting_threshold)
    await callback.message.answer("কতজন Active Referral হলে বোনাস দেবেন? সংখ্যা লিখুন:")
    await callback.answer()


@router.message(AdminMilestone.waiting_threshold)
async def milestone_threshold(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not value.isdigit() or int(value) <= 0:
        await message.answer("❌ ১ বা তার বেশি একটি সংখ্যা দিন।")
        return
    await state.update_data(threshold=int(value))
    await state.set_state(AdminMilestone.waiting_reward)
    await message.answer("এই milestone-এ কত কয়েন বোনাস দেবেন?")


@router.message(AdminMilestone.waiting_reward)
async def milestone_reward(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not value.isdigit() or int(value) <= 0:
        await message.answer("❌ ১ বা তার বেশি একটি সংখ্যা দিন।")
        return
    data = await state.get_data()
    await create_milestone(data["threshold"], int(value))
    await state.clear()
    await message.answer(f"✅ Milestone যোগ হয়েছে: {data['threshold']} referrals → 🪙{value}")


@router.callback_query(F.data.startswith("admin:referral:milestone_del:"))
async def milestone_delete(callback: CallbackQuery) -> None:
    milestone_id = int(callback.data.split(":")[3])
    await delete_milestone(milestone_id)
    await callback.answer("Milestone মুছে ফেলা হয়েছে।", show_alert=True)
    await milestones_view(callback)
