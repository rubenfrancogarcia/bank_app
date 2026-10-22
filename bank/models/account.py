"""Bank account model and money amount validation."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from bank.utils.bank_exception import BankException


def normalize_amount(amount: Decimal | int | float | str) -> Decimal:
    """Return a valid monetary amount rounded to cents."""
    try:
        value = Decimal(str(amount))
    except InvalidOperation as error:
        raise ValueError("Amount must be a valid number.") from error

    if not value.is_finite():
        raise ValueError("Amount must be a finite number.")
    if value != value.quantize(Decimal("0.01")):
        raise ValueError("Amounts may have at most two decimal places.")
    return value.quantize(Decimal("0.01"))


@dataclass
class Account:
    """Represent a checking or savings account."""

    owner_name: str
    user_id: int
    account_type: str = "checking"
    account_id: int | None = None
    balance: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def __post_init__(self) -> None:
        """Validate account details after construction."""
        self.owner_name = self.owner_name.strip()
        if not self.owner_name:
            raise ValueError("Owner name cannot be empty.")
        if self.user_id <= 0:
            raise ValueError("User ID must be greater than zero.")
        if self.account_type not in {"checking", "savings"}:
            raise ValueError("Account type must be checking or savings.")
        self.balance = normalize_amount(self.balance)
        if self.balance < 0:
            raise ValueError("Balance cannot be negative.")

    def deposit(self, amount: Decimal | int | float | str) -> None:
        """Add a positive amount to the account."""
        amount = normalize_amount(amount)
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        self.balance += amount

    def withdraw(self, amount: Decimal | int | float | str) -> None:
        """Remove a positive amount if the balance covers it."""
        amount = normalize_amount(amount)
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > self.balance:
            raise BankException("Insufficient funds.")
        self.balance -= amount
