"""Loan model with monthly interest calculations."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from bank.models.account import normalize_amount
from bank.models.financial_product import FinancialProduct


@dataclass
class Loan(FinancialProduct):
    """Represent a fixed-term loan linked to a bank account."""

    account_id: int
    principal: Decimal
    annual_rate: Decimal
    term_months: int
    balance: Decimal | None = None
    payments_made: int = 0

    def __post_init__(self) -> None:
        """Validate loan details and initialize its balance."""
        super().__post_init__()
        self.principal = normalize_amount(self.principal)
        self.annual_rate = Decimal(str(self.annual_rate))
        if (
            not self.annual_rate.is_finite()
            or not 0 <= self.annual_rate <= 100
        ):
            raise ValueError("Annual rate must be between 0 and 100 percent.")
        if self.annual_rate != self.annual_rate.quantize(Decimal("0.01")):
            raise ValueError(
                "Annual rate may have at most two decimal places."
            )
        if self.principal <= 0:
            raise ValueError("Loan principal must be greater than zero.")
        if self.term_months <= 0:
            raise ValueError("Loan term must be greater than zero months.")
        if self.payments_made < 0:
            raise ValueError("Payments made cannot be negative.")
        if self.balance is None:
            self.balance = self.principal
        else:
            self.balance = normalize_amount(self.balance)
        if self.balance < 0 or self.balance > self.principal:
            raise ValueError(
                "Loan balance must be between zero and the principal."
            )

    @property
    def remaining_months(self) -> int:
        """Return the number of installments left."""
        return max(self.term_months - self.payments_made, 1)

    @property
    def monthly_payment(self) -> Decimal:
        """Calculate the current estimated monthly payment."""
        assert self.balance is not None
        monthly_rate = self.annual_rate / Decimal("1200")
        if not monthly_rate:
            payment = self.balance / self.remaining_months
        else:
            factor = (Decimal("1") + monthly_rate) ** self.remaining_months
            payment = self.balance * monthly_rate * factor / (factor - 1)
        return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def pay(self, amount: Decimal | int | float | str) -> Decimal:
        """Apply one installment and return its interest amount."""
        assert self.balance is not None
        amount = normalize_amount(amount)
        if amount <= 0:
            raise ValueError("Loan payment must be greater than zero.")

        monthly_interest = (
            self.balance * self.annual_rate / Decimal("1200")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        amount_due = min(self.balance + monthly_interest, self.monthly_payment)
        if amount < amount_due:
            raise ValueError(
                f"Payment must be at least {amount_due:.2f} "
                "for this installment."
            )
        if amount > self.balance + monthly_interest:
            raise ValueError(
                "Payment exceeds the remaining loan balance and interest."
            )

        self.balance = max(
            Decimal("0.00"), self.balance + monthly_interest - amount
        )
        self.payments_made += 1
        return monthly_interest