from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent
CSV_FILE = PROJECT_DIR / "SGJobData_cleaned.csv"
DB_FILE = PROJECT_DIR / "SGJobData_cleaned.db"
TABLE_NAME = "sg_job_data_cleaned"


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Cleaned CSV not found: {CSV_FILE}")

    print(f"Reading cleaned CSV: {CSV_FILE}")
    print(f"Creating DuckDB file: {DB_FILE}")

    con = duckdb.connect(str(DB_FILE))

    con.sql(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    con.sql(
        f"""
        CREATE TABLE {TABLE_NAME} AS
        SELECT *
        FROM read_csv_auto('{CSV_FILE.as_posix()}', HEADER=TRUE)
        """
    )

    row_count = con.sql(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    columns = con.sql(f"DESCRIBE {TABLE_NAME}").fetchall()

    con.close()

    print(f"Created database: {DB_FILE.name}")
    print(f"Created table: {TABLE_NAME}")
    print(f"Rows loaded: {row_count:,}")
    print("Columns:")
    for column in columns:
        print(f"  {column[0]}: {column[1]}")


if __name__ == "__main__":
    main()
