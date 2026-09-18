from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.queries import (
    all_user_ids,
    close_support_ticket,
    delete_product,
    edit_product,
    get_product,
    get_setting,
    get_support_ticket,
    list_force_join_channels,
    add_force_join_channel,
    log_admin_action,
    open_support_tickets,
    remove_force_join_channel,
    set_product_featured,
    set_setting,
    toggle_force_join_required,
)
from utils.filters import IsAdmin
from utils.keyboards import (
    admin_product_tools_kb,
    admin_ticket_list_kb,
    force_join_admin_kb,
    force_join_required_kb,
    force_join_type_kb,
)
from utils.states import AdminBroadcast, AdminForceJoin, AdminProductEdit, AdminSupportReply

router = Router(name="admin_advanced")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data.startswith("admin:product:view:"))
async def product_tools(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[3])
    product = await get_product(product_id)
    if not product:
        await callback.answer("Product পাওয়া যায়নি।", show_alert=True)
        return
    status = "Active" if product["is_active"] else "Archived/Disabled"
    text = (
        f"🧰 <b>Product Tools</b>\n\n"
        f"ID: <code>#{product['product_id']}</code>\n"
        f"Name: <b>{escape(product['name'])}</b>\n"
        f"Description: {escape(product['description']) or '—'}\n"
        f"Coin price: <b>{product['price_coin']}</b>\n"
        f"Stars price: <b>{product['price_stars']}</b>\n"
        f"Sales: {product['sales_count']}\n"
        f"Status: {status}\n"
        f"Featured: {'Yes' if product.get('is_featured') else 'No'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_product_tools_kb(product_id, bool(product.get("is_featured"))),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:product:edit:"))
async def start_product_edit(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.split(":")[3])
    if not await get_product(product_id):
        await callback.answer("Product পাওয়া যায়নি।", show_alert=True)
        return
    await state.set_state(AdminProductEdit.waiting_field)
    await state.update_data(product_id=product_id)
    await callback.message.answer(
        "কোন তথ্য পরিবর্তন করবেন?\n"
        "নিচের format-এ লিখুন: <code>name</code>, <code>description</code>, "
        "<code>price_coin</code>, অথবা <code>price_stars</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminProductEdit.waiting_field)
async def product_edit_field(message: Message, state: FSMContext) -> None:
    field = (message.text or "").strip().lower()
    if field not in {"name", "description", "price_coin", "price_stars"}:
        await message.answer("❌ সঠিক field লিখুন: name, description, price_coin, price_stars")
        return
    await state.update_data(field=field)
    await state.set_state(AdminProductEdit.waiting_value)
    await message.answer(f"নতুন {field} লিখুন:")


@router.message(AdminProductEdit.waiting_value)
async def product_edit_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = data["field"]
    value = (message.text or "").strip()
    if field in {"price_coin", "price_stars"}:
        if not value.isdigit():
            await message.answer("❌ Price হিসেবে শুধু 0 বা positive সংখ্যা দিন।")
            return
        value = int(value)
    if not value:
        await message.answer("❌ Value খালি রাখা যাবে না।")
        return
    updated = await edit_product(data["product_id"], field, value)
    await state.clear()
    await message.answer("✅ Product আপডেট হয়েছে।" if updated else "❌ Product পাওয়া যায়নি।")


@router.callback_query(F.data.startswith("admin:product:feature:"))
async def toggle_featured(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[3])
    product = await get_product(product_id)
    if not product:
        await callback.answer("Product পাওয়া যায়নি।", show_alert=True)
        return
    await set_product_featured(product_id, not bool(product.get("is_featured")))
    await callback.answer("Featured status আপডেট হয়েছে।")
    await product_tools(callback)


@router.callback_query(F.data.startswith("admin:product:delete:"))
async def archive_product(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[3])
    archived = await delete_product(product_id)
    await callback.answer("Product archive করা হয়েছে।" if archived else "Product পাওয়া যায়নি।", show_alert=True)
    await callback.message.edit_text("🗑 Product archive হয়েছে।", parse_mode="HTML")


@router.callback_query(F.data == "admin:logs")
async def view_audit_logs(callback: CallbackQuery) -> None:
    from database.queries import recent_admin_logs
    from utils.keyboards import back_to_admin_kb

    logs = await recent_admin_logs(20)
    if not logs:
        text = "🧾 <b>Audit Log</b>\n\nকোনো এন্ট্রি নেই এখনো।"
    else:
        lines = ["🧾 <b>Audit Log</b> (সাম্প্রতিক ২০টি)\n"]
        for entry in logs:
            lines.append(f"• {entry['created_at']} — admin {entry['admin_id']}: {entry['action']} ({entry['details'] or '-'})")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()
async def force_join_settings(callback: CallbackQuery) -> None:
    channels = await list_force_join_channels(active_only=False)
    active_channels = [c for c in channels if c["is_active"]]
    required_count = len([c for c in active_channels if c["is_required"]])
    optional_count = len(active_channels) - required_count
    gate_enabled = await get_setting("force_join_disabled", "0") != "1"
    text = (
        "📌 <b>Force Join Settings</b>\n\n"
        "একাধিক Channel/Group একসাথে mandatory (Required) বা শুধু encourage করার জন্য "
        "Optional রাখা যায়। Required-এর সবগুলোতে Join না করলে user বট ব্যবহার করতে পারবে না।\n\n"
        f"Required: <b>{required_count}</b> · Optional: <b>{optional_count}</b>\n"
        f"Gate status: {'🟢 ON' if gate_enabled else '🔴 Temporarily OFF'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=force_join_admin_kb(active_channels, gate_enabled=gate_enabled),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:forcejoin:toggle_gate")
async def force_join_toggle_gate(callback: CallbackQuery) -> None:
    current = await get_setting("force_join_disabled", "0")
    await set_setting("force_join_disabled", "0" if current == "1" else "1")
    await callback.answer("Force Join gate আপডেট হয়েছে।", show_alert=True)
    await force_join_settings(callback)


@router.callback_query(F.data.startswith("admin:forcejoin:toggle_req:"))
async def force_join_toggle_required(callback: CallbackQuery) -> None:
    channel_id = int(callback.data.split(":")[3])
    await toggle_force_join_required(channel_id)
    await callback.answer("Required/Optional পরিবর্তন হয়েছে।")
    await force_join_settings(callback)


@router.callback_query(F.data == "admin:forcejoin:add")
async def force_join_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminForceJoin.waiting_channel_id)
    await callback.message.answer(
        "Channel/Group-এর numeric ID লিখুন (যেমন: -1001234567890):"
    )
    await callback.answer()


