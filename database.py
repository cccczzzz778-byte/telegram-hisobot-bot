from __future__ import annotations

from datetime import date, datetime

import asyncpg


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url,
            min_size=1,
            max_size=5,
            command_timeout=30,
        )
        async with self.pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    institution_no INTEGER NOT NULL,
                    report_date DATE NOT NULL,
                    submitted_at TIMESTAMPTZ NOT NULL,
                    telegram_user_id BIGINT,
                    telegram_name TEXT,
                    message_id BIGINT NOT NULL,
                    caption TEXT NOT NULL,
                    match_score DOUBLE PRECISION NOT NULL,
                    PRIMARY KEY (institution_no, report_date)
                )
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS bot_admins (
                    user_id BIGINT PRIMARY KEY,
                    added_by BIGINT NOT NULL,
                    added_at TIMESTAMPTZ NOT NULL
                )
            """)
            await connection.execute(
                "CREATE INDEX IF NOT EXISTS submissions_report_date_idx ON submissions (report_date)"
            )

    def _pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database hali ishga tushirilmagan")
        return self.pool

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()

    async def save_first(self, institution_no: int, submitted_at: datetime, user_id: int | None,
                         telegram_name: str, message_id: int, caption: str, match_score: float) -> bool:
        result = await self._pool().execute("""
            INSERT INTO submissions
            (institution_no, report_date, submitted_at, telegram_user_id, telegram_name,
             message_id, caption, match_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (institution_no, report_date) DO NOTHING
        """, institution_no, submitted_at.date(), submitted_at, user_id,
            telegram_name, message_id, caption, match_score)
        return result == "INSERT 0 1"

    async def get_for_date(self, report_date: str | date) -> dict[int, dict]:
        if isinstance(report_date, str):
            report_date = date.fromisoformat(report_date)
        rows = await self._pool().fetch(
            "SELECT * FROM submissions WHERE report_date = $1::date", report_date
        )
        return {row["institution_no"]: dict(row) for row in rows}

    async def is_bot_admin(self, user_id: int) -> bool:
        return await self._pool().fetchval(
            "SELECT EXISTS(SELECT 1 FROM bot_admins WHERE user_id = $1)", user_id
        )

    async def add_bot_admin(self, user_id: int, added_by: int, added_at: datetime) -> bool:
        result = await self._pool().execute("""
            INSERT INTO bot_admins (user_id, added_by, added_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, added_by, added_at)
        return result == "INSERT 0 1"
