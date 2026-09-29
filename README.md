# Data Engineering Practice — Day 1

## Project Overview

This project implements a basic batch ingestion process for a daily customer CSV file.

The goal is to read the source CSV, preserve the original data, add ingestion metadata, write the result to the Bronze layer, validate row counts, and log the result.

## Project Structure

```text
data-engineering-practice/
├── src/
│   └── ingest_customers.py
├── tests/
│   └── test_ingestion.py
├── data/
│   ├── incoming/
│   │   └── customers_day01.csv
│   ├── bronze/
│   ├── silver/
│   └── quarantine/
├── reports/
│   └── ingestion.log
├── docs/
└── README.md
```

## Input File

The source file is:

```text
data/incoming/customers_day01.csv
```

Expected source columns:

```text
customer_id
customer_name
email
state
updated_at
```

The sample file contains 12 fictional customer records, including duplicate customer IDs and extra whitespace.

## Ingestion Process

The Python ingestion script:

```text
src/ingest_customers