@router.message(AdminForceJoin.waiting_channel_id)
async def force_join_channel_id(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not value.lstrip("-").isdigit():
        await message.answer("❌ সঠিক numeric ID দিন।")
        return
    await state.update_data(channel_id=int(value))
    await state.set_state(AdminForceJoin.waiting_title)
    await message.answer("Display name লিখুন:")


@router.message(AdminForceJoin.waiting_title)
async def force_join_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("❌ নাম খালি রাখা যাবে না।")
        return
    await state.update_data(title=title)
    await state.set_state(AdminForceJoin.waiting_invite_link)
    await message.answer("Invite link লিখুন (https://t.me/... ):")


@router.message(AdminForceJoin.waiting_invite_link)
async def force_join_invite(message: Message, state: FSMContext) -> None:
    link = (message.text or "").strip()
    if not (link.startswith("https://t.me/") or link.startswith("http://t.me/")):
        await message.answer("❌ বৈধ Telegram invite link দিন, যেমন https://t.me/yourchannel")
        return
    await state.update_data(invite_link=link)
    await state.set_state(AdminForceJoin.waiting_type)
    await message.answer("এটি কী ধরনের চ্যাট?", reply_markup=force_join_type_kb())


@router.callback_query(AdminForceJoin.waiting_type, F.data.startswith("admin:forcejoin:type:"))
async def force_join_pick_type(callback: CallbackQuery, state: FSMContext) -> None:
    chat_type = callback.data.split(":")[3]
    await state.update_data(chat_type=chat_type)
    await state.set_state(AdminForceJoin.waiting_required)
    await callback.message.edit_text(
        "এটি কি Mandatory (সবার জন্য বাধ্যতামূলক) নাকি শুধু Optional?",
        reply_markup=force_join_required_kb(),
    )
    await callback.answer()


@router.callback_query(AdminForceJoin.waiting_required, F.data.startswith("admin:forcejoin:required:"))
async def force_join_pick_required(callback: CallbackQuery, state: FSMContext) -> None:
    is_required = callback.data.split(":")[3] == "1"
    data = await state.get_data()
    await add_force_join_channel(
        data["channel_id"], data["title"], data["invite_link"],
        chat_type=data["chat_type"], is_required=is_required,
    )
    await log_admin_action(
        callback.from_user.id, "forcejoin_add",
        f"channel_id={data['channel_id']}, type={data['chat_type']}, required={is_required}",
    )
    await state.clear()
    await callback.message.edit_text(
        "✅ Force Join এন্ট্রি যোগ হয়েছে। Bot-কে ওই Channel/Group-এ admin রাখুন "
        "(Add Members permission সহ, না হলে membership check ব্যর্থ হবে)।"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:forcejoin:remove:"))
async def force_join_remove(callback: CallbackQuery) -> None:
    channel_id = int(callback.data.split(":")[3])
    await remove_force_join_channel(channel_id)
    await log_admin_action(callback.from_user.id, "forcejoin_remove", f"channel_id={channel_id}")
    await callback.answer("Entry সরানো হয়েছে।", show_alert=True)
    await force_join_settings(callback)


@router.callback_query(F.data == "admin:maintenance")
async def toggle_maintenance(callback: CallbackQuery) -> None:
    current = await get_setting("maintenance_mode", "0")
    new_value = "0" if current == "1" else "1"
    await set_setting("maintenance_mode", new_value)
    label = "ON — users এখন blocked" if new_value == "1" else "OFF — bot open"
    await callback.answer(f"Maintenance {label}", show_alert=True)


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminBroadcast.waiting_message)
    await callback.message.answer(
        "📢 Broadcast text লিখুন। এটি সব non-banned user-কে plain text হিসেবে যাবে।"
    )
    await callback.answer()


@router.message(AdminBroadcast.waiting_message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("❌ Broadcast text খুব ছোট।")
        return
    await state.clear()
    sent, failed = 0, 0
    for user_id in await all_user_ids():
        try:
            await bot.send_message(user_id, text, parse_mode=None)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Broadcast শেষ। Sent: {sent}, Failed: {failed}")


@router.callback_query(F.data == "admin:tickets")
async def list_tickets(callback: CallbackQuery) -> None:
    tickets = await open_support_tickets()
    if not tickets:
        await callback.answer("কোনো Open ticket নেই।", show_alert=True)
        return
    await callback.message.edit_text(
        "🆘 <b>Open Support Tickets</b>",
        reply_markup=admin_ticket_list_kb(tickets),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:ticket:view:"))
async def view_ticket(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.split(":")[3])
    ticket = await get_support_ticket(ticket_id)
    if not ticket:
        await callback.answer("Ticket পাওয়া যায়নি।", show_alert=True)
        return
    username = f"@{escape(ticket['username'])}" if ticket.get("username") else "username নেই"
    await callback.message.edit_text(
        f"🆘 <b>Ticket #{ticket_id}</b>\n\n"
        f"User: {username}\nUser ID: <code>{ticket['user_id']}</code>\n\n"
        f"{escape(ticket['message'])}",
        reply_markup=support_admin_kb(ticket_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:ticket:reply:"))
async def ticket_reply_start(callback: CallbackQuery, state: FSMContext) -> None:
    ticket_id = int(callback.data.split(":")[3])
    await state.set_state(AdminSupportReply.waiting_reply)
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer("✍️ User-কে যে reply পাঠাতে চান তা লিখুন:")
    await callback.answer()


@router.message(AdminSupportReply.waiting_reply)
async def ticket_reply_send(message: Message, state: FSMContext, bot: Bot) -> None:
    reply = (message.text or "").strip()
    if len(reply) < 2:
        await message.answer("❌ Reply খুব ছোট।")
        return
    data = await state.get_data()
    result = await close_support_ticket(data["ticket_id"], message.from_user.id, reply)
    await state.clear()
    if not result:
        await message.answer("এই ticket ইতিমধ্যে closed হয়েছে।")
        return
    try:
        await bot.send_message(
            result["user_id"],
            f"🆘 <b>Support Reply — Ticket #{result['ticket_id']}</b>\n\n{escape(reply)}",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await message.answer("✅ Reply পাঠানো ও ticket close করা হয়েছে।")