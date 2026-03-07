"""Helper script to execute the SQL migration file against the configured
MySQL server.  You can call this from the command line:

    python -m database.run_migration

or directly with your interpreter.  It reads `app.config` for the
connection parameters, creates the database if necessary, and runs every
statement inside `migration.sql`.

The same SQL file (`migration.sql`) can be opened in MySQL Workbench and
executed manually if preferred.
"""
import os
from pathlib import Path

import mysql.connector

# import the project's configuration values
from app import config


def run_migration():
    base = Path(__file__).parent
    migration_file = base / "migration.sql"

    if not migration_file.exists():
        raise FileNotFoundError(f"migration file not found: {migration_file}")

    with migration_file.open("r", encoding="utf-8") as f:
        sql_text = f.read()

    # split on semicolon; simple but workable for the current file
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    # configure connection; separate host and port if provided
    host = config.HOST
    port = None
    if ":" in host:
        host, port = host.split(":", 1)
    connection_args = {
        "host": host,
        "user": config.USER,
        "password": config.PASSWORD,
    }
    if port is not None:
        try:
            connection_args["port"] = int(port)
        except ValueError:
            pass

    # Establish connection; do not specify database so we can create it
    conn = mysql.connector.connect(**connection_args)
    cursor = conn.cursor()

    try:
        for stmt in statements:
            cursor.execute(stmt)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    print("Migration executed successfully.")


if __name__ == "__main__":
    run_migration()
