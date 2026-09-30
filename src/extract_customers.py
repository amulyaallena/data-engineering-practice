import argparse
import csv
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def extract_customers(db_path, requested_status, output_root):
    db_path = Path(db_path)
    output_root = Path(output_root)

    logging.basicConfig(
        filename="reports/customer_extract.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    if not db_path.exists():
        message = f"Database unavailable: {db_path}"
        logging.error(message)
        raise FileNotFoundError(message)

    # Open existing DB without silently creating a new one
    db_uri = f"file:{db_path.resolve()}?mode=rw"

    try:
        connection = sqlite3.connect(db_uri, uri=True)
    except sqlite3.Error as error:
        logging.error(f"Database connection failed: {error}")
        raise

    query = """
        SELECT
            customer_id,
            customer_name,
            email,
            state,
            updated_at,
            status
        FROM customer_source
        WHERE status = ?
    """

    try:
        cursor = connection.cursor()

        cursor.execute(query, (requested_status,))

        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description]

    except sqlite3.Error as error:
        logging.error(f"Query failed: {error}")
        connection.close()
        raise

    connection.close()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    run_folder = output_root / run_id
    run_folder.mkdir(parents=True, exist_ok=True)

    output_file = run_folder / "customer_extract.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    logging.info(f"Requested status: {requested_status}")
    logging.info(f"Extracted count: {len(rows)}")
    logging.info(f"Output file: {output_file}")

    print(f"Requested status: {requested_status}")
    print(f"Extracted count: {len(rows)}")
    print(f"Output file: {output_file}")

    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to existing SQLite database"
    )

    parser.add_argument(
        "--status",
        required=True,
        help="Customer status to extract"
    )

    parser.add_argument(
        "--output-dir",
        default="data/extracts",
        help="Root folder for extracts"
    )

    args = parser.parse_args()

    extract_customers(
        args.db_path,
        args.status,
        args.output_dir
    )