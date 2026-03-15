"""
services/memory.py
Persistent session memory using SQLite.
Chat history now survives server restarts.

Database: ./memory.db (auto-created on first run)

Schema:
  sessions  → session_id, title, created_at, updated_at
  messages  → id, session_id, role, content, timestamp
"""

import uuid
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv('MEMORY_DB_PATH', './memory.db')
MAX_HISTORY = 40  # max messages per session (trims oldest first)


# ── DB init ────────────────────────────────────────────────────────────────

@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT PRIMARY KEY,
                title       TEXT DEFAULT 'New Chat',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id)")
        conn.commit()


_init_db()  # runs once on import


# ── Public API ─────────────────────────────────────────────────────────────

def create_session(title: str = "New Chat") -> str:
    """Create and persist a new session. Returns session_id UUID."""
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, title, created_at, updated_at) VALUES (?,?,?,?)",
            (session_id, title, now, now)
        )
        conn.commit()
    return session_id


def get_session(session_id: str) -> dict | None:
    """Get session dict with messages, or None if not found."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        return {
            'session_id': row['session_id'],
            'title':      row['title'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'messages':   _fetch_messages(conn, session_id)
        }


def add_message(session_id: str, role: str, content: str):
    """
    Save a message to SQLite.
    Auto-creates session if missing.
    Auto-titles session from first user message.
    role: 'user' | 'assistant'
    """
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        # Auto-create session if it doesn't exist
        if not conn.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone():
            conn.execute(
                "INSERT INTO sessions (session_id, title, created_at, updated_at) VALUES (?,?,?,?)",
                (session_id, "New Chat", now, now)
            )

        # Insert message
        conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
            (session_id, role, content, now)
        )

        # Auto-title from first user message
        if role == 'user':
            title_row = conn.execute(
                "SELECT title FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if title_row and title_row['title'] == 'New Chat':
                title = content[:55] + ('...' if len(content) > 55 else '')
                conn.execute(
                    "UPDATE sessions SET title=?, updated_at=? WHERE session_id=?",
                    (title, now, session_id)
                )
            else:
                conn.execute("UPDATE sessions SET updated_at=? WHERE session_id=?", (now, session_id))

        # Trim to MAX_HISTORY
        count = conn.execute(
            "SELECT COUNT(*) as c FROM messages WHERE session_id=?", (session_id,)
        ).fetchone()['c']
        if count > MAX_HISTORY:
            conn.execute("""
                DELETE FROM messages WHERE id IN (
                    SELECT id FROM messages WHERE session_id=?
                    ORDER BY id ASC LIMIT ?
                )
            """, (session_id, count - MAX_HISTORY))

        conn.commit()


def get_history(session_id: str) -> list[dict]:
    """Return messages for a session, oldest first."""
    with _get_conn() as conn:
        return _fetch_messages(conn, session_id)


def _fetch_messages(conn, session_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT role, content, timestamp FROM messages WHERE session_id=? ORDER BY id ASC",
        (session_id,)
    ).fetchall()
    return [{'role': r['role'], 'content': r['content'], 'timestamp': r['timestamp']} for r in rows]


def list_sessions() -> list[dict]:
    """All sessions ordered by most recently updated."""
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT s.session_id, s.title, s.created_at, s.updated_at,
                   COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
        """).fetchall()
        return [{
            'session_id':    r['session_id'],
            'title':         r['title'],
            'message_count': r['message_count'],
            'created_at':    r['created_at'],
            'updated_at':    r['updated_at'],
        } for r in rows]


def delete_session(session_id: str) -> bool:
    """Delete session + all its messages (CASCADE). Returns True if found."""
    with _get_conn() as conn:
        res = conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        conn.commit()
        return res.rowcount > 0


def rename_session(session_id: str, new_title: str) -> bool:
    """Rename a session. Returns True if updated."""
    with _get_conn() as conn:
        res = conn.execute(
            "UPDATE sessions SET title=?, updated_at=? WHERE session_id=?",
            (new_title, datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()
        return res.rowcount > 0


def clear_session_messages(session_id: str):
    """Wipe messages but keep the session."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        conn.execute(
            "UPDATE sessions SET title='New Chat', updated_at=? WHERE session_id=?",
            (datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()


def get_db_stats() -> dict:
    """Stats about the memory database."""
    with _get_conn() as conn:
        sessions = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()['c']
        messages = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()['c']
    size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        'total_sessions': sessions,
        'total_messages': messages,
        'db_path':        DB_PATH,
        'db_size_kb':     round(size / 1024, 1)
    }
