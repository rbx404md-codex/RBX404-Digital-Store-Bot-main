from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router(name="common")


@router.message(Command("cancel"))
async def cancel_any_flow(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("কোনো চলমান কাজ নেই।")
        return
    await state.clear()
    await message.answer("❌ বাতিল করা হয়েছে।")


@router.message(Command("id"))
async def show_id(message: Message) -> None:
    await message.answer(
        f"🆔 আপনার Telegram user ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("ping"))
async def ping(message: Message) -> None:
    await message.answer("🏓 Pong · RBX404 Bot online ✅")


@router.message(Command("emojiid"))
async def emoji_id(message: Message) -> None:
    entities = list(message.entities or []) + list(message.caption_entities or [])
    ids = [entity.custom_emoji_id for entity in entities if entity.type == "custom_emoji" and entity.custom_emoji_id]
    if not ids:
        await message.answer(
            "🎨 এই মেসেজে custom emoji পাওয়া যায়নি। একটি custom emoji একই মেসেজে পাঠিয়ে "
            "<code>/emojiid</code> যোগ করে আবার চেষ্টা করুন।",
            parse_mode="HTML",
        )
        return
    await message.answer(
        "✅ পাওয়া custom emoji ID:\n" + "\n".join(f"<code>{item}</code>" for item in ids),
        parse_mode="HTML",
    )
