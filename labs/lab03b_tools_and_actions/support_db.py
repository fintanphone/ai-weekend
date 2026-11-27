#!/usr/bin/env python3
"""The database layer for Lab 3b. There is nothing agentic in this file.

It runs on SQLite with no setup whatsoever, or on PostgreSQL if you set
DATABASE_URL:

    (nothing set)                               -> support.db next to this file
    DATABASE_URL=postgresql://user@host:5432/db -> that server

The SQL is identical either way. Only the placeholder style differs, which is
the only thing `_q()` exists for. Run `python support_db.py` to see which
backend you are on.

Read `find_tickets` carefully. Every parameter the model is allowed to choose
is a decision about what the model is allowed to see, and that is the whole
lesson of this lab.
"""

import os
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
SQLITE_PATH = HERE / "support.db"

STATUSES = ("open", "closed", "any")


# ==========================================================================
# Connection
# ==========================================================================

def flavour() -> str:
    """'postgres' if DATABASE_URL is set, otherwise 'sqlite'."""
    return "postgres" if os.environ.get("DATABASE_URL", "").strip() else "sqlite"


def connect():
    if flavour() == "sqlite":
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    url = os.environ["DATABASE_URL"].strip()
    try:
        import psycopg
    except ImportError:
        raise SystemExit(
            "DATABASE_URL is set but the psycopg driver is missing.\n"
            "  Fix:   python -m pip install 'psycopg[binary]'\n"
            "  Or:    unset DATABASE_URL     (falls back to SQLite, no install)"
        )
    from psycopg.rows import dict_row

    try:
        return psycopg.connect(url, row_factory=dict_row)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"Could not reach PostgreSQL at the DATABASE_URL you set.\n  {exc}\n"
            "  Fix: check the host, port and password, or unset DATABASE_URL to\n"
            "       use SQLite instead. The lab works identically on either."
        )


def _q(sql: str) -> str:
    """SQLite wants `?`, psycopg wants `%s`. Same SQL otherwise."""
    return sql if flavour() == "sqlite" else sql.replace("?", "%s")


def fetch(sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT and return rows as plain dicts of strings.

    Normalising to strings here means the agent sees byte-identical tool
    output on SQLite and on PostgreSQL, which matters when you are comparing
    two runs and wondering why they differ.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(_q(sql), params)
        rows = [dict(r) for r in cur.fetchall()]
    return [{k: ("" if v is None else str(v)) for k, v in row.items()} for row in rows]


# ==========================================================================
# The two queries the agent's tools are allowed to make
#
# Note what is NOT here: anything that takes SQL as an argument. The model
# chooses values for named parameters. It never composes a query.
# ==========================================================================

def lookup_customer_by_email(email_address: str) -> dict | None:
    """Resolve a sender's email address to a customer, by its domain.

    This is the authentication step, such as it is. In a real system the
    sender would be verified; here the domain is all we have.
    """
    domain = email_address.strip().lower().rsplit("@", 1)[-1]
    rows = fetch(
        "SELECT id, company, email_domain FROM customers WHERE email_domain = ?",
        (domain,),
    )
    return rows[0] if rows else None


def find_tickets(customer_id: str, status: str = "any", opened_since: str = "") -> list[dict]:
    """Support tickets for one customer.

    status:       'open' (not yet closed), 'closed', or 'any'
    opened_since: 'YYYY-MM-DD'; empty means no lower bound

    Parameterised, so a customer_id of "x' OR '1'='1" finds nothing rather
    than everything. That is a property of this function, not of the prompt.
    """
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")

    sql = "SELECT ref, subject, severity, status, opened_on, closed_on FROM tickets WHERE customer_id = ?"
    params: list = [customer_id]

    if status != "any":
        sql += " AND status = ?"
        params.append(status)
    if opened_since:
        sql += " AND opened_on >= ?"
        params.append(opened_since)

    return fetch(sql + " ORDER BY opened_on", tuple(params))


def all_customers() -> list[dict]:
    return fetch("SELECT id, company, email_domain FROM customers ORDER BY company")


if __name__ == "__main__":
    print(f"\nbackend: {flavour()}", end="")
    print(f"  ({SQLITE_PATH})" if flavour() == "sqlite" else f"  ({os.environ['DATABASE_URL']})")
    try:
        customers = all_customers()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"\nCannot read the tables. Run: python seed_db.py\n  {exc}")
    if not customers:
        raise SystemExit("\nNo customers. Run: python seed_db.py\n")
    print(f"\n{len(customers)} customers:")
    for c in customers:
        n = len(find_tickets(c["id"]))
        print(f"  {c['company']:22} {c['email_domain']:26} {n:2} tickets")
    print()
