"""
SQLite 데이터베이스 모듈
대화 히스토리, 설정, 로그 등을 로컬에 저장한다.
"""
import sqlite3
import os
import time
import json
from typing import Optional
from config.security import DATA_DIR, DB_PATH
from utils.logger import log


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


class Database:
    def __init__(self, db_path: str = DB_PATH):
        _ensure_data_dir()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    detail TEXT,
                    timestamp REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_conv_session
                    ON conversations(session_id);
                CREATE INDEX IF NOT EXISTS idx_event_type
                    ON event_log(event_type);
            """)
        log.info("데이터베이스 초기화 완료")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # -- 대화 히스토리 --

    def save_message(self, session_id: int, role: str, content: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, role, content, timestamp) "
                "VALUES (?, ?, ?, ?)",
                (session_id, role, content, time.time()),
            )

    def get_recent_conversations(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT session_id, role, content, timestamp "
                "FROM conversations ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"session_id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]}
            for r in reversed(rows)
        ]

    # -- 설정 --

    def set_setting(self, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) "
                "VALUES (?, ?, ?)",
                (key, value, time.time()),
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row else default

    # -- 이벤트 로그 --

    def log_event(self, event_type: str, detail: str = ""):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO event_log (event_type, detail, timestamp) "
                "VALUES (?, ?, ?)",
                (event_type, detail, time.time()),
            )

    def get_events(self, event_type: str = None, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            if event_type:
                rows = conn.execute(
                    "SELECT event_type, detail, timestamp FROM event_log "
                    "WHERE event_type = ? ORDER BY id DESC LIMIT ?",
                    (event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT event_type, detail, timestamp FROM event_log "
                    "ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [
            {"event_type": r[0], "detail": r[1], "timestamp": r[2]}
            for r in reversed(rows)
        ]
