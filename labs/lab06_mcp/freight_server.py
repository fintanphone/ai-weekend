#!/usr/bin/env python3
"""Lab 6 — an MCP server, about 60 lines.

Exposes a local SQLite database as tools that ANY MCP client can use:
Claude Code, Claude Desktop, or something you write yourself.

Run `python seed_db.py` first, then register this with a client (see README).
To sanity-check it standalone:

    python freight_server.py          # starts on stdio and waits
"""

import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB = Path(__file__).parent / "freight.db"

mcp = FastMCP("aurora-freight")


def query(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


@mcp.tool()
def list_shipments(status: str = "all", limit: int = 20) -> str:
    """List shipments, optionally filtered by status.

    Args:
        status: One of 'all', 'delivered', 'in_transit', 'delayed'.
        limit: Maximum rows to return (default 20).
    """
    if status == "all":
        rows = query("SELECT * FROM shipments ORDER BY ref LIMIT ?", (limit,))
    else:
        rows = query(
            "SELECT * FROM shipments WHERE status = ? ORDER BY ref LIMIT ?", (status, limit)
        )
    if not rows:
        return f"No shipments with status {status!r}."
    header = " | ".join(rows[0].keys())
    body = "\n".join(" | ".join(str(v) for v in r.values()) for r in rows)
    return f"{header}\n{body}"


@mcp.tool()
def shipment_detail(ref: str) -> str:
    """Get full detail for a single shipment by its reference.

    Args:
        ref: Shipment reference, e.g. 'SH-4404'.
    """
    rows = query("SELECT * FROM shipments WHERE ref = ?", (ref,))
    if not rows:
        return f"No shipment with reference {ref!r}."
    return "\n".join(f"{k}: {v}" for k, v in rows[0].items())


@mcp.tool()
def stock_by_warehouse(warehouse: str) -> str:
    """Show inventory held at one warehouse, with total value.

    Args:
        warehouse: Warehouse name, e.g. 'Dublin', 'Cork', 'Galway'.
    """
    rows = query(
        "SELECT sku, description, qty, unit_cost_eur FROM inventory "
        "WHERE warehouse = ? ORDER BY sku",
        (warehouse,),
    )
    if not rows:
        return f"No stock at {warehouse!r}."
    total = sum(r["qty"] * r["unit_cost_eur"] for r in rows)
    lines = [f"{r['sku']}  {r['description']:<28} qty={r['qty']:<6} @ {r['unit_cost_eur']:.2f}"
             for r in rows]
    return "\n".join(lines) + f"\n\nTotal value: EUR {total:,.2f}"


@mcp.tool()
def search_inventory(term: str) -> str:
    """Search inventory descriptions for a term.

    Args:
        term: Substring to search for, e.g. 'strapping'.
    """
    rows = query(
        "SELECT sku, description, warehouse, qty FROM inventory "
        "WHERE description LIKE ? ORDER BY sku",
        (f"%{term}%",),
    )
    if not rows:
        return f"Nothing matching {term!r}."
    return "\n".join(
        f"{r['sku']}  {r['description']:<28} {r['warehouse']:<8} qty={r['qty']}" for r in rows
    )


# Note what is NOT here: there is no `run_sql` tool taking arbitrary SQL.
# That would be far more flexible and a genuinely bad idea. Discuss in the lab.


if __name__ == "__main__":
    if not DB.exists():
        raise SystemExit("freight.db missing — run: python seed_db.py")
    mcp.run()
