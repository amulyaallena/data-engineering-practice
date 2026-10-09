import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.validate_customer_quality import validate_customers


class TestCustomerQuality(unittest.TestCase):

    def create_state_mapping(self, path):
        mapping = {
            "oh": "OH",
            "ohio": "OH",
            "tx": "TX",
            "texas": "TX",
            "ny": "NY",
            "new york": "NY",
            "or": "OR",
            "oregon": "OR"
        }

        with path.open("w", encoding="utf-8") as file:
            json.dump(mapping, file)


    def run_validation(self, rows):
        temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(temp_dir.name)

        input_file = temp_path / "customers.csv"
        state_mapping = temp_path / "state_mapping.json"
        output_dir = temp_path / "output"

        self.create_state_mapping(state_mapping)

        with input_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
                "customer_id",
                "customer_name",
                "email",
                "state",
                "updated_at"
            ])

            writer.writerows(rows)

        summary = validate_customers(
            input_file,
            state_mapping,
            output_dir
        )

        return temp_dir, output_dir, summary


    def test_valid_customer(self):
        rows = [
            [
                "001",
                "John Smith",
                "john@example.com",
                "OH",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["valid_count"], 1)
        self.assertEqual(summary["invalid_count"], 0)

        temp_dir.cleanup()


    def test_blank_customer_id(self):
        rows = [
            [
                "",
                "John Smith",
                "john@example.com",
                "OH",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["invalid_count"], 1)
        self.assertEqual(
            summary["rule_failure_counts"]["MISSING_CUSTOMER_ID"],
            1
        )

        temp_dir.cleanup()


    def test_whitespace_only_name(self):
        rows = [
            [
                "001",
                "   ",
                "john@example.com",
                "OH",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["invalid_count"], 1)
        self.assertEqual(
            summary["rule_failure_counts"]["BLANK_CUSTOMER_NAME"],
            1
        )

        temp_dir.cleanup()


    def test_invalid_email(self):
        rows = [
            [
                "001",
                "John Smith",
                "johnexample.com",
                "OH",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["invalid_count"], 1)
        self.assertEqual(
            summary["rule_failure_counts"]["INVALID_EMAIL"],
            1
        )

        temp_dir.cleanup()


    def test_valid_mixed_case_email(self):
        rows = [
            [
                "001",
                "John Smith",
                "JOHN.SMITH@EXAMPLE.COM",
                "OH",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["valid_count"], 1)

        temp_dir.cleanup()


    def test_state_mapping_accepts_case_and_spaces(self):
        rows = [
            [
                "001",
                "John Smith",
                "john@example.com",
                "  Ohio  ",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["valid_count"], 1)

        temp_dir.cleanup()


    def test_invalid_state(self):
        rows = [
            [
                "001",
                "John Smith",
                "john@example.com",
                "CA",
                "2026-10-01T10:00:00Z"
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["invalid_count"], 1)
        self.assertEqual(
            summary["rule_failure_counts"]["INVALID_STATE"],
            1
        )

        temp_dir.cleanup()


    def test_missing_timestamp(self):
        rows = [
            [
                "001",
                "John Smith",
                "john@example.com",
                "OH",
                ""
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["invalid_count"], 1)
        self.assertEqual(
            summary["rule_failure_counts"]["MISSING_UPDATED_AT"],
            1
        )

        temp_dir.cleanup()


    def test_multiple_failures_on_one_row(self):
        rows = [
            [
                "",
                "   ",
                "bademail",
                "CA",
                ""
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["invalid_count"], 1)

        self.assertEqual(
            summary["rule_failure_counts"]["MISSING_CUSTOMER_ID"],
            1
        )

        self.assertEqual(
            summary["rule_failure_counts"]["BLANK_CUSTOMER_NAME"],
            1
        )

        self.assertEqual(
            summary["rule_failure_counts"]["INVALID_EMAIL"],
            1
        )

        self.assertEqual(
            summary["rule_failure_counts"]["INVALID_STATE"],
            1
        )

        self.assertEqual(
            summary["rule_failure_counts"]["MISSING_UPDATED_AT"],
            1
        )

        temp_dir.cleanup()


    def test_reconciliation(self):
        rows = [
            [
                "001",
                "John Smith",
                "john@example.com",
                "OH",
                "2026-10-01T10:00:00Z"
            ],
            [
                "",
                "Bad Customer",
                "bademail",
                "CA",
                ""
            ]
        ]

        temp_dir, output_dir, summary = self.run_validation(rows)

        self.assertEqual(summary["input_count"], 2)
        self.assertEqual(
            summary["input_count"],
            summary["valid_count"] + summary["invalid_count"]
        )
        self.assertEqual(
            summary["reconciliation_status"],
            "PASS"
        )

        temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()