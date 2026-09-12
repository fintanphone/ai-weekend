#!/usr/bin/env python3
"""Create freight.db for the Lab 6 MCP server. Run once."""

import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "freight.db"
DB.unlink(missing_ok=True)

conn = sqlite3.connect(DB)
conn.executescript(
    """
    CREATE TABLE shipments (
        ref TEXT PRIMARY KEY,
        origin TEXT, destination TEXT,
        weight_kg INTEGER, status TEXT,
        days_in_transit INTEGER, carrier TEXT, hold_reason TEXT
    );

    CREATE TABLE inventory (
        sku TEXT PRIMARY KEY,
        description TEXT, warehouse TEXT,
        qty INTEGER, unit_cost_eur REAL
    );
    """
)

conn.executemany(
    "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
    [
        ("SH-4401", "Dublin", "Rotterdam", 1240, "delivered", 3, "Vanguard", None),
        ("SH-4402", "Cork", "Hamburg", 880, "delivered", 4, "Vanguard", None),
        ("SH-4403", "Dublin", "Rotterdam", 2100, "in_transit", 2, "Northline", None),
        ("SH-4404", "Galway", "Liverpool", 340, "delayed", 9, "Northline", "customs hold"),
        ("SH-4405", "Cork", "Antwerp", 1670, "delivered", 3, "Vanguard", None),
        ("SH-4406", "Dublin", "Bilbao", 940, "delayed", 11, "Sealane", "customs hold"),
        ("SH-4407", "Dublin", "Rotterdam", 1580, "in_transit", 1, "Vanguard", None),
        ("SH-4408", "Cork", "Le Havre", 720, "delayed", 6, "Sealane", "carrier capacity"),
        ("SH-4409", "Dublin", "Hamburg", 1930, "in_transit", 3, "Northline", None),
        ("SH-4410", "Galway", "Liverpool", 410, "delivered", 2, "Northline", None),
    ],
)

conn.executemany(
    "INSERT INTO inventory VALUES (?,?,?,?,?)",
    [
        ("AF-1001", "Pallet wrap 500mm", "Dublin", 340, 12.50),
        ("AF-1002", "Pallet wrap 750mm", "Dublin", 128, 18.75),
        ("AF-1003", "Corner protectors", "Cork", 2400, 0.85),
        ("AF-1010", "Strapping tension tool", "Dublin", 17, 145.00),
        ("AF-1011", "Steel strapping 19mm", "Cork", 88, 64.20),
        ("AF-1012", "Poly strapping 12mm", "Cork", 210, 28.40),
        ("AF-1020", "Thermal labels 100x150", "Dublin", 1560, 0.06),
        ("AF-1021", "Label printer ribbon", "Galway", 45, 22.40),
        ("AF-1030", "Load bars adjustable", "Cork", 63, 38.90),
        ("AF-1031", "Edge boards 1200mm", "Galway", 890, 1.35),
    ],
)

conn.commit()
conn.close()
print(f"Created {DB} — 10 shipments, 10 inventory lines.")
