import csv
import tempfile
import unittest
from pathlib import Path

from src.ingest_customers import ingest_file


class TestCustomerIngestion(unittest.TestCase):

    def test_valid_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_file = temp_path / "valid.csv"
            output_dir = temp_path / "bronze"

            input_file.write_text(
                "customer_id,customer_name,email,state,updated_at\n"
                "001,John Smith,john@example.com,NY,2026-09-28\n"
                "002,Mary Jones,mary@example.com,NJ,2026-09-28\n"
            )

            ingest_file(input_file, output_dir)

            bronze_file = output_dir / "valid_bronze.csv"

            self.assertTrue(bronze_file.exists())

            with bronze_file.open("r", newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)


    def test_header_only_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_file = temp_path / "header_only.csv"
            output_dir = temp_path / "bronze"

            input_file.write_text(
                "customer_id,customer_name,email,state,updated_at\n"
            )

            ingest_file(input_file, output_dir)

            bronze_file = output_dir / "header_only_bronze.csv"

            with bronze_file.open("r", newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 0)


    def test_empty_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_file = temp_path / "empty.csv"
            output_dir = temp_path / "bronze"

            input_file.write_text("")

            with self.assertRaises(ValueError):
                ingest_file(input_file, output_dir)


    def test_missing_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_file = temp_path / "missing.csv"
            output_dir = temp_path / "bronze"

            with self.assertRaises(FileNotFoundError):
                ingest_file(input_file, output_dir)


    def test_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_file = temp_path / "duplicates.csv"
            output_dir = temp_path / "bronze"

            input_file.write_text(
                "customer_id,customer_name,email,state,updated_at\n"
                "001,John Smith,john@example.com,NY,2026-09-28\n"
                "002,Mary Jones,mary@example.com,NJ,2026-09-28\n"
                "002,Mary Jones,mary@example.com,NJ,2026-09-28\n"
            )

            ingest_file(input_file, output_dir)

            bronze_file = output_dir / "duplicates_bronze.csv"

            with bronze_file.open("r", newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()