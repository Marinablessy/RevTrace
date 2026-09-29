import json
import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).resolve().parent / "revtrace_core.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            opportunity_id TEXT,
            company TEXT NOT NULL,
            contact_name TEXT,
            industry TEXT,
            role TEXT,
            stage TEXT NOT NULL,
            current_agent TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            opportunity_id TEXT,
            agent TEXT NOT NULL,
            event_type TEXT NOT NULL,
            stage TEXT NOT NULL,
            summary TEXT NOT NULL,
            payload_json TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def create_account(account):
    now = datetime.utcnow().isoformat()

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO accounts (
            account_id,
            opportunity_id,
            company,
            contact_name,
            industry,
            role,
            stage,
            current_agent,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            account["account_id"],
            account.get("opportunity_id"),
            account["company"],
            account.get("contact_name"),
            account.get("industry"),
            account.get("role"),
            account["stage"],
            account["current_agent"],
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()


def get_account(account_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id = ?
        """,
        (account_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def get_accounts():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM accounts
        ORDER BY updated_at DESC
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def update_account_stage(
    account_id,
    stage,
    current_agent,
    opportunity_id=None,
):
    now = datetime.utcnow().isoformat()

    conn = get_connection()

    if opportunity_id:
        conn.execute(
            """
            UPDATE accounts
            SET stage = ?,
                current_agent = ?,
                opportunity_id = ?,
                updated_at = ?
            WHERE account_id = ?
            """,
            (
                stage,
                current_agent,
                opportunity_id,
                now,
                account_id,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE accounts
            SET stage = ?,
                current_agent = ?,
                updated_at = ?
            WHERE account_id = ?
            """,
            (
                stage,
                current_agent,
                now,
                account_id,
            ),
        )

    conn.commit()
    conn.close()


def create_event(event):
    now = datetime.utcnow().isoformat()

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO events (
            event_id,
            account_id,
            opportunity_id,
            agent,
            event_type,
            stage,
            summary,
            payload_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["event_id"],
            event["account_id"],
            event.get("opportunity_id"),
            event["agent"],
            event["event_type"],
            event["stage"],
            event["summary"],
            json.dumps(event.get("payload", {})),
            now,
        ),
    )

    conn.commit()
    conn.close()


def get_account_events(account_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM events
        WHERE account_id = ?
        ORDER BY created_at ASC
        """,
        (account_id,),
    ).fetchall()

    conn.close()

    results = []

    for row in rows:
        item = dict(row)

        try:
            item["payload"] = json.loads(
                item.get("payload_json") or "{}"
            )
        except Exception:
            item["payload"] = {}

        results.append(item)

    return results