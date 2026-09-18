"""Admin overview for the /linkgen sharing system: aggregate stats, a
recent-links browser, and force-delete for abusive/leaked links."""
from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.queries import delete_shared_link, get_shared_link, link_admin_stats, log_admin_action, recent_shared_links
from utils.filters import IsAdmin
from utils.keyboards import admin_link_detail_kb, admin_link_list_kb

router = Router(name="admin_links")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin:links")
async def link_overview(callback: CallbackQuery) -> None:
    stats = await link_admin_stats()
    links = await recent_shared_links(20)
    text = (
        "🔗 <b>Link Management</b>\n\n"
        f"Total links: <b>{stats['total']}</b>\n"
        f"Active: <b>{stats['active']}</b>\n"
        f"Total views: <b>{stats['total_views']}</b>\n\n"
        "সাম্প্রতিক ২০টি link (নিচে ট্যাপ করে বিস্তারিত দেখুন):"
    )
    await callback.message.edit_text(text, reply_markup=admin_link_list_kb(links), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:link:view:"))
async def link_detail(callback: CallbackQuery) -> None:
    token = callback.data.split(":", 3)[3]
    link = await get_shared_link(token)
    if not link:
        await callback.answer("Link পাওয়া যায়নি।", show_alert=True)
        return
    owner = f"@{escape(link['username'])}" if link.get("username") else str(link["owner_id"])
    text = (
        f"🔗 <b>{escape(token)}</b>\n\n"
        f"Owner: {owner} (<code>{link['owner_id']}</code>)\n"
        f"Type: {escape(link['content_type'])}\n"
        f"Status: {'✅ Active' if link['is_active'] else '🚫 Disabled'}\n"
        f"👁 Views: {link['views']}\n"
        f"📅 Created: {escape(link.get('created_at') or '—')}\n"
        f"🕒 Last accessed: {escape(link.get('last_accessed_at') or 'কখনো না')}\n"
        f"⏳ Expires: {escape(link.get('expires_at') or 'Never')}\n"
        f"🔒 Password protected: {'Yes' if link.get('password_hash') else 'No'}"
    )
    await callback.message.edit_text(text, reply_markup=admin_link_detail_kb(token), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:link:delete:"))
async def link_force_delete(callback: CallbackQuery) -> None:
    token = callback.data.split(":", 3)[3]
    deleted = await delete_shared_link(token)
    if deleted:
        await log_admin_action(callback.from_user.id, "link_force_delete", f"token={token}")
    await callback.answer("✅ Force deleted." if deleted else "❌ পাওয়া যায়নি।", show_alert=True)
    await link_overview(callback)
