"""SQLite storage operations for bank accounts."""

import sqlite3
from decimal import Decimal

from bank.models.account import Account


class AccountRepository:
    """Load and save accounts in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Create a repository using an open database connection."""
        self._connection = connection

    def create(self, account: Account) -> Account:
        """Insert an account and assign its database ID."""
        cursor = self._connection.execute(
            """
            INSERT INTO accounts (
                owner_name, user_id, account_type, balance_cents
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                account.owner_name,
                account.user_id,
                account.account_type,
                self._to_cents(account.balance),
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return an account ID.")
        account.account_id = cursor.lastrowid
        return account

    def get(self, account_id: int) -> Account | None:
        """Return an account by ID, or None if it does not exist."""
        row = self._connection.execute(
            """
            SELECT id, owner_name, user_id, account_type, balance_cents
            FROM accounts
            WHERE id = ?
            """,
            (account_id,),
        ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[Account]:
        """Return all accounts in ID order."""
        rows = self._connection.execute(
            """
            SELECT id, owner_name, user_id, account_type, balance_cents
            FROM accounts
            ORDER BY id
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_for_user(self, user_id: int) -> list[Account]:
        """Return accounts owned by one user."""
        rows = self._connection.execute(
            """
            SELECT id, owner_name, user_id, account_type, balance_cents
            FROM accounts
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, account: Account) -> None:
        """Update a stored account."""
        if account.account_id is None:
            raise ValueError("Cannot save an account without an ID.")
        cursor = self._connection.execute(
            """
            UPDATE accounts
            SET owner_name = ?, user_id = ?, account_type = ?,
                balance_cents = ?
            WHERE id = ?
            """,
            (
                account.owner_name,
                account.user_id,
                account.account_type,
                self._to_cents(account.balance),
                account.account_id,
            ),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Account {account.account_id} does not exist.")

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the repository's database connection."""
        return self._connection

    @staticmethod
    def _to_cents(amount: Decimal) -> int:
        """Convert a monetary amount to integer cents."""
        return int(amount * 100)

    @staticmethod
    def _from_row(row: tuple[int, str, int, str, int]) -> Account:
        """Build an account from a database row."""
        account_id, owner_name, user_id, account_type, balance_cents = row
        return Account(
            account_id=account_id,
            owner_name=owner_name,
            user_id=user_id,
            account_type=account_type,
            balance=Decimal(balance_cents) / 100,
        )