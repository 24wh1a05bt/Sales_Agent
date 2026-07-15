"""
database.py
Handles SQLite schema creation and all data-access helpers for the
Lead Qualification & Outreach Agent.

Tables map directly to the spec (Module 8 - Database Tables):
    leads, enrichment, email_draft, audit_log, users, icp_settings
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "lead_agent.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('SDR','Sales Manager','Admin'))
        );

        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            company TEXT,
            email TEXT,
            phone TEXT,
            role TEXT,
            website TEXT,
            country TEXT,
            notes TEXT,
            score INTEGER DEFAULT 0,
            classification TEXT DEFAULT 'Unscored',
            classification_reason TEXT,
            status TEXT DEFAULT 'New',
            source TEXT DEFAULT 'Manual Entry',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS enrichment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            industry TEXT,
            company_size TEXT,
            revenue TEXT,
            employee_count INTEGER,
            linkedin TEXT,
            technology_stack TEXT,
            funding TEXT,
            buying_signals TEXT,
            decision_maker_status TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS icp_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_targets TEXT,
            revenue_min INTEGER,
            revenue_max INTEGER,
            employee_min INTEGER,
            employee_max INTEGER,
            job_titles TEXT,
            buying_intent_keywords TEXT,
            company_growth TEXT,
            weights TEXT
        );

        CREATE TABLE IF NOT EXISTS email_draft (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            subject TEXT,
            body TEXT,
            approved INTEGER DEFAULT 0,
            approved_by TEXT,
            status TEXT DEFAULT 'Pending Review',
            version INTEGER DEFAULT 1,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            action TEXT,
            reason TEXT,
            prompt TEXT,
            response TEXT,
            actor TEXT,
            timestamp TEXT
        );
        """
    )
    conn.commit()

    # Seed a default ICP + default users if empty
    if cur.execute("SELECT COUNT(*) FROM icp_settings").fetchone()[0] == 0:
        cur.execute(
            """INSERT INTO icp_settings
               (industry_targets, revenue_min, revenue_max, employee_min, employee_max,
                job_titles, buying_intent_keywords, company_growth, weights)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                json.dumps(["Software", "SaaS", "Fintech", "E-commerce"]),
                1_000_000,
                500_000_000,
                10,
                5000,
                json.dumps(["CEO", "CTO", "VP Sales", "Head of Growth", "Founder"]),
                json.dumps(["hiring", "funding round", "new office", "product launch"]),
                "Growing",
                json.dumps(
                    {
                        "industry_match": 20,
                        "decision_maker": 20,
                        "buying_intent": 20,
                        "revenue": 15,
                        "company_size": 15,
                        "technology_match": 10,
                    }
                ),
            ),
        )

    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        import bcrypt

        default_users = [
            ("Sam SDR", "sdr@demo.com", "password123", "SDR"),
            ("Mia Manager", "manager@demo.com", "password123", "Sales Manager"),
            ("Alex Admin", "admin@demo.com", "password123", "Admin"),
        ]
        for name, email, pw, role in default_users:
            pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                (name, email, pw_hash, role),
            )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------- leads ----
def insert_lead(data: dict, source="Manual Entry") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO leads (name, company, email, phone, role, website, country,
                               notes, status, source, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data.get("name"),
            data.get("company"),
            data.get("email"),
            data.get("phone"),
            data.get("role"),
            data.get("website"),
            data.get("country"),
            data.get("notes"),
            "New",
            source,
            datetime.utcnow().isoformat(),
        ),
    )
    lead_id = cur.lastrowid
    conn.commit()
    conn.close()
    return lead_id


def get_leads(status=None, classification=None):
    conn = get_connection()
    query = "SELECT * FROM leads"
    clauses, params = [], []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if classification:
        clauses.append("classification = ?")
        params.append(classification)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_lead(lead_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_lead(lead_id: int, fields: dict):
    conn = get_connection()
    cur = conn.cursor()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    cur.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", (*fields.values(), lead_id))
    conn.commit()
    conn.close()


def delete_lead(lead_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------ enrichment ---
def upsert_enrichment(lead_id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM enrichment WHERE lead_id = ?", (lead_id,)).fetchone()
    payload = (
        data.get("industry"),
        data.get("company_size"),
        data.get("revenue"),
        data.get("employee_count"),
        data.get("linkedin"),
        data.get("technology_stack"),
        data.get("funding"),
        data.get("buying_signals"),
        data.get("decision_maker_status"),
        datetime.utcnow().isoformat(),
    )
    if existing:
        cur.execute(
            """UPDATE enrichment SET industry=?, company_size=?, revenue=?, employee_count=?,
               linkedin=?, technology_stack=?, funding=?, buying_signals=?,
               decision_maker_status=?, updated_at=? WHERE lead_id = ?""",
            (*payload, lead_id),
        )
    else:
        cur.execute(
            """INSERT INTO enrichment (industry, company_size, revenue, employee_count,
               linkedin, technology_stack, funding, buying_signals, decision_maker_status,
               updated_at, lead_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (*payload, lead_id),
        )
    conn.commit()
    conn.close()


def get_enrichment(lead_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM enrichment WHERE lead_id = ?", (lead_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ------------------------------------------------------------------ ICP ----
def get_icp():
    conn = get_connection()
    row = conn.execute("SELECT * FROM icp_settings ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    icp = dict(row)
    for key in ("industry_targets", "job_titles", "buying_intent_keywords", "weights"):
        icp[key] = json.loads(icp[key]) if icp[key] else {}
    return icp


def update_icp(icp: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE icp_settings SET industry_targets=?, revenue_min=?, revenue_max=?,
           employee_min=?, employee_max=?, job_titles=?, buying_intent_keywords=?,
           company_growth=?, weights=?""",
        (
            json.dumps(icp["industry_targets"]),
            icp["revenue_min"],
            icp["revenue_max"],
            icp["employee_min"],
            icp["employee_max"],
            json.dumps(icp["job_titles"]),
            json.dumps(icp["buying_intent_keywords"]),
            icp["company_growth"],
            json.dumps(icp["weights"]),
        ),
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------ email draft --
def insert_email_draft(lead_id: int, subject: str, body: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    version = cur.execute(
        "SELECT COALESCE(MAX(version),0)+1 FROM email_draft WHERE lead_id = ?", (lead_id,)
    ).fetchone()[0]
    cur.execute(
        """INSERT INTO email_draft (lead_id, subject, body, status, version, created_at)
           VALUES (?,?,?,?,?,?)""",
        (lead_id, subject, body, "Pending Review", version, datetime.utcnow().isoformat()),
    )
    draft_id = cur.lastrowid
    conn.commit()
    conn.close()
    return draft_id


def get_latest_draft(lead_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM email_draft WHERE lead_id = ? ORDER BY version DESC LIMIT 1", (lead_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_draft(draft_id: int, fields: dict):
    conn = get_connection()
    cur = conn.cursor()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    cur.execute(f"UPDATE email_draft SET {set_clause} WHERE id = ?", (*fields.values(), draft_id))
    conn.commit()
    conn.close()


def get_all_drafts(status=None):
    conn = get_connection()
    query = """SELECT email_draft.*, leads.name as lead_name, leads.company
               FROM email_draft JOIN leads ON leads.id = email_draft.lead_id"""
    params = []
    if status:
        query += " WHERE email_draft.status = ?"
        params.append(status)
    query += " ORDER BY email_draft.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ------------------------------------------------------------ audit log ----
def log_action(lead_id, action, reason="", prompt="", response="", actor="system"):
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_log (lead_id, action, reason, prompt, response, actor, timestamp)
           VALUES (?,?,?,?,?,?,?)""",
        (lead_id, action, reason, prompt, response, actor, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_audit_logs(lead_id=None):
    conn = get_connection()
    query = "SELECT * FROM audit_log"
    params = []
    if lead_id:
        query += " WHERE lead_id = ?"
        params.append(lead_id)
    query += " ORDER BY timestamp DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ----------------------------------------------------------------- users ---
def get_user_by_email(email: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_connection()
    rows = conn.execute("SELECT id, name, email, role FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]