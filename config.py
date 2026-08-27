from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} muhit o‘zgaruvchisida ko‘rsatilmagan")
    return value


def _ids(value: str) -> frozenset[int]:
    return frozenset(int(item.strip()) for item in value.split(",") if item.strip())


def _clock(value: str) -> time:
    try:
        hour, minute = map(int, value.split(":"))
        return time(hour, minute)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("DEADLINE_TIME HH:MM shaklida bo‘lishi kerak") from exc


@dataclass(frozen=True)
class Settings:
    token: str
    target_chat_id: int
    admin_ids: frozenset[int]
    deadline: time
    timezone: ZoneInfo
    roster_file: Path
    report_title: str
    match_threshold: float
    database_url: str


def load_settings() -> Settings:
    roster = Path(os.getenv("ROSTER_FILE", "muassasalar.xlsx"))
    if not roster.is_absolute():
        roster = BASE_DIR / roster
    return Settings(
        token=_required("BOT_TOKEN"),
        target_chat_id=int(os.getenv("TARGET_CHAT_ID", "-4239058213")),
        admin_ids=_ids(os.getenv("ADMIN_IDS", "6262616970")),
        deadline=_clock(os.getenv("DEADLINE_TIME", "14:00")),
        timezone=ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent")),
        roster_file=roster,
        report_title=os.getenv("REPORT_TITLE", "083 forma").strip() or "083 forma",
        match_threshold=float(os.getenv("MATCH_THRESHOLD", "0.64")),
        database_url=_required("DATABASE_URL"),
    )
