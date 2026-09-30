import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.extract_customers import extract_customers


class TestCustomerExtract(unittest.TestCase):

    def create_test_db(self, db_path):
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE customer_source (
                customer_id TEXT,
                customer_name TEXT,
                email TEXT,
                state TEXT,
                updated_at TEXT,
                status TEXT
            )
        """)

        rows = [
            ("001", "John Smith", "john@example.com", "NY", "2026-09-30T10:00:00Z", "active"),
            ("002", "Mary Jones", "mary@example.com", "NJ", "2026-09-30T10:05:00Z", "inactive"),
            ("003", "Bob Brown", "bob@example.com", "CA", "2026-09-30T10:10:00Z", "active"),
            ("004", "Lisa Hall", "lisa@example.com", "TX", "2026-09-30T10:15:00Z", None),
            ("003", "Bob Brown Duplicate", "bob2@example.com", "CA", "2026-09-30T10:20:00Z", "active")
        ]

        cursor.executemany("""
            INSERT INTO customer_source
            (customer_id, customer_name, email, state, updated_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rows)

        connection.commit()
        connection.close()


    def test_active_only_extraction(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            db_path = temp_path / "test.db"
            output_dir = temp_path / "extracts"

            self.create_test_db(db_path)

            rows = extract_customers(
                db_path,
                "active",
                output_dir
            )

            self.assertEqual(len(rows), 3)

            for row in rows:
                self.assertEqual(row[5], "active")


    def test_zero_matches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            db_path = temp_path / "test.db"
            output_dir = temp_path / "extracts"

            self.create_test_db(db_path)

            rows = extract_customers(
                db_path,
                "suspended",
                output_dir
            )

            self.assertEqual(len(rows), 0)


    def test_duplicate_business_keys_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            db_path = temp_path / "test.db"
            output_dir = temp_path / "extracts"

            self.create_test_db(db_path)

            rows = extract_customers(
                db_path,
                "active",
                output_dir
            )

            customer_ids = [row[0] for row in rows]

            self.assertEqual(customer_ids.count("003"), 2)


    def test_null_status_not_returned_for_active(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            db_path = temp_path / "test.db"
            output_dir = temp_path / "extracts"

            self.create_test_db(db_path)

            rows = extract_customers(
                db_path,
                "active",
                output_dir
            )

            customer_ids = [row[0] for row in rows]

            self.assertNotIn("004", customer_ids)


    def test_unavailable_database_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            missing_db = temp_path / "does_not_exist.db"
            output_dir = temp_path / "extracts"

            with self.assertRaises(FileNotFoundError):
                extract_customers(
                    missing_db,
                    "active",
                    output_dir
                )


if __name__ == "__main__":
    unittest.main()