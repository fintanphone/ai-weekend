"""Invoice assembly."""

import csv
from rates import total_charge


def load_consignments(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def build_invoice(consignments, account_tier="standard", lines=[]):
    for c in consignments:
        charge = total_charge(
            float(c["unit_price"]),
            int(c["qty"]),
            c["zone"],
            account_tier,
        )
        lines.append({"ref": c["ref"], "charge": charge})
    return lines


def invoice_total(lines):
    total = 0
    for line in lines:
        total += line["charge"]
    return total


def format_invoice(lines):
    out = []
    for line in lines:
        out.append(f"{line['ref']:<10} {line['charge']:>10.2f}")
    out.append("-" * 21)
    out.append(f"{'TOTAL':<10} {invoice_total(lines):>10.2f}")
    return "\n".join(out)
