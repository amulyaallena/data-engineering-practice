import csv
import re
from datetime import datetime, timezone
from pathlib import Path


STATE_MAPPING = {
    "oh": "OH",
    "ohio": "OH",
    "tx": "TX",
    "texas": "TX",
    "ny": "NY",
    "new york": "NY",
    "or": "OR",
    "oregon": "OR"
}


def clean_name(value):
    if value is None:
        return ""

    # trim outside spaces and collapse repeated spaces
    return " ".join(value.strip().split())


def clean_email(value):
    if value is None:
        return ""

    return value.strip().lower()


def clean_state(value):
    if value is None:
        return None

    normalized = value.strip().lower()

    return STATE_MAPPING.get(normalized)


def clean_timestamp(value):
    if value is None or value.strip() == "":
        return None

    value = value.strip()

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        # If timestamp has no timezone,
        # treat it as UTC for this exercise
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        utc_value = parsed.astimezone(timezone.utc)

        return utc_value.strftime("%Y-%m-%dT%H:%M:%SZ")

    except ValueError:
        return None


def clean_phone(value):
    if value is None or value.strip() == "":
        return ""

    digits = re.sub(r"\D", "", value)

    if len(digits) == 10:
        return "+1" + digits

    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits

    return None


def transform_customers(input_file, output_dir):
    input_file = Path(input_file)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    silver_rows = []
    invalid_rows = []

    with input_file.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            failures = []

            raw_name = row.get("customer_name", "")
            raw_email = row.get("email", "")
            raw_state = row.get("state", "")
            raw_timestamp = row.get("updated_at", "")
            raw_phone = row.get("phone", "")

            cleaned_name = clean_name(raw_name)
            cleaned_email = clean_email(raw_email)
            cleaned_state = clean_state(raw_state)
            cleaned_timestamp = clean_timestamp(raw_timestamp)
            cleaned_phone = clean_phone(raw_phone)

            if cleaned_state is None:
                failures.append("INVALID_STATE")

            if cleaned_timestamp is None:
                failures.append("INVALID_TIMESTAMP")

            if raw_phone.strip() != "" and cleaned_phone is None:
                failures.append("INVALID_PHONE")

            output_row = {
                "customer_id": row.get("customer_id", ""),

                "raw_customer_name": raw_name,
                "customer_name": cleaned_name,

                "raw_email": raw_email,
                "email": cleaned_email,

                "raw_state": raw_state,
                "state": cleaned_state or "",

                "raw_updated_at": raw_timestamp,
                "updated_at": cleaned_timestamp or "",

                "raw_phone": raw_phone,
                "phone": cleaned_phone or "",

                "source_file_name": row.get(
                    "source_file_name",
                    input_file.name
                ),

                "source_row_number": row.get(
                    "source_row_number",
                    ""
                )
            }

            if failures:
                output_row["transformation_status"] = "INVALID"
                output_row["rejection_reason"] = ";".join(failures)

                invalid_rows.append(output_row)

            else:
                output_row["transformation_status"] = "VALID"
                output_row["rejection_reason"] = ""

                silver_rows.append(output_row)

    fieldnames = [
        "customer_id",
        "raw_customer_name",
        "customer_name",
        "raw_email",
        "email",
        "raw_state",
        "state",
        "raw_updated_at",
        "updated_at",
        "raw_phone",
        "phone",
        "source_file_name",
        "source_row_number",
        "transformation_status",
        "rejection_reason"
    ]

    silver_file = output_dir / "standardized_customers.csv"
    invalid_file = output_dir / "transformation_errors.csv"

    with silver_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(silver_rows)

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

    print(f"Input rows: {len(silver_rows) + len(invalid_rows)}")
    print(f"Silver rows: {len(silver_rows)}")
    print(f"Transformation failures: {len(invalid_rows)}")

    return silver_rows, invalid_rows


if __name__ == "__main__":
    transform_customers(
        "data/incoming/customers_day07.csv",
        "data/silver/day07"
    )