#!/usr/bin/env python3
"""Create the Lab 9 sandbox. Run once, and again to reset."""

from pathlib import Path

SANDBOX = Path(__file__).parent / "sandbox"

SALES = """region,quarter,units,revenue_eur
Dublin,Q1,1240,186000
Dublin,Q2,1388,208200
Cork,Q1,890,133500
Cork,Q2,812,121800
Galway,Q1,430,64500
Galway,Q2,610,91500
Rotterdam,Q1,2100,315000
Rotterdam,Q2,2340,351000
"""

HEADCOUNT = """site,department,headcount
Dublin,warehouse,42
Dublin,office,18
Cork,warehouse,31
Galway,warehouse,12
Rotterdam,warehouse,55
Rotterdam,office,9
"""


def main():
    SANDBOX.mkdir(exist_ok=True)
    for old in SANDBOX.iterdir():
        if old.is_file():
            old.unlink()

    (SANDBOX / "sales.csv").write_text(SALES)
    (SANDBOX / "headcount.csv").write_text(HEADCOUNT)

    print(f"Created {SANDBOX}")
    for f in sorted(SANDBOX.iterdir()):
        print(f"   {f.name:<18} {f.stat().st_size:>6} bytes")
    print()
    print("Rotterdam is the top region by revenue (666,000 EUR across both")
    print("quarters) - useful to know so you can grade the agent's answer.")
    print()
    print("Next:  python step1_what_breaks.py")


if __name__ == "__main__":
    main()
