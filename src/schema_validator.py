import csv
import json
from datetime import datetime
from pathlib import Path


def load_schema(schema_path):
    schema_path = Path(schema_path)

    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_valid_utc_timestamp(value):
    if value == "":
        return True

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_schema(csv_path, schema_path, strict=False):
    csv_path = Path(csv_path)

    schema = load_schema(schema_path)

    required_columns = list(schema["columns"].keys())

    report = {
        "status": "PASS",
        "missing_columns": [],
        "extra_columns": [],
        "duplicate_headers": [],
        "parse_failures": []
    }

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)

        try:
            headers = next(reader)
        except StopIteration:
            report["status"] = "FAIL"
            report["missing_columns"] = required_columns
            return report

        # Duplicate headers
        for header in headers:
            if headers.count(header) > 1 and header not in report["duplicate_headers"]:
                report["duplicate_headers"].append(header)

        # Missing columns
        for column in required_columns:
            if column not in headers:
                report["missing_columns"].append(column)

        # Extra columns
        for column in headers:
            if column not in required_columns:
                report["extra_columns"].append(column)

        # Critical header failures
        if report["missing_columns"] or report["duplicate_headers"]:
            report["status"] = "FAIL"

        if strict and report["extra_columns"]:
            report["status"] = "FAIL"

    if report["status"] == "FAIL":
        return report

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=2):

            updated_at = row.get("updated_at", "")

            if not is_valid_utc_timestamp(updated_at):
                report["parse_failures"].append({
                    "row": row_number,
                    "column": "updated_at",
                    "value": updated_at,
                    "reason": "Invalid UTC timestamp"
                })

    if report["parse_failures"]:
        report["status"] = "FAIL"

    return report