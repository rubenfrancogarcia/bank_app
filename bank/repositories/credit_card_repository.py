"""SQLite storage operations for credit cards."""

import sqlite3
from decimal import Decimal

from bank.models.credit_card import CreditCard


class CreditCardRepository:
    """Load and save credit cards in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Create a repository using an open database connection."""
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the repository's database connection."""
        return self._connection

    def create(self, card: CreditCard) -> CreditCard:
        """Insert a credit card and assign its database ID."""
        cursor = self._connection.execute(
            """
            INSERT INTO credit_cards (
                user_id, account_id, credit_limit_cents, balance_cents
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                card.user_id,
                card.account_id,
                self._to_cents(card.credit_limit),
                self._to_cents(card.balance),
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return a credit card ID.")
        card.product_id = cursor.lastrowid
        return card

    def get(self, product_id: int) -> CreditCard | None:
        """Return a card by ID, or None if it does not exist."""
        row = self._connection.execute(
            """
            SELECT id, user_id, account_id, credit_limit_cents, balance_cents
            FROM credit_cards
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[CreditCard]:
        """Return all cards in ID order."""
        rows = self._connection.execute(
            """
            SELECT id, user_id, account_id, credit_limit_cents, balance_cents
            FROM credit_cards
            ORDER BY id
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_for_user(self, user_id: int) -> list[CreditCard]:
        """Return cards owned by one user."""
        rows = self._connection.execute(
            """
            SELECT id, user_id, account_id, credit_limit_cents, balance_cents
            FROM credit_cards
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, card: CreditCard) -> None:
        """Update a stored card balance."""
        if card.product_id is None:
            raise ValueError("Cannot save a credit card without an ID.")
        cursor = self._connection.execute(
            """
            UPDATE credit_cards
            SET balance_cents = ?
            WHERE id = ?
            """,
            (self._to_cents(card.balance), card.product_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Credit card {card.product_id} does not exist.")

    @staticmethod
    def _to_cents(amount: Decimal) -> int:
        """Convert a monetary amount to integer cents."""
        return int(amount * 100)

    @staticmethod
    def _from_row(row: tuple[int, int, int, int, int]) -> CreditCard:
        """Build a credit card from a database row."""
        product_id, user_id, account_id, limit_cents, balance_cents = row
        return CreditCard(
            product_id=product_id,
            user_id=user_id,
            account_id=account_id,
            credit_limit=Decimal(limit_cents) / 100,
            balance=Decimal(balance_cents) / 100,
        )
