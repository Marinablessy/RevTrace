import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "revtrace.db"
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prospects (
            prospect_id TEXT PRIMARY KEY,
            account_id TEXT,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            industry TEXT NOT NULL,
            role TEXT NOT NULL,
            company_size TEXT NOT NULL,
            pain_point TEXT NOT NULL,
            message_angle TEXT,
            message_sent TEXT,
            outcome TEXT,
            stage TEXT DEFAULT 'NEW_PROSPECT',
            meeting_date TEXT,
            meeting_time TEXT,
            meeting_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ---------------------------------------------------
    # Upgrade older database automatically
    # ---------------------------------------------------

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(prospects)"
        ).fetchall()
    }

    additions = {
        "account_id": "TEXT",
        "stage": "TEXT DEFAULT 'NEW_PROSPECT'",
        "meeting_date": "TEXT",
        "meeting_time": "TEXT",
        "meeting_status": "TEXT",
    }

    for column, definition in additions.items():

        if column not in columns:

            conn.execute(
                f"""
                ALTER TABLE prospects
                ADD COLUMN {column}
                {definition}
                """
            )

    conn.commit()
    conn.close()


def insert_prospect(prospect: dict):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO prospects (
            prospect_id,
            account_id,
            name,
            company,
            industry,
            role,
            company_size,
            pain_point,
            message_angle,
            message_sent,
            outcome,
            stage
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prospect["prospect_id"],
            prospect.get("account_id"),
            prospect["name"],
            prospect["company"],
            prospect["industry"],
            prospect["role"],
            prospect["company_size"],
            prospect["pain_point"],
            prospect.get("message_angle"),
            prospect.get("message_sent"),
            prospect.get("outcome"),
            prospect.get(
                "stage",
                "NEW_PROSPECT",
            ),
        ),
    )

    conn.commit()
    conn.close()


def get_prospect(
    prospect_id: str
):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM prospects
        WHERE prospect_id = ?
        """,
        (prospect_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def get_all_prospects():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM prospects
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def update_analysis(
    prospect_id: str,
    message_angle: str,
):
    conn = get_connection()

    conn.execute(
        """
        UPDATE prospects
        SET message_angle = ?
        WHERE prospect_id = ?
        """,
        (
            message_angle,
            prospect_id,
        ),
    )

    conn.commit()
    conn.close()


def update_message(
    prospect_id: str,
    message_angle: str,
    message_sent: str,
):
    conn = get_connection()

    conn.execute(
        """
        UPDATE prospects
        SET message_angle = ?,
            message_sent = ?,
            stage = 'OUTREACH_SENT'
        WHERE prospect_id = ?
        """,
        (
            message_angle,
            message_sent,
            prospect_id,
        ),
    )

    conn.commit()
    conn.close()


def update_outcome(
    prospect_id: str,
    outcome: str,
    stage: str,
):
    conn = get_connection()

    conn.execute(
        """
        UPDATE prospects
        SET outcome = ?,
            stage = ?
        WHERE prospect_id = ?
        """,
        (
            outcome,
            stage,
            prospect_id,
        ),
    )

    conn.commit()
    conn.close()


def schedule_meeting(
    prospect_id: str,
    meeting_date: str,
    meeting_time: str,
):
    conn = get_connection()

    conn.execute(
        """
        UPDATE prospects
        SET meeting_date = ?,
            meeting_time = ?,
            meeting_status = 'SCHEDULED',
            stage = 'MEETING_SCHEDULED'
        WHERE prospect_id = ?
        """,
        (
            meeting_date,
            meeting_time,
            prospect_id,
        ),
    )

    conn.commit()
    conn.close()


def complete_meeting(
    prospect_id: str
):
    conn = get_connection()

    conn.execute(
        """
        UPDATE prospects
        SET meeting_status = 'COMPLETED',
            stage = 'QUALIFIED_OPPORTUNITY'
        WHERE prospect_id = ?
        """,
        (prospect_id,),
    )

    conn.commit()
    conn.close()