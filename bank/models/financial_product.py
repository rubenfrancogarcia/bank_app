"""Shared identity for account-linked financial products."""

from dataclasses import dataclass


@dataclass(kw_only=True)
class FinancialProduct:
    """Identify a financial product and its owner."""

    user_id: int
    product_id: int | None = None

    def __post_init__(self) -> None:
        """Check that a product has a valid user ID."""
        if self.user_id <= 0:
            raise ValueError("User ID must be greater than zero.")
