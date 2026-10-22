"""SQLite connection and schema setup."""

import os
import sqlite3
from pathlib import Path


def connect() -> sqlite3.Connection:
    """Open the configured SQLite database."""
    database_path = Path(os.environ.get("BANK_DB_PATH", "bank.db"))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(database_path)


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create missing tables and migrate old account records."""
    schema_path = Path(__file__).with_name("schema.sql")
    schema = schema_path.read_text(encoding="utf-8")

    with connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)
        _add_user_links(connection)


def _add_user_links(connection: sqlite3.Connection) -> None:
    """Add user IDs to databases created before users were stored."""
    account_columns = _column_names(connection, "accounts")
    if "user_id" not in account_columns:
        connection.execute(
            "ALTER TABLE accounts ADD COLUMN user_id "
            "INTEGER REFERENCES users(id)"
        )

    old_accounts = connection.execute(
        "SELECT id, owner_name FROM accounts WHERE user_id IS NULL"
    ).fetchall()
    for account_id, owner_name in old_accounts:
        name_parts = owner_name.strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else "Unknown"
        last_name = name_parts[1] if len(name_parts) > 1 else "User"
        cursor = connection.execute(
            """
            INSERT INTO users (first_name, last_name)
            VALUES (?, ?)
            """,
            (first_name, last_name),
        )
        if cursor.lastrowid is None:
            raise RuntimeError(
                "SQLite did not return a user ID during migration."
            )
        connection.execute(
            "UPDATE accounts SET user_id = ? WHERE id = ?",
            (cursor.lastrowid, account_id),
        )

    for table in ("credit_cards", "loans"):
        columns = _column_names(connection, table)
        if "user_id" not in columns:
            add_column_sql = (
                f"ALTER TABLE {table} "
                "ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )
            connection.execute(
                add_column_sql
            )
        connection.execute(
            f"""
            UPDATE {table} AS product
            SET user_id = (
                SELECT user_id
                FROM accounts
                WHERE accounts.id = product.account_id
            )
            WHERE user_id IS NULL
            """
        )


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    """Return the column names in a table."""
    return {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }