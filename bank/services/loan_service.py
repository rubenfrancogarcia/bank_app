"""Business operations for account-linked loans."""

from decimal import Decimal

from bank.models.account import Account
from bank.models.loan import Loan
from bank.repositories.account_repository import AccountRepository
from bank.repositories.loan_repository import LoanRepository
from bank.utils.bank_exception import BankException


class LoanService:
    """Apply loan rules and coordinate account payments."""

    def __init__(
        self,
        loans: LoanRepository,
        accounts: AccountRepository,
    ) -> None:
        """Create the service with loan and account repositories."""
        if loans.connection is not accounts.connection:
            raise ValueError(
                "Loans and accounts must share a database connection."
            )
        self._loans = loans
        self._accounts = accounts

    def create_loan(
        self,
        account_id: int,
        principal: Decimal,
        annual_rate: Decimal,
        term_months: int,
    ) -> Loan:
        """Create a loan and deposit its principal into the linked account."""
        with self._loans.connection:
            account = self._get_account(account_id)
            loan = Loan(
                user_id=account.user_id,
                account_id=account_id,
                principal=principal,
                annual_rate=annual_rate,
                term_months=term_months,
            )
            account.deposit(loan.principal)
            self._accounts.save(account)
            return self._loans.create(loan)

    def get_loan(self, product_id: int) -> Loan:
        """Return a loan or raise an error if it is missing."""
        loan = self._loans.get(product_id)
        if loan is None:
            raise BankException(f"Loan {product_id} was not found.")
        return loan

    def list_loans(self) -> list[Loan]:
        """Return all stored loans."""
        return self._loans.list_all()

    def pay(self, product_id: int, amount: Decimal) -> Loan:
        """Apply a loan payment from its linked account."""
        with self._loans.connection:
            loan = self.get_loan(product_id)
            account = self._get_account(loan.account_id)
            loan.pay(amount)
            account.withdraw(amount)
            self._loans.save(loan)
            self._accounts.save(account)
            return loan

    def _get_account(self, account_id: int) -> Account:
        """Return the linked account or raise an error if it is missing."""
        account = self._accounts.get(account_id)
        if account is None:
            raise BankException(f"Account {account_id} was not found.")
        return account
