import unittest

from src.schema_validator import validate_schema


SCHEMA = "config/customer_schema.json"


class TestSchemaValidator(unittest.TestCase):

    def test_valid_file(self):
        report = validate_schema(
            "tests/fixtures/valid.csv",
            SCHEMA
        )

        self.assertEqual(report["status"], "PASS")


    def test_missing_column(self):
        report = validate_schema(
            "tests/fixtures/missing_column.csv",
            SCHEMA
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("state", report["missing_columns"])


    def test_misspelled_column(self):
        report = validate_schema(
            "tests/fixtures/misspelled_column.csv",
            SCHEMA
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("state", report["missing_columns"])
        self.assertIn("stte", report["extra_columns"])


    def test_extra_column(self):
        report = validate_schema(
            "tests/fixtures/extra_column.csv",
            SCHEMA
        )

        self.assertEqual(report["status"], "PASS")
        self.assertIn("phone", report["extra_columns"])


    def test_invalid_timestamp(self):
        report = validate_schema(
            "tests/fixtures/invalid_timestamp.csv",
            SCHEMA
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(len(report["parse_failures"]) > 0)


    def test_leading_zero_id(self):
        report = validate_schema(
            "tests/fixtures/leading_zero_id.csv",
            SCHEMA
        )

        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()