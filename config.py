"""
Central configuration. Everything is read from .env so the same codebase
runs unchanged on Termux, a VPS, or Railway — only the .env values differ.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _int_list(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = _int_list(os.getenv("ADMIN_IDS", ""))
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "@RBX404").lstrip("@")
BKASH_NUMBER: str = os.getenv("BKASH_NUMBER", "01838372430")
NAGAD_NUMBER: str = os.getenv("NAGAD_NUMBER", "01732466920")

STORAGE_CHANNEL_ID: int = int(os.getenv("STORAGE_CHANNEL_ID", "0"))
BACKUP_CHANNEL_ID: int = int(os.getenv("BACKUP_CHANNEL_ID", "0"))

BACKUP_INTERVAL_MINUTES: int = int(os.getenv("BACKUP_INTERVAL_MINUTES", "60"))
REFERRAL_REWARD_COIN: int = int(os.getenv("REFERRAL_REWARD_COIN", "20"))
REFERRAL_REVALIDATION_MINUTES: int = int(os.getenv("REFERRAL_REVALIDATION_MINUTES", "180"))
# Level-2 (multi-level) referral: a smaller bonus paid to the referrer's OWN
# referrer when the level-1 referral makes their first purchase. Set to 0 to
# disable regardless of the admin panel toggle.
REFERRAL_LEVEL2_REWARD_COIN: int = int(os.getenv("REFERRAL_LEVEL2_REWARD_COIN", "5"))
# Pending-join reminder sweep: nudges referred users who created an account
# but haven't finished joining the required channels/groups yet.
REFERRAL_REMINDER_HOURS: int = int(os.getenv("REFERRAL_REMINDER_HOURS", "6"))
REFERRAL_REMINDER_MAX_COUNT: int = int(os.getenv("REFERRAL_REMINDER_MAX_COUNT", "3"))
REFERRAL_REMINDER_SWEEP_MINUTES: int = int(os.getenv("REFERRAL_REMINDER_SWEEP_MINUTES", "30"))
DAILY_CHECKIN_REWARD: int = int(os.getenv("DAILY_CHECKIN_REWARD", "10"))
CUSTOM_EMOJI_ID: str = os.getenv("CUSTOM_EMOJI_ID", "").strip()

# Optional role-specific Telegram custom emoji document IDs.  When a role is
# not configured, the legacy CUSTOM_EMOJI_ID is used as the shared fallback.
CUSTOM_EMOJI_IDS: dict[str, str] = {
    role: os.getenv(f"CUSTOM_EMOJI_{role.upper()}_ID", "").strip()
    for role in (
        "brand",
        "success",
        "error",
        "store",
        "wallet",
        "referral",
        "help",
        "security",
        "support",
        "admin",
    )
}

DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")
def _auto_detect_base_url() -> str:
    """The mini web portal's public address, resolved with zero manual
    config on the hosts that support it. Priority:
      1. BASE_URL — if you set it explicitly, that always wins.
      2. Render — RENDER_EXTERNAL_URL is injected automatically.
      3. Railway — RAILWAY_PUBLIC_DOMAIN is injected once you attach a
         public domain to the service (Settings → Networking → Generate
         Domain); this stitches https:// onto it.
      4. Fly.io — derives https://<app-name>.fly.dev from FLY_APP_NAME.
      5. Nothing found — falls back to relative links (works fine inside
         Telegram, just isn't shareable outside the bot without a domain).
    """
    explicit = os.getenv("BASE_URL", "").strip().rstrip("/")
    if explicit:
        return explicit

    render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
    if render_url:
        return render_url

    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip().rstrip("/")
    if railway_domain:
        return f"https://{railway_domain}"

    fly_app = os.getenv("FLY_APP_NAME", "").strip()
    if fly_app:
        return f"https://{fly_app}.fly.dev"

    return ""


BASE_URL: str = _auto_detect_base_url()
# Railway (and most PaaS hosts) inject PORT at runtime; prefer it when
# set so the same image works unchanged on Railway, Render, Termux, etc.
WEB_PORT: int = int(os.getenv("PORT", os.getenv("WEB_PORT", "8099")))
LINK_DEFAULT_EXPIRY_HOURS: int = int(os.getenv("LINK_DEFAULT_EXPIRY_HOURS", "0"))
LINK_SIGNING_SECRET: str = os.getenv("LINK_SIGNING_SECRET", "") or BOT_TOKEN


def validate() -> None:
    """Fail loudly and clearly instead of crashing with a cryptic trace."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not ADMIN_IDS:
        missing.append("ADMIN_IDS")
    if missing:
        raise SystemExit(
            "\n❌ .env এ এই ভ্যালুগুলো সেট করা নেই: "
            + ", ".join(missing)
            + "\n👉 .env.example কপি করে .env বানান এবং মান বসান।\n"
        )
