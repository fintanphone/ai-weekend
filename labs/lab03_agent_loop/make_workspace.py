#!/usr/bin/env python3
"""Create the sandbox files the Lab 3 agent explores. Run once."""

from pathlib import Path

WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)

FILES = {
    "inventory.csv": """sku,description,warehouse,qty,unit_cost_eur
AF-1001,Pallet wrap 500mm,Dublin,340,12.50
AF-1002,Pallet wrap 750mm,Dublin,128,18.75
AF-1003,Corner protectors,Cork,2400,0.85
AF-1010,Strapping tension tool,Dublin,17,145.00
AF-1011,Steel strapping 19mm,Cork,88,64.20
AF-1020,Thermal labels 100x150,Dublin,1560,0.06
AF-1021,Label printer ribbon,Galway,45,22.40
AF-1030,Load bars adjustable,Cork,63,38.90
""",
    "shipments.csv": """ref,origin,destination,weight_kg,status,days_in_transit
SH-4401,Dublin,Rotterdam,1240,delivered,3
SH-4402,Cork,Hamburg,880,delivered,4
SH-4403,Dublin,Rotterdam,2100,in_transit,2
SH-4404,Galway,Liverpool,340,delayed,9
SH-4405,Cork,Antwerp,1670,delivered,3
SH-4406,Dublin,Bilbao,940,delayed,11
SH-4407,Dublin,Rotterdam,1580,in_transit,1
""",
    "notes.md": """# Warehouse notes — Q3

Cork has been running consistently over capacity since the Antwerp route
opened. Worth reviewing whether the strapping stock should move to Dublin.

The two delayed shipments (SH-4404, SH-4406) are both customs holds, not
carrier problems. Different issue entirely, and we keep conflating them in
the weekly report.

Reorder threshold is currently 50 units for anything under 20 euro unit cost,
and 20 units for anything above. Nobody has checked whether that's still
sensible since we changed suppliers.
""",
    "pricing.py": """\"\"\"Pricing helpers. Deliberately small.\"\"\"

VAT_RATE = 0.23
BULK_THRESHOLD = 100
BULK_DISCOUNT = 0.08


def line_total(unit_cost, qty):
    subtotal = unit_cost * qty
    if qty >= BULK_THRESHOLD:
        subtotal *= (1 - BULK_DISCOUNT)
    return round(subtotal * (1 + VAT_RATE), 2)


def margin(sell_price, unit_cost):
    if sell_price <= 0:
        return 0.0
    return round((sell_price - unit_cost) / sell_price, 4)
""",
    "report.py": """\"\"\"Generates the weekly summary. Nobody reads it.\"\"\"

import csv


def load(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def delayed_shipments(rows):
    return [r for r in rows if r["status"] == "delayed"]


def total_stock_value(rows):
    return sum(float(r["qty"]) * float(r["unit_cost_eur"]) for r in rows)


def main():
    shipments = load("shipments.csv")
    inventory = load("inventory.csv")
    print(f"Delayed: {len(delayed_shipments(shipments))}")
    print(f"Stock value: EUR {total_stock_value(inventory):,.2f}")


if __name__ == "__main__":
    main()
""",
}

for name, content in FILES.items():
    (WORKSPACE / name).write_text(content)

print(f"Created {len(FILES)} files in {WORKSPACE}")
for name in sorted(FILES):
    print(f"  {name}")
