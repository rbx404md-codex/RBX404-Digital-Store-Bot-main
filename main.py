"""
Single entry point. `git clone` -> fill .env -> `python main.py` and
everything (db restore/creation, scheduled backups, handlers) wires itself
up automatically. No manual setup steps beyond .env.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ErrorEvent

import config
from database.models import init_db
from database.backup_restore import restore_latest, backup_and_pin
from database.queries import cleanup_shared_links
from handlers import root_router
from middlewares import AccessMiddleware
from utils.throttling import ThrottlingMiddleware
# Add import after line 20:
from web_portal_distribution import get_distribution_app

# In async main(), after start_web_server call (line ~105):
# Add distribution app to web server:
from services import referral_engine
from utils.bot import BrandedBot
from web_portal import start_web_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("main")


async def on_error(event: ErrorEvent) -> bool:
    """
    Catches any exception raised inside a handler so one bad update never
    takes the whole bot down — it just gets logged, and the user's update
    is skipped instead of crashing the polling loop.
    """
    log.error("Unhandled error while processing update: %s", event.exception, exc_info=event.exception)
    return True


async def periodic_backup(bot: Bot) -> None:
    if not config.BACKUP_CHANNEL_ID:
        log.info("Automatic backups disabled until BACKUP_CHANNEL_ID is configured.")
        return
    interval = max(5, config.BACKUP_INTERVAL_MINUTES) * 60
    while True:
        await asyncio.sleep(interval)
        try:
            await backup_and_pin(bot, note="auto")
        except Exception as e:  # noqa: BLE001 — never let a backup failure kill the bot
            log.error("Auto-backup failed: %s", e)


async def periodic_referral_revalidation(bot: Bot) -> None:
    """Leave-detection sweep: catches referred users who quietly left a
    required channel/group after being verified, so referral counts stay
    honest without needing the user to open the bot again."""
    interval = max(10, config.REFERRAL_REVALIDATION_MINUTES) * 60
    while True:
        await asyncio.sleep(interval)
        try:
            checked, revoked = await referral_engine.revalidate_all_active(bot)
            if revoked:
                log.info("Referral revalidation: checked %s, revoked %s", checked, revoked)
        except Exception as e:  # noqa: BLE001 — never let this loop kill the bot
            log.error("Referral revalidation failed: %s", e)


async def periodic_referral_reminders(bot: Bot) -> None:
    """Nudges referred users stuck in 'pending' (haven't finished joining
    the required channels/groups) so referrers aren't left waiting forever
    on someone who just forgot to finish the last step."""
    interval = max(5, config.REFERRAL_REMINDER_SWEEP_MINUTES) * 60
    while True:
        await asyncio.sleep(interval)
        try:
            reminded, auto_activated = await referral_engine.send_pending_reminders(bot)
            if reminded or auto_activated:
                log.info(
                    "Referral reminder sweep: reminded %s, auto-activated %s",
                    reminded, auto_activated,
                )
        except Exception as e:  # noqa: BLE001 — never let this loop kill the bot
            log.error("Referral reminder sweep failed: %s", e)


async def periodic_link_cleanup() -> None:
    """Deletes expired shared links every 30 minutes so old tokens don't
    pile up in the database indefinitely."""
    while True:
        await asyncio.sleep(30 * 60)
        try:
            removed = await cleanup_shared_links()
            if removed:
                log.info("Expired-link cleanup removed %s link(s).", removed)
        except Exception as e:  # noqa: BLE001
            log.error("Link cleanup failed: %s", e)


async def main() -> None:
    config.validate()

    bot = BrandedBot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.callback_query.outer_middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(AccessMiddleware())
    dp.callback_query.outer_middleware(AccessMiddleware())
    dp.include_router(root_router)
    dp.errors.register(on_error)

    await bot.set_my_commands([
        BotCommand(command="start", description="বট শুরু করুন / মেনু দেখুন"),
        BotCommand(command="help", description="বট ব্যবহারের নিয়ম"),
        BotCommand(command="cancel", description="চলমান কাজ বাতিল করুন"),
        BotCommand(command="admin", description="অ্যাডমিন প্যানেল (শুধু অ্যাডমিনদের জন্য)"),
        BotCommand(command="skip", description="Preview না দিয়ে পরের ধাপে যান"),
        BotCommand(command="search", description="Product search করুন"),
        BotCommand(command="checkin", description="আজকের Daily Bonus নিন"),
        BotCommand(command="support", description="Support ticket খুলুন"),
        BotCommand(command="linkgen", description="Secure share link বানান"),
        BotCommand(command="mylinks", description="আপনার generated links"),
        BotCommand(command="id", description="আপনার Telegram ID"),
        BotCommand(command="ping", description="Bot status check"),
        BotCommand(command="emojiid", description="Custom emoji ID বের করুন"),
    ])

    log.info("Checking for an existing backup to restore...")
    restored = await restore_latest(bot)
    log.info("Restored from backup channel." if restored else "Starting with local/fresh database.")

    await init_db()
    log.info("Database ready at %s", config.DB_PATH)

    await start_web_server(bot)
    site_url = config.BASE_URL or f"http://<your-server-ip>:{config.WEB_PORT}"
    log.info("Mini web portal listening on port %s — public address: %s", config.WEB_PORT, site_url)
    if config.BASE_URL and config.ADMIN_IDS:
        try:
            await bot.send_message(
                config.ADMIN_IDS[0],
                f"🌐 Mini Web Portal লাইভ হয়েছে:\n{config.BASE_URL}\n\n"
                "এটাই আপনার generated link/share page-এর ঠিকানা — /linkgen দিয়ে তৈরি সব লিংক "
                "এই ডোমেইনের নিচে খুলবে।",
            )
        except Exception:  # noqa: BLE001 — never block startup on a DM failure
            pass
    asyncio.create_task(periodic_backup(bot))
    asyncio.create_task(periodic_referral_revalidation(bot))
    asyncio.create_task(periodic_referral_reminders(bot))
    asyncio.create_task(periodic_link_cleanup())

    log.info("Bot starting (long polling)...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped.")
