import sqlite3
from pathlib import Path


DB_PATH = Path("data/customer_source.db")


def setup_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS customer_source")

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

        # duplicate business key on purpose
        ("003", "Bob Brown Duplicate", "bob2@example.com", "CA", "2026-09-30T10:20:00Z", "active")
    ]

    cursor.executemany("""
        INSERT INTO customer_source
        (customer_id, customer_name, email, state, updated_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)

    connection.commit()
    connection.close()

    print(f"Database created at: {DB_PATH}")


if __name__ == "__main__":
    setup_database()