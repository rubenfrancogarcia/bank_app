"""SQLite storage operations for loans."""

import sqlite3
from decimal import Decimal

from bank.models.loan import Loan


class LoanRepository:
    """Load and save loans in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Create a repository using an open database connection."""
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the repository's database connection."""
        return self._connection

    def create(self, loan: Loan) -> Loan:
        """Insert a loan and assign its database ID."""
        assert loan.balance is not None
        cursor = self._connection.execute(
            """
            INSERT INTO loans (
                user_id, account_id, original_principal_cents,
                balance_cents, annual_rate_basis_points, term_months,
                payments_made
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                loan.user_id,
                loan.account_id,
                self._to_cents(loan.principal),
                self._to_cents(loan.balance),
                int(loan.annual_rate * 100),
                loan.term_months,
                loan.payments_made,
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return a loan ID.")
        loan.product_id = cursor.lastrowid
        return loan

    def get(self, product_id: int) -> Loan | None:
        """Return a loan by ID, or None if it does not exist."""
        row = self._connection.execute(
            """
            SELECT id, user_id, account_id, original_principal_cents,
                   balance_cents, annual_rate_basis_points, term_months,
                   payments_made
            FROM loans
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[Loan]:
        """Return all loans in ID order."""
        rows = self._connection.execute(
            """
            SELECT id, user_id, account_id, original_principal_cents,
                   balance_cents, annual_rate_basis_points, term_months,
                   payments_made
            FROM loans
            ORDER BY id
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_for_user(self, user_id: int) -> list[Loan]:
        """Return loans owned by one user."""
        rows = self._connection.execute(
            """
            SELECT id, user_id, account_id, original_principal_cents,
                   balance_cents, annual_rate_basis_points, term_months,
                   payments_made
            FROM loans
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, loan: Loan) -> None:
        """Update a stored loan balance and payment count."""
        if loan.product_id is None:
            raise ValueError("Cannot save a loan without an ID.")
        assert loan.balance is not None
        cursor = self._connection.execute(
            """
            UPDATE loans
            SET balance_cents = ?, payments_made = ?
            WHERE id = ?
            """,
            (
                self._to_cents(loan.balance),
                loan.payments_made,
                loan.product_id,
            ),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Loan {loan.product_id} does not exist.")

    @staticmethod
    def _to_cents(amount: Decimal) -> int:
        """Convert a monetary amount to integer cents."""
        return int(amount * 100)

    @staticmethod
    def _from_row(row: tuple[int, int, int, int, int, int, int, int]) -> Loan:
        """Build a loan from a database row."""
        (
            product_id,
            user_id,
            account_id,
            principal_cents,
            balance_cents,
            rate,
            term,
            payments,
        ) = row
        return Loan(
            product_id=product_id,
            user_id=user_id,
            account_id=account_id,
            principal=Decimal(principal_cents) / 100,
            balance=Decimal(balance_cents) / 100,
            annual_rate=Decimal(rate) / 100,
            term_months=term,
            payments_made=payments,
        )
