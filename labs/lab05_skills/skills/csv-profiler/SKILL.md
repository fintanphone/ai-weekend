---
name: csv-profiler
description: Profile a CSV file to a consistent house standard - row/column counts, types, null rates, cardinality, and data quality flags. Use whenever the user asks about the contents, shape, quality, or summary of a CSV or tabular data file.
---

# CSV Profiler

Aurora Freight's standard profile for any tabular data file. Follow this exactly
so profiles are comparable between analysts.

## Procedure

1. Read the file with `read_file`.
2. Determine the delimiter from the header row. Do not assume comma.
3. Produce the profile in the exact section order below. Do not add sections,
   do not reorder them, do not skip a section because it seems empty — write
   "None" instead.

## Required output format

### Shape
Row count (excluding header) and column count, as `N rows x M columns`.

### Columns
A markdown table with exactly these columns: `name`, `inferred_type`,
`null_count`, `distinct_count`, `example`.

Inferred type must be one of: `integer`, `decimal`, `date`, `categorical`,
`free_text`, `identifier`. Use `identifier` when values look like keys or
reference codes, even if numeric. This distinction matters more than it looks:
identifiers must never be summed or averaged.

### Quality flags
Report any of the following that apply, one per line, each starting with a
severity in square brackets:

- `[high]` a column that should be an identifier contains duplicates
- `[high]` a numeric column contains values that cannot be parsed
- `[medium]` null rate above 5% in any column
- `[medium]` a categorical column with cardinality above 50
- `[low]` inconsistent capitalisation or whitespace in a categorical column
- `[low]` a date column with mixed formats

Write "None" if nothing applies.

### Suggested next step
One sentence. What should the analyst actually do with this file next?

## Rules

- Never speculate about business meaning. Describe the data, not the domain.
- Never recommend a modelling approach. That is not this skill's job.
- If the file has more than 20 columns, profile all of them anyway. Do not
  truncate the table.
