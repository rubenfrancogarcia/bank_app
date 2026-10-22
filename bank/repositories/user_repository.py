"""SQLite storage operations for users."""

import sqlite3

from bank.models.user import User


class UserRepository:
    """Load and save users in SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Create a repository using an open database connection."""
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the repository's database connection."""
        return self._connection

    def create(self, user: User) -> User:
        """Insert a user and assign its database ID."""
        cursor = self._connection.execute(
            """
            INSERT INTO users (first_name, last_name, email)
            VALUES (?, ?, ?)
            """,
            (user.first_name, user.last_name, user.email),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return a user ID.")
        user.user_id = cursor.lastrowid
        return user

    def get(self, user_id: int) -> User | None:
        """Return a user by ID, or None if it does not exist."""
        row = self._connection.execute(
            """
            SELECT id, first_name, last_name, email
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[User]:
        """Return all users in ID order."""
        rows = self._connection.execute(
            """
            SELECT id, first_name, last_name, email
            FROM users
            ORDER BY id
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: tuple[int, str, str, str | None]) -> User:
        """Build a user from a database row."""
        user_id, first_name, last_name, email = row
        return User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
