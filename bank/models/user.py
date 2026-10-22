"""User models shared by customers and employees."""

from dataclasses import dataclass


@dataclass
class User:
    """Store a person's basic contact information."""

    first_name: str
    last_name: str
    email: str | None = None
    user_id: int | None = None

    def __post_init__(self) -> None:
        """Check the user's name and email."""
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        if not self.first_name or not self.last_name:
            raise ValueError("First and last name are required.")
        if self.email is not None:
            self.email = self.email.strip()
            if not self.email:
                raise ValueError("Email cannot be empty.")

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"