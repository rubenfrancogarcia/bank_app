"""Business operations for bank accounts."""

from decimal import Decimal

from bank.models.account import Account
from bank.repositories.account_repository import AccountRepository
from bank.repositories.user_repository import UserRepository
from bank.utils.bank_exception import BankException


class AccountService:
    """Apply account rules and coordinate account storage."""

    def __init__(
        self,
        repository: AccountRepository,
        users: UserRepository,
    ) -> None:
        """Create the service with account and user repositories."""
        if repository.connection is not users.connection:
            raise ValueError(
                "Accounts and users must share a database connection."
            )
        self._repository = repository
        self._users = users

    def create_account(
        self, user_id: int, account_type: str = "checking"
    ) -> Account:
        """Create an account for an existing user."""
        with self._repository.connection:
            user = self._users.get(user_id)
            if user is None:
                raise BankException(f"User {user_id} was not found.")
            return self._repository.create(
                Account(
                    owner_name=user.full_name,
                    user_id=user_id,
                    account_type=account_type,
                )
            )

    def get_account(self, account_id: int) -> Account:
        """Return an account or raise an error if it is missing."""
        account = self._repository.get(account_id)
        if account is None:
            raise BankException(f"Account {account_id} was not found.")
        return account

    def list_accounts(self) -> list[Account]:
        """Return all stored accounts."""
        return self._repository.list_all()

    def deposit(self, account_id: int, amount: Decimal) -> Account:
        """Deposit money and save the updated account."""
        with self._repository.connection:
            account = self.get_account(account_id)
            account.deposit(amount)
            self._repository.save(account)
            return account

    def withdraw(self, account_id: int, amount: Decimal) -> Account:
        """Withdraw money and save the updated account."""
        with self._repository.connection:
            account = self.get_account(account_id)
            account.withdraw(amount)
            self._repository.save(account)
            return account