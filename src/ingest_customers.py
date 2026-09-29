from pathlib import Path
import csv
import shutil
import logging
from datetime import datetime, timezone


def ingest_file(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    logging.basicConfig(
        filename="reports/ingestion.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    original_copy = output_dir / input_path.name
    shutil.copy2(input_path, original_copy)

    bronze_file = output_dir / f"{input_path.stem}_bronze.csv"

    ingestion_timestamp = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        if reader.fieldnames is None:
            logging.error("Missing CSV header")
            raise ValueError("Missing CSV header")

        rows = list(reader)

    fieldnames = reader.fieldnames + [
        "ingestion_timestamp",
        "source_file_name",
        "source_row_number",
        "run_id"
    ]

    with bronze_file.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(rows, start=1):
            row["ingestion_timestamp"] = ingestion_timestamp
            row["source_file_name"] = input_path.name
            row["source_row_number"] = str(index)
            row["run_id"] = run_id
            writer.writerow(row)

    source_count = len(rows)

    with bronze_file.open("r", newline="", encoding="utf-8") as check_file:
        bronze_count = sum(1 for _ in csv.DictReader(check_file))

    status = "PASS" if source_count == bronze_count else "FAIL"

    logging.info(f"Source row count: {source_count}")
    logging.info(f"Bronze row count: {bronze_count}")
    logging.info(f"Count validation: {status}")

    print(f"Source rows: {source_count}")
    print(f"Bronze rows: {bronze_count}")
    print(f"Validation: {status}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python src/ingest_customers.py <input_file> <output_dir>")
        sys.exit(1)

    ingest_file(sys.argv[1], sys.argv[2])