from __future__ import annotations

import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.types import BotCommand, FSInputFile, Message

from config import Settings, load_settings
from database import Database
from report import create_report
from roster import ensure_roster_file, find_institution, load_roster


router = Router()
settings: Settings
database: Database
roster = []


async def is_admin(message: Message, bot: Bot) -> bool:
    if not message.from_user:
        return False
    if message.from_user.id in settings.admin_ids:
        return True
    if await database.is_bot_admin(message.from_user.id):
        return True
    try:
        member = await bot.get_chat_member(settings.target_chat_id, message.from_user.id)
        return member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
    except Exception:
        logging.exception("Guruh administratori tekshirilmadi. user_id=%s", message.from_user.id)
        return False


def help_text() -> str:
    return (
        "📊 Hisobot botiga xush kelibsiz!\n\n"
        "/hisobot — bugungi Excel hisobot\n"
        "/hisobot 26.08.2026 — tanlangan sana hisoboti\n"
        "/royhat — muassasalar ro‘yxati\n"
        "/stats — bugungi statistika\n"
        "/stats 26.08.2026 — tanlangan sana statistikasi\n"
        "/admin_qosh 123456789 — yangi admin qo‘shish\n"
        "/yordam — buyruqlar ro‘yxati"
    )


@router.message(Command("start"))
async def start_command(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE:
        return
    if not await is_admin(message, bot):
        user_id = message.from_user.id if message.from_user else "noma’lum"
        await message.answer(f"⛔ Sizda botdan foydalanish huquqi yo‘q.\nTelegram ID: {user_id}")
        return
    await message.answer(help_text())


@router.message(Command("yordam"))
async def help_command(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE or not await is_admin(message, bot):
        return
    await message.answer(help_text())


@router.message(F.photo)
async def capture_photo(message: Message) -> None:
    if message.chat.id != settings.target_chat_id:
        return
    caption = (message.caption or "").strip()
    if not caption:
        return
    institution, score = find_institution(caption, roster, settings.match_threshold)
    if not institution:
        logging.warning("Muassasa aniqlanmadi. message_id=%s score=%.2f", message.message_id, score)
        return
    sent = message.date.astimezone(settings.timezone)
    sender = message.from_user.full_name if message.from_user else "Noma’lum"
    await database.save_first(
        institution.number, sent, message.from_user.id if message.from_user else None,
        sender, message.message_id, caption, score,
    )


@router.message(Command("hisobot"))
async def send_report(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE:
        return
    if not await is_admin(message, bot):
        return
    today = datetime.now(settings.timezone).date()
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2:
        try:
            today = datetime.strptime(parts[1].strip(), "%d.%m.%Y").date()
        except ValueError:
            await message.answer("Sana formati: /hisobot 26.08.2026")
            return
    submissions = await database.get_for_date(today.isoformat())
    with tempfile.NamedTemporaryFile(
        prefix=f"hisobot_{today:%Y-%m-%d}_", suffix=".xlsx", delete=False
    ) as temporary:
        path = Path(temporary.name)
    try:
        create_report(roster, submissions, today, settings.deadline, settings.report_title, path)
        await message.answer_document(
            FSInputFile(path), caption=f"{today:%d.%m.%Y} kungi hisobot"
        )
    finally:
        path.unlink(missing_ok=True)


@router.message(Command("royhat"))
async def send_roster(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE or not await is_admin(message, bot):
        return
    await message.answer_document(
        FSInputFile(settings.roster_file),
        caption=f"Muassasalar ro‘yxati — jami {len(roster)} ta",
    )


@router.message(Command("stats"))
async def send_stats(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE or not await is_admin(message, bot):
        return
    report_date = datetime.now(settings.timezone).date()
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2:
        try:
            report_date = datetime.strptime(parts[1].strip(), "%d.%m.%Y").date()
        except ValueError:
            await message.answer("Sana formati: /stats 26.08.2026")
            return
    submissions = await database.get_for_date(report_date.isoformat())
    on_time = 0
    late = 0
    for submission in submissions.values():
        raw_sent = submission["submitted_at"]
        sent = raw_sent if isinstance(raw_sent, datetime) else datetime.fromisoformat(raw_sent)
        if sent.time().replace(tzinfo=None) > settings.deadline:
            late += 1
        else:
            on_time += 1
    missing = max(0, len(roster) - len(submissions))
    await message.answer(
        f"📊 {report_date:%d.%m.%Y} kungi statistika\n\n"
        f"🟢 Vaqtida topshirdi: {on_time} ta\n"
        f"🟡 Kechikdi: {late} ta\n"
        f"🔴 Topshirmadi: {missing} ta\n"
        f"📋 Jami muassasa: {len(roster)} ta"
    )


@router.message(Command("admin_qosh"))
async def add_admin(message: Message, bot: Bot) -> None:
    if message.chat.type != ChatType.PRIVATE or not await is_admin(message, bot):
        return
    parts = (message.text or "").split()
    if len(parts) != 2:
        await message.answer("Foydalanish: /admin_qosh 123456789")
        return
    try:
        new_admin_id = int(parts[1])
        if new_admin_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Telegram ID faqat musbat raqamlardan iborat bo‘lishi kerak.")
        return
    added = await database.add_bot_admin(
        new_admin_id, message.from_user.id, datetime.now(settings.timezone)
    )
    if added:
        await message.answer(f"✅ {new_admin_id} bot admini sifatida qo‘shildi.")
    else:
        await message.answer(f"ℹ️ {new_admin_id} avvaldan bot admini.")


async def main() -> None:
    global settings, database, roster
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    settings = load_settings()
    ensure_roster_file(settings.roster_file)
    roster = load_roster(settings.roster_file)
    database = Database(settings.database_url)
    await database.initialize()
    bot = Bot(settings.token)
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="hisobot", description="Excel hisobot olish"),
        BotCommand(command="royhat", description="Muassasalar ro‘yxati"),
        BotCommand(command="stats", description="Statistikani ko‘rish"),
        BotCommand(command="admin_qosh", description="Yangi admin qo‘shish"),
        BotCommand(command="yordam", description="Buyruqlar ro‘yxati"),
    ])
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=False)
    try:
        await dp.start_polling(bot, allowed_updates=["message"])
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
