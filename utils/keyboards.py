from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ Store", callback_data="store:categories")
    kb.button(text="🪙 Wallet", callback_data="wallet:open")
    kb.button(text="🎁 Referral", callback_data="referral:open")
    kb.button(text="📚 My Purchases", callback_data="orders:mine")
    kb.button(text="🔎 Search", callback_data="search:start")
    kb.button(text="🔗 Link Generator", callback_data="linkgen:start")
    kb.button(text="❤️ Wishlist", callback_data="wishlist:list")
    kb.button(text="🎁 Daily Bonus", callback_data="daily:checkin")
    kb.button(text="🆘 Support", callback_data="support:open")
    kb.button(text="ℹ️ Help", callback_data="help:open")
    kb.button(text="⚙️ Settings", callback_data="menu:settings")
    kb.adjust(2, 2, 2, 2, 2, 1)
    return kb.as_markup()


def settings_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Language", callback_data="settings:language")
    kb.button(text="⬅️ Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def categories_kb(categories: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=f"{c['icon']} {c['name']}", callback_data=f"store:cat:{c['category_id']}")
    kb.button(text="⬅️ Back", callback_data="menu:main")
    kb.adjust(2)
    return kb.as_markup()


def products_kb(products: list[dict], category_id: int, page: int = 0,
                has_next: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in products:
        featured = "⭐ " if p.get("is_featured") else ""
        kb.button(text=f"{featured}{p['name']} — 🪙{p['price_coin']} / ⭐{p['price_stars']}",
                   callback_data=f"store:product:{p['product_id']}")
    if page > 0:
        kb.button(text="⬅️ Previous", callback_data=f"store:cat:{category_id}:{page - 1}")
    if has_next:
        kb.button(text="Next ➡️", callback_data=f"store:cat:{category_id}:{page + 1}")
    kb.button(text="⬅️ Back", callback_data="store:categories")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def product_detail_kb(product_id: int, has_preview: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if has_preview:
        kb.button(text="🔍 Preview দেখুন", callback_data=f"store:preview:{product_id}")
    kb.button(text="🪙 Buy with Coin", callback_data=f"buy:coin:{product_id}")
    kb.button(text="⭐ Buy with Stars", callback_data=f"buy:stars:{product_id}")
    kb.button(text="🎟️ I have a coupon", callback_data=f"buy:coupon:{product_id}")
    kb.button(text="❤️ Wishlist", callback_data=f"wishlist:toggle:{product_id}")
    kb.button(text="⭐ Reviews", callback_data=f"product:reviews:{product_id}")
    kb.button(text="⬅️ Back", callback_data="store:categories")
    if has_preview:
        kb.adjust(1, 2, 2, 2, 1)
    else:
        kb.adjust(2, 1, 2, 1)
    return kb.as_markup()


def wallet_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📜 Transaction History", callback_data="wallet:history")
    kb.button(text="➕ Top-up (Coin)", callback_data="wallet:topup")
    kb.button(text="📋 Top-up Status", callback_data="topup:status")
    kb.button(text="⬅️ Back", callback_data="menu:main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def topup_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🧾 Submit payment", callback_data="topup:start")
    kb.button(text="📋 My top-up requests", callback_data="topup:status")
    kb.button(text="⬅️ Back to Wallet", callback_data="wallet:open")
    kb.adjust(1)
    return kb.as_markup()


def topup_method_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="bKash", callback_data="topup:method:bkash")
    kb.button(text="Nagad", callback_data="topup:method:nagad")
    kb.button(text="❌ Cancel", callback_data="wallet:open")
    kb.adjust(2, 1)
    return kb.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Add Product", callback_data="admin:add_product")
    kb.button(text="📋 Manage Products", callback_data="admin:list_products")
    kb.button(text="📂 Add Category", callback_data="admin:add_category")
    kb.button(text="🪙 Add/Deduct Coin", callback_data="admin:coin")
    kb.button(text="💳 Top-up Requests", callback_data="admin:topups")
    kb.button(text="🎟️ Create Coupon", callback_data="admin:add_coupon")
    kb.button(text="🚫 Ban / Unban", callback_data="admin:ban")
    kb.button(text="📊 Sales Stats", callback_data="admin:stats")
    kb.button(text="🗄 Backup Now", callback_data="admin:backup_now")
    kb.button(text="📢 Broadcast", callback_data="admin:broadcast")
    kb.button(text="📌 Force Join", callback_data="admin:force_join")
    kb.button(text="🎁 Referral Settings", callback_data="admin:referral_settings")
    kb.button(text="🔗 Link Management", callback_data="admin:links")
    kb.button(text="🧾 Audit Log", callback_data="admin:logs")
    kb.button(text="🛠 Maintenance", callback_data="admin:maintenance")
    kb.button(text="🆘 Support Tickets", callback_data="admin:tickets")
    kb.adjust(2)
    return kb.as_markup()


def admin_product_list_kb(products: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in products:
        status = "✅" if p["is_active"] else "🚫"
        kb.button(text=f"{status} {p['name']}", callback_data=f"admin:product:view:{p['product_id']}")
    kb.button(text="⬅️ Back", callback_data="admin:panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_product_tools_kb(product_id: int, featured: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Edit / Price", callback_data=f"admin:product:edit:{product_id}")
    kb.button(
        text="⭐ Unfeature" if featured else "⭐ Feature",
        callback_data=f"admin:product:feature:{product_id}",
    )
    kb.button(text="🗑 Delete (Archive)", callback_data=f"admin:product:delete:{product_id}")
    kb.button(text="⬅️ Product List", callback_data="admin:list_products")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def admin_topup_list_kb(requests: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for request in requests:
        username = f"@{request['username']}" if request.get("username") else str(request["user_id"])
        method = request["payment_method"].upper()
        kb.button(
            text=f"#{request['request_id']} · {method} · {request['coin_amount']} 🪙 · {username}",
            callback_data=f"admin:topup:view:{request['request_id']}",
        )
    kb.button(text="⬅️ Back", callback_data="admin:panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_topup_review_kb(request_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Approve & Add Coins", callback_data=f"admin:topup:approve:{request_id}")
    kb.button(text="❌ Reject", callback_data=f"admin:topup:reject:{request_id}")
    kb.button(text="⬅️ Pending List", callback_data="admin:topups")
    kb.adjust(1, 1, 1)
    return kb.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ Open Store", callback_data="store:categories")
    kb.button(text="🪙 Open Wallet", callback_data="wallet:open")
    kb.button(text="🎁 Daily Bonus", callback_data="daily:checkin")
    kb.button(text="🆘 Support", callback_data="support:open")
    kb.button(text="❓ FAQ", callback_data="help:faq")
    kb.button(text="📜 Terms", callback_data="help:terms")
    kb.button(text="🔒 Privacy", callback_data="help:privacy")
    kb.button(text="⬅️ Main Menu", callback_data="menu:main")
    kb.adjust(2, 2, 2, 2, 1)
    return kb.as_markup()


def referral_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏆 Leaderboard", callback_data="referral:leaderboard")
    kb.button(text="⬅️ Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Admin Panel", callback_data="admin:panel")
    kb.adjust(1)
    return kb.as_markup()


def force_join_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    """User-facing 'join these to continue' gate. One button per required
    channel/group (opens its invite link) plus a re-check button."""
    kb = InlineKeyboardBuilder()
    for channel in channels:
        kind = "📢" if channel.get("chat_type") == "channel" else "👥"
        kb.button(text=f"{kind} {channel['title']}", url=channel["invite_link"])
    kb.button(text="✅ Joined — Check করুন", callback_data="forcejoin:check")
    kb.adjust(1)
    return kb.as_markup()


def force_join_admin_kb(channels: list[dict], gate_enabled: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Channel/Group", callback_data="admin:forcejoin:add")
    kb.button(
        text="🔕 Disable Gate (Temporary)" if gate_enabled else "🔔 Enable Gate",
        callback_data="admin:forcejoin:toggle_gate",
    )
    for channel in channels:
        kind = "📢" if channel["chat_type"] == "channel" else "👥"
        req = "✅ Required" if channel["is_required"] else "➖ Optional"
        kb.button(
            text=f"{kind} {channel['title']} · {req}",
            callback_data=f"admin:forcejoin:toggle_req:{channel['channel_id']}",
        )
        kb.button(
            text=f"🗑 Remove {channel['title']}",
            callback_data=f"admin:forcejoin:remove:{channel['channel_id']}",
        )
    kb.button(text="⬅️ Admin Panel", callback_data="admin:panel")
    kb.adjust(1, 1, *([2] * len(channels)), 1)
    return kb.as_markup()


def force_join_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Channel", callback_data="admin:forcejoin:type:channel")
    kb.button(text="👥 Group", callback_data="admin:forcejoin:type:group")
    kb.adjust(2)
    return kb.as_markup()


def force_join_required_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Required (Mandatory)", callback_data="admin:forcejoin:required:1")
    kb.button(text="➖ Optional", callback_data="admin:forcejoin:required:0")
    kb.adjust(1)
    return kb.as_markup()


def referral_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏆 Top Referrers", callback_data="admin:referral:top")
    kb.button(text="🎯 Milestones", callback_data="admin:referral:milestones")
    kb.button(
        text="🔁 Revoke-on-leave: toggle",
        callback_data="admin:referral:toggle_revoke",
    )
    kb.button(
        text="🧬 Level-2 bonus: toggle",
        callback_data="admin:referral:toggle_level2",
    )
    kb.button(
        text="⏰ Join reminder: toggle",
        callback_data="admin:referral:toggle_reminder",
    )
    kb.button(text="⬅️ Admin Panel", callback_data="admin:panel")
    kb.adjust(1)
    return kb.as_markup()


def milestone_list_kb(milestones: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Milestone", callback_data="admin:referral:milestone_add")
    for m in milestones:
        kb.button(
            text=f"🗑 {m['threshold']} referrals → 🪙{m['reward_coin']}",
            callback_data=f"admin:referral:milestone_del:{m['milestone_id']}",
        )
    kb.button(text="⬅️ Referral Settings", callback_data="admin:referral_settings")
    kb.adjust(1)
    return kb.as_markup()


def admin_ticket_list_kb(tickets: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ticket in tickets:
        username = f"@{ticket['username']}" if ticket.get("username") else str(ticket["user_id"])
        kb.button(
            text=f"#{ticket['ticket_id']} · {username}",
            callback_data=f"admin:ticket:view:{ticket['ticket_id']}",
        )
    kb.button(text="⬅️ Admin Panel", callback_data="admin:panel")
    kb.adjust(1)
    return kb.as_markup()


def search_results_kb(products: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for product in products:
        featured = "⭐ " if product.get("is_featured") else ""
        kb.button(
            text=f"{featured}{product['name']} · 🪙{product['price_coin']}",
            callback_data=f"store:product:{product['product_id']}",
        )
    kb.button(text="🔎 New Search", callback_data="search:start")
    kb.button(text="⬅️ Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def wishlist_kb(products: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(
            text=f"❤️ {product['name']}",
            callback_data=f"store:product:{product['product_id']}",
        )
    kb.button(text="⬅️ Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def rating_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for rating in range(1, 6):
        kb.button(text=f"{'⭐' * rating}", callback_data=f"review:rating:{product_id}:{rating}")
    kb.button(text="❌ Cancel", callback_data="orders:mine")
    kb.adjust(5, 1)
    return kb.as_markup()


def support_admin_kb(ticket_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Reply & Close", callback_data=f"admin:ticket:reply:{ticket_id}")
    kb.adjust(1)
    return kb.as_markup()


def language_picker_kb() -> InlineKeyboardMarkup:
    from locales.strings import SUPPORTED_LANGUAGES

    kb = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGUAGES.items():
        kb.button(text=label, callback_data=f"settings:lang:{code}")
    kb.button(text="⬅️ Settings", callback_data="menu:settings")
    kb.adjust(2)
    return kb.as_markup()
    kb = InlineKeyboardBuilder()
    for channel in channels:
        icon = "📢" if channel.get("chat_type", "channel") == "channel" else "👥"
        kb.button(text=f"{icon} Join {channel['title']}", url=channel["invite_link"])
    kb.button(text="✅ I Joined — Check", callback_data="forcejoin:check")
    kb.adjust(1)
    return kb.as_markup()


def link_list_kb(links: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for link in links:
        state = "✅" if link["is_active"] else "🚫"
        kb.button(
            text=f"{state} {link['token']} · {link['views']} views",
            callback_data=f"link:view:{link['token']}",
        )
    kb.button(text="⬅️ Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def link_detail_kb(link: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🚫 Disable" if link["is_active"] else "✅ Enable",
        callback_data=f"link:toggle:{link['token']}",
    )
    kb.button(text="🗑 Delete Permanently", callback_data=f"link:delete:{link['token']}")
    kb.button(text="⬅️ My Links", callback_data="linkgen:mylinks")
    kb.adjust(2, 1)
    return kb.as_markup()


def link_delete_confirm_kb(token: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⚠️ হ্যাঁ, মুছে ফেলুন", callback_data=f"link:delete_confirm:{token}")
    kb.button(text="❌ বাতিল", callback_data=f"link:view:{token}")
    kb.adjust(1)
    return kb.as_markup()


def admin_link_list_kb(links: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for link in links:
        state = "✅" if link["is_active"] else "🚫"
        owner = f"@{link['username']}" if link.get("username") else str(link["owner_id"])
        kb.button(
            text=f"{state} {link['token']} · {owner} · {link['views']}👁",
            callback_data=f"admin:link:view:{link['token']}",
        )
    kb.button(text="⬅️ Admin Panel", callback_data="admin:panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_link_detail_kb(token: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Force Delete", callback_data=f"admin:link:delete:{token}")
    kb.button(text="⬅️ Link List", callback_data="admin:links")
    kb.adjust(1)
    return kb.as_markup()
