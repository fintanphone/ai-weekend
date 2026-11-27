#!/usr/bin/env python3
"""Create and populate the support-ticket tables for Lab 3b.

    python seed_db.py            # build it (SQLite by default — no install)
    python seed_db.py --reset    # drop and rebuild
    python seed_db.py --show     # print the whole table, no agent involved

Works on SQLite or PostgreSQL; see support_db.py. Dates are generated relative
to today, so "the last year" means the same thing whenever you run the lab.
"""

import argparse
from datetime import date, timedelta

import support_db as db

TODAY = date.today()


def d(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).isoformat()


CUSTOMERS = [
    ("meridian-health", "Meridian Health", "meridianhealth.ie"),
    ("meridian-logistics", "Meridian Logistics", "meridianlogistics.com"),
    ("cobalt-systems", "Cobalt Systems", "cobaltsystems.io"),
]

# (ref, customer_id, subject, severity, status, opened_days_ago, closed_days_ago)
#
# Meridian Health's eleven tickets are arranged so that the three plausible
# readings of "open in the last year" give three different answers:
#
#   currently open                      ->  5
#   opened during the last year         ->  7
#   open at some point in the last year ->  9
#
# That is deliberate. See step 4 of the README.
TICKETS = [
    # --- Meridian Health: open, opened inside the last year (3)
    ("MH-0031", "meridian-health", "Production database unreachable", "critical", "open", 40, None),
    ("MH-0044", "meridian-health", "Nightly export silently truncating", "high", "open", 120, None),
    ("MH-0052", "meridian-health", "Portal login fails for ward staff", "high", "open", 15, None),
    # --- Meridian Health: closed, opened inside the last year (4)
    ("MH-0029", "meridian-health", "Duplicate patient records after sync", "high", "closed", 200, 190),
    ("MH-0033", "meridian-health", "Invoice PDF missing VAT line", "low", "closed", 180, 179),
    ("MH-0041", "meridian-health", "API rate limit too low for batch run", "medium", "closed", 95, 80),
    ("MH-0048", "meridian-health", "Timezone wrong on scheduled reports", "medium", "closed", 60, 58),
    # --- Meridian Health: still open, opened BEFORE the last year (2)
    ("MH-0012", "meridian-health", "Archive restore never completed", "medium", "open", 500, None),
    ("MH-0019", "meridian-health", "SSO certificate renewal unclear", "low", "open", 420, None),
    # --- Meridian Health: opened and closed BEFORE the last year (2)
    ("MH-0008", "meridian-health", "Onboarding data import failed", "high", "closed", 620, 600),
    ("MH-0015", "meridian-health", "Reporting dashboard blank on Safari", "low", "closed", 480, 470),
    # --- Meridian Logistics: a different company with a confusable name (6)
    ("ML-0101", "meridian-logistics", "Depot scanner offline in Cork", "high", "open", 30, None),
    ("ML-0104", "meridian-logistics", "Driver app crashes on route upload", "critical", "open", 9, None),
    ("ML-0097", "meridian-logistics", "Pallet weights rounding incorrectly", "medium", "closed", 150, 140),
    ("ML-0099", "meridian-logistics", "Customs paperwork template outdated", "low", "closed", 110, 100),
    ("ML-0088", "meridian-logistics", "Fuel surcharge applied twice", "high", "closed", 300, 280),
    ("ML-0072", "meridian-logistics", "Tracking webhook retries exhausted", "medium", "open", 390, None),
    # --- Cobalt Systems (5)
    ("CS-0210", "cobalt-systems", "Webhook signature mismatch", "high", "open", 22, None),
    ("CS-0204", "cobalt-systems", "Sandbox environment out of date", "low", "open", 75, None),
    ("CS-0198", "cobalt-systems", "Bulk upload rejects valid CSV", "medium", "closed", 160, 155),
    ("CS-0191", "cobalt-systems", "Latency spike on EU endpoint", "high", "closed", 240, 236),
    ("CS-0185", "cobalt-systems", "Docs example uses retired field", "low", "closed", 330, 325),
]

DATE_TYPE = {"sqlite": "TEXT", "postgres": "DATE"}


def build(reset: bool) -> None:
    dt = DATE_TYPE[db.flavour()]
    with db.connect() as conn:
        cur = conn.cursor()
        if reset:
            cur.execute("DROP TABLE IF EXISTS tickets")
            cur.execute("DROP TABLE IF EXISTS customers")

        cur.execute(
            """CREATE TABLE IF NOT EXISTS customers (
                   id            TEXT PRIMARY KEY,
                   company       TEXT NOT NULL,
                   email_domain  TEXT NOT NULL UNIQUE
               )"""
        )
        cur.execute(
            f"""CREATE TABLE IF NOT EXISTS tickets (
                    ref          TEXT PRIMARY KEY,
                    customer_id  TEXT NOT NULL REFERENCES customers(id),
                    subject      TEXT NOT NULL,
                    severity     TEXT NOT NULL,
                    status       TEXT NOT NULL,
                    opened_on    {dt} NOT NULL,
                    closed_on    {dt}
                )"""
        )

        cur.execute("DELETE FROM tickets")
        cur.execute("DELETE FROM customers")
        cur.executemany(db._q("INSERT INTO customers VALUES (?, ?, ?)"), CUSTOMERS)
        cur.executemany(
            db._q("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)"),
            [
                (ref, cid, subj, sev, st, d(opened), d(closed) if closed else None)
                for ref, cid, subj, sev, st, opened, closed in TICKETS
            ],
        )
        conn.commit()


def show() -> None:
    year_ago = d(365)
    print(f"\n  backend: {db.flavour()}     today: {TODAY}     one year ago: {year_ago}\n")
    for c in db.all_customers():
        rows = db.find_tickets(c["id"])
        print(f"  {c['company']}  <{c['email_domain']}>   {len(rows)} tickets")
        for r in rows:
            closed = r["closed_on"] or "—"
            print(f"      {r['ref']:9} {r['status']:7} opened {r['opened_on']}  closed {closed:11} {r['subject']}")
        openish = [r for r in rows if r["status"] == "open"]
        recent = [r for r in rows if r["opened_on"] >= year_ago]
        during = [r for r in rows if r["status"] == "open" or r["closed_on"] >= year_ago]
        print(
            f"      -> currently open: {len(openish)}"
            f"   opened in last year: {len(recent)}"
            f"   open during last year: {len(during)}\n"
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="drop the tables first")
    ap.add_argument("--show", action="store_true", help="print the data and exit")
    args = ap.parse_args()

    if not args.show:
        build(args.reset)
        n = sum(len(db.find_tickets(c["id"])) for c in db.all_customers())
        where = db.SQLITE_PATH if db.flavour() == "sqlite" else "PostgreSQL"
        print(f"\nSeeded {len(CUSTOMERS)} customers and {n} tickets into {where}.\n")
    show()
