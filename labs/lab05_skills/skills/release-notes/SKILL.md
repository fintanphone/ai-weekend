---
name: release-notes
description: Write release notes from a changelog, commit list, or set of code changes, in Aurora Freight's house style. Use when the user asks for release notes, a changelog entry, a version summary, or notes for a deployment.
---

# Release Notes

House style for customer-facing release notes.

## Voice

Write for a warehouse manager, not an engineer. They are competent but busy and
do not know what a migration is. Lead with what changed for them.

Never use: "we're excited to announce", "seamless", "leverage", "robust",
"under the hood", "empowers". These are banned outright.

## Structure

```
## Version <number> - <date>

<One sentence saying what this release is mostly about.>

### What's new
### Fixed
### Changed
### Known issues
```

Omit any section that would be empty, except **Known issues** — if there are
none, write "None reported."

## Rules for entries

- One line per entry. Start with a verb in past tense.
- Say the user-visible effect, not the implementation.
  - Bad: "Refactored the shipment serialiser to use streaming."
  - Good: "Shipment exports over 10,000 rows no longer time out."
- Anything that changes existing behaviour goes in **Changed**, never in
  **What's new**, even if it is an improvement. People need to find it.
- If a fix could have caused wrong data to be shown, say so explicitly and say
  which dates were affected. Never quietly fix a data correctness bug.
- No ticket numbers in customer-facing notes. Keep them in the internal version.
