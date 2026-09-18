"""Translation strings, keyed by language code then message key.

`bn` (Bangla) and `en` are fully written out since they're this bot's
primary markets. `hi`, `ur`, `ru`, `ar` are registered as selectable
languages but currently fall back to English for any key not yet
translated — add entries under those codes the same way to complete
them; nothing else in the code needs to change.
"""

SUPPORTED_LANGUAGES = {
    "bn": "🇧🇩 বাংলা",
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिन्दी",
    "ur": "🇵🇰 اردو",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
}

STRINGS: dict[str, dict[str, str]] = {
    "bn": {
        "welcome_new": "👋 স্বাগতম, {name}!\n\n⚡ RBX404 DIGITAL STORE-এ আপনাকে স্বাগতম।",
        "welcome_back": "👋 আবার স্বাগতম, {name}!",
        "menu_store": "🛍 Explore Store",
        "menu_library": "📦 My Library",
        "menu_wallet": "💰 Wallet",
        "menu_referral": "🎁 Referral",
        "menu_linkgen": "🔗 Link Generator",
        "menu_help": "❓ Help",
        "menu_settings": "⚙️ Settings",
        "menu_language": "🌐 Language",
        "language_prompt": "আপনার পছন্দের ভাষা বেছে নিন:",
        "language_saved": "✅ ভাষা {lang} সেট করা হয়েছে।",
    },
    "en": {
        "welcome_new": "👋 Welcome, {name}!\n\n⚡ Welcome to RBX404 DIGITAL STORE.",
        "welcome_back": "👋 Welcome back, {name}!",
        "menu_store": "🛍 Explore Store",
        "menu_library": "📦 My Library",
        "menu_wallet": "💰 Wallet",
        "menu_referral": "🎁 Referral",
        "menu_linkgen": "🔗 Link Generator",
        "menu_help": "❓ Help",
        "menu_settings": "⚙️ Settings",
        "menu_language": "🌐 Language",
        "language_prompt": "Choose your preferred language:",
        "language_saved": "✅ Language set to {lang}.",
    },
}
