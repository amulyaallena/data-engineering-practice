import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def parse_timestamp(value):
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def deduplicate_customers(input_file, output_dir):
    input_file = Path(input_file)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    with input_file.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    grouped = defaultdict(list)

    for row in rows:
        customer_id = row["customer_id"]
        grouped[customer_id].append(row)

    winners = []
    duplicate_audit = []

    for customer_id, customer_rows in grouped.items():

        sorted_rows = sorted(
            customer_rows,
            key=lambda row: (
                -parse_timestamp(
                    row["updated_at"]
                ).timestamp(),
                row["source_file_name"],
                int(row["source_row_number"])
            )
        )

        winner = sorted_rows[0]
        winners.append(winner)

        for removed_row in sorted_rows[1:]:

            audit_row = dict(removed_row)

            audit_row["winner_source_file_name"] = (
                winner["source_file_name"]
            )

            audit_row["winner_source_row_number"] = (
                winner["source_row_number"]
            )

            audit_row["winner_updated_at"] = (
                winner["updated_at"]
            )

            audit_row["removal_reason"] = (
                "OLDER_OR_TIE_BREAK_DUPLICATE"
            )

            duplicate_audit.append(audit_row)

    winner_file = (
        output_dir / "deduplicated_customers.csv"
    )

    duplicate_file = (
        output_dir / "duplicate_audit.csv"
    )

    if rows:
        winner_fieldnames = list(rows[0].keys())

        with winner_file.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=winner_fieldnames
            )

            writer.writeheader()
            writer.writerows(winners)

        audit_fieldnames = (
            winner_fieldnames
            + [
                "winner_source_file_name",
                "winner_source_row_number",
                "winner_updated_at",
                "removal_reason"
            ]
        )

        with duplicate_file.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=audit_fieldnames
            )

            writer.writeheader()
            writer.writerows(duplicate_audit)

    input_count = len(rows)
    winner_count = len(winners)
    removed_count = len(duplicate_audit)

    reconciliation = (
        "PASS"
        if input_count
        == winner_count + removed_count
        else "FAIL"
    )

    print(f"Valid input rows: {input_count}")
    print(f"Winners: {winner_count}")
    print(f"Removed duplicates: {removed_count}")
    print(f"Reconciliation: {reconciliation}")

    return {
        "input_count": input_count,
        "winner_count": winner_count,
        "removed_count": removed_count,
        "reconciliation": reconciliation
    }


if __name__ == "__main__":
    deduplicate_customers(
        "data/quality/day05/valid_customers.csv",
        "data/quality/day06"
    )