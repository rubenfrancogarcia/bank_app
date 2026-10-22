"""Credit card model."""

from dataclasses import dataclass
from decimal import Decimal

from bank.models.account import normalize_amount
from bank.models.financial_product import FinancialProduct


@dataclass
class CreditCard(FinancialProduct):
    """Represent a credit card linked to a bank account."""

    account_id: int
    credit_limit: Decimal
    balance: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        """Validate the card limit and balance."""
        super().__post_init__()
        self.credit_limit = normalize_amount(self.credit_limit)
        self.balance = normalize_amount(self.balance)
        if self.credit_limit <= 0:
            raise ValueError("Credit limit must be greater than zero.")
        if self.balance < 0 or self.balance > self.credit_limit:
            raise ValueError(
                "Card balance must be between zero and the credit limit."
            )

    @property
    def available_credit(self) -> Decimal:
        """Return the credit still available to spend."""
        return self.credit_limit - self.balance

    def charge(self, amount: Decimal | int | float | str) -> None:
        """Add a charge within the available credit."""
        amount = normalize_amount(amount)
        if amount <= 0:
            raise ValueError("Charge amount must be greater than zero.")
        if amount > self.available_credit:
            raise ValueError("Charge exceeds the available credit.")
        self.balance += amount

    def pay(self, amount: Decimal | int | float | str) -> None:
        """Reduce the card balance by a valid payment."""
        amount = normalize_amount(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        if amount > self.balance:
            raise ValueError("Payment cannot exceed the card balance.")
        self.balance -= amount
