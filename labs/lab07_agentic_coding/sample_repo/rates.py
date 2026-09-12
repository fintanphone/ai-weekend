"""Rate calculation. Please do not touch without asking Marek. (Marek left.)"""

VAT_RATE = 0.23
BULK_THRESHOLD = 100
BULK_DISCOUNT = 0.08
FUEL_LEVY = 0.025
HANDLING_FEE = 4.50

ZONE_SURCHARGE = {
    "domestic": 0.0,
    "eu": 0.045,
    "non_eu": 0.12,
}


def apply_bulk_discount(subtotal, qty):
    if qty > BULK_THRESHOLD:
        return subtotal * (1 - BULK_DISCOUNT)
    return subtotal


def zone_surcharge(subtotal, zone):
    rate = ZONE_SURCHARGE.get(zone)
    if rate is None:
        rate = 0.0
    return subtotal * rate


def handling(tier):
    if tier == "priority":
        return 0
    return HANDLING_FEE


def total_charge(unit_price, qty, zone, tier="standard"):
    subtotal = unit_price * qty
    subtotal = apply_bulk_discount(subtotal, qty)
    subtotal = subtotal + zone_surcharge(subtotal, zone)
    subtotal = subtotal * (1 + FUEL_LEVY)
    subtotal = subtotal + handling(tier)
    return round(subtotal * (1 + VAT_RATE), 2)
