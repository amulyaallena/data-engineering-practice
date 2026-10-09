import csv
import json
import re
from datetime import datetime
from pathlib import Path


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def load_state_mapping(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value):
    if value is None:
        return ""
    return value.strip()


def is_valid_email(value):
    value = normalize(value)

    if value == "":
        return False

    return EMAIL_PATTERN.fullmatch(value) is not None


def is_valid_timestamp(value):
    value = normalize(value)

    if value == "":
        return False

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_customers(
    input_file,
    state_mapping_file,
    output_dir
):
    input_file = Path(input_file)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    state_mapping = load_state_mapping(state_mapping_file)

    valid_rows = []
    invalid_rows = []

    rule_failure_counts = {
        "MISSING_CUSTOMER_ID": 0,
        "BLANK_CUSTOMER_NAME": 0,
        "INVALID_EMAIL": 0,
        "INVALID_STATE": 0,
        "MISSING_UPDATED_AT": 0,
        "INVALID_UPDATED_AT": 0
    }

    with input_file.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for source_row_number, row in enumerate(reader, start=2):

            failures = []

            customer_id_check = normalize(
                row.get("customer_id")
            )

            customer_name_check = normalize(
                row.get("customer_name")
            )

            email_check = normalize(
                row.get("email")
            )

            state_check = normalize(
                row.get("state")
            ).lower()

            updated_at_check = normalize(
                row.get("updated_at")
            )

            if customer_id_check == "":
                failures.append("MISSING_CUSTOMER_ID")

            if customer_name_check == "":
                failures.append("BLANK_CUSTOMER_NAME")

            if not is_valid_email(email_check):
                failures.append("INVALID_EMAIL")

            if state_check not in state_mapping:
                failures.append("INVALID_STATE")

            if updated_at_check == "":
                failures.append("MISSING_UPDATED_AT")
            elif not is_valid_timestamp(updated_at_check):
                failures.append("INVALID_UPDATED_AT")

            for failure in failures:
                rule_failure_counts[failure] += 1

            output_row = dict(row)

            output_row["source_file_name"] = input_file.name

            output_row["source_row_number"] = (
                str(source_row_number)
            )

            if failures:
                output_row["validation_status"] = "INVALID"
                output_row["rejection_reason"] = ";".join(failures)
                invalid_rows.append(output_row)

            else:
                output_row["validation_status"] = "VALID"
                output_row["rejection_reason"] = ""
                valid_rows.append(output_row)

    fieldnames = [
        "customer_id",
        "customer_name",
        "email",
        "state",
        "updated_at",
        "source_row_number",
        "source_file_name",
        "validation_status",
        "rejection_reason"
    ]

    valid_file = output_dir / "valid_customers.csv"
    invalid_file = output_dir / "invalid_customers.csv"
    summary_file = output_dir / "dq_summary.json"

    with valid_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(valid_rows)

    with invalid_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(invalid_rows)

    input_count = len(valid_rows) + len(invalid_rows)

    summary = {
        "input_count": input_count,
        "valid_count": len(valid_rows),
        "invalid_count": len(invalid_rows),
        "reconciliation_status": (
            "PASS"
            if input_count
            == len(valid_rows) + len(invalid_rows)
            else "FAIL"
        ),
        "rule_failure_counts": rule_failure_counts
    }

    with summary_file.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=2)

    print(f"Input rows: {input_count}")
    print(f"Valid rows: {len(valid_rows)}")
    print(f"Invalid rows: {len(invalid_rows)}")
    print(
        "Reconciliation: "
        f"{summary['reconciliation_status']}"
    )

    return summary


if __name__ == "__main__":
    validate_customers(
        "data/incoming/customers_day05.csv",
        "config/state_mapping.json",
        "data/quality/day05"
    )