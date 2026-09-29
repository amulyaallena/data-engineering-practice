import csv
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timezone


def flatten_orders(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename="reports/orders_ingestion.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # Preserve original file in Bronze
    original_copy = output_dir / input_path.name
    shutil.copy2(input_path, original_copy)

    items_output = output_dir / "orders_items_flattened.csv"
    headers_output = output_dir / "orders_header_audit.csv"
    errors_output = output_dir / "orders_errors.csv"

    ingestion_timestamp = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    item_rows = []
    header_rows = []
    error_rows = []

    source_line_count = 0
    expected_item_count = 0

    with input_path.open("r", encoding="utf-8") as file:

        for line_number, line in enumerate(file, start=1):
            source_line_count += 1

            try:
                order = json.loads(line)

            except json.JSONDecodeError as error:
                error_rows.append({
                    "source_line_number": line_number,
                    "reason": "Malformed JSON",
                    "details": str(error),
                    "raw_line": line.strip()
                })
                continue

            order_id = order.get("order_id")
            customer = order.get("customer")

            # Reject missing required fields
            if not order_id:
                error_rows.append({
                    "source_line_number": line_number,
                    "reason": "Missing order_id",
                    "details": "",
                    "raw_line": line.strip()
                })
                continue

            if not customer or not customer.get("customer_id"):
                error_rows.append({
                    "source_line_number": line_number,
                    "reason": "Missing customer or customer_id",
                    "details": "",
                    "raw_line": line.strip()
                })
                continue

            items = order.get("items", [])
            shipping = order.get("shipping", {})

            # Accepted order header
            header_rows.append({
                "order_id": order_id,
                "customer_id": customer.get("customer_id", ""),
                "item_count": len(items),
                "source_line_number": line_number,
                "ingestion_timestamp": ingestion_timestamp,
                "run_id": run_id
            })

            expected_item_count += len(items)

            # Flatten one row per item
            for item_index, item in enumerate(items, start=1):

                item_rows.append({
                    "order_id": order_id,
                    "customer_id": customer.get("customer_id", ""),
                    "item_index": item_index,
                    "product_id": item.get("product_id", ""),
                    "quantity": item.get("quantity", ""),
                    "price": item.get("price", ""),
                    "shipping_city": shipping.get("city", ""),
                    "shipping_state": shipping.get("state", ""),
                    "shipping_zip": shipping.get("zip", ""),
                    "source_file_name": input_path.name,
                    "source_line_number": line_number,
                    "ingestion_timestamp": ingestion_timestamp,
                    "run_id": run_id
                })

    # Write flattened item output
    with items_output.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "order_id",
            "customer_id",
            "item_index",
            "product_id",
            "quantity",
            "price",
            "shipping_city",
            "shipping_state",
            "shipping_zip",
            "source_file_name",
            "source_line_number",
            "ingestion_timestamp",
            "run_id"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(item_rows)

    # Write accepted order header audit
    with headers_output.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "order_id",
            "customer_id",
            "item_count",
            "source_line_number",
            "ingestion_timestamp",
            "run_id"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(header_rows)

    # Write rejected rows
    with errors_output.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "source_line_number",
            "reason",
            "details",
            "raw_line"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(error_rows)

    actual_item_count = len(item_rows)

    item_reconciliation = (
        "PASS"
        if expected_item_count == actual_item_count
        else "FAIL"
    )

    line_reconciliation = (
        "PASS"
        if source_line_count == len(header_rows) + len(error_rows)
        else "FAIL"
    )

    logging.info(f"Source lines: {source_line_count}")
    logging.info(f"Accepted order headers: {len(header_rows)}")
    logging.info(f"Rejected lines: {len(error_rows)}")
    logging.info(f"Expected item rows: {expected_item_count}")
    logging.info(f"Actual item rows: {actual_item_count}")
    logging.info(f"Item reconciliation: {item_reconciliation}")
    logging.info(f"Line reconciliation: {line_reconciliation}")

    print(f"Source lines: {source_line_count}")
    print(f"Accepted order headers: {len(header_rows)}")
    print(f"Rejected lines: {len(error_rows)}")
    print(f"Expected item rows: {expected_item_count}")
    print(f"Actual item rows: {actual_item_count}")
    print(f"Item reconciliation: {item_reconciliation}")
    print(f"Line reconciliation: {line_reconciliation}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(
            "Usage: python src/flatten_orders.py "
            "<input_file> <output_dir>"
        )
        sys.exit(1)

    flatten_orders(sys.argv[1], sys.argv[2])