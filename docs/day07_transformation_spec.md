# Day 7 Transformation Specification

## Name
- Trim leading/trailing whitespace.
- Collapse repeated internal spaces to one space.
- Preserve original capitalization.

## Email
- Trim leading/trailing whitespace.
- Convert to lowercase.

## State
Accepted values:
- OH / Ohio -> OH
- TX / Texas -> TX
- NY / New York -> NY
- OR / Oregon -> OR

Lookup ignores case and surrounding spaces.

## updated_at
- Parse as a timestamp.
- Convert to UTC.
- Store using ISO 8601 format ending in Z.
- If no timezone is provided, treat the input as UTC for this exercise.

## Phone
Phone is optional.

Accepted examples:
- 6145551234
- 614-555-1234
- (614) 555-1234
- +1 614 555 1234

Valid phone numbers are stored as:

+16145551234

Missing phone remains blank/NULL.

Unsupported phone formats are treated as transformation failures.

## Lineage
Preserve:
- source_file_name
- source_row_number

Raw source values are preserved alongside cleaned values where useful.