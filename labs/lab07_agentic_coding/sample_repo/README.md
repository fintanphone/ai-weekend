# freight-billing

Calculates shipping charges for Aurora Freight.

## Business rules

- Bulk discount of 8% applies to orders of 100 units or more.
- VAT at 23% is applied after any discount.
- Zone surcharges: domestic 0%, eu 4.5%, non_eu 12%.
- Fuel levy is a flat 2.5% applied to the pre-VAT total including surcharge.
- Accounts on the `priority` tier get free handling; everyone else pays 4.50
  per consignment.

## Status

Written in a hurry two years ago. No tests. The finance team have reported that
some invoices "look a bit off" but nobody has narrowed it down.
