"""Business operations for user records."""

from dataclasses import dataclass

from bank.models.account import Account
from bank.models.credit_card import CreditCard
from bank.models.loan import Loan
from bank.models.user import User
from bank.repositories.account_repository import AccountRepository
from bank.repositories.credit_card_repository import CreditCardRepository
from bank.repositories.loan_repository import LoanRepository
from bank.repositories.user_repository import UserRepository
from bank.utils.bank_exception import BankException


@dataclass
class UserDetails:
    """Collect a user and their linked banking records."""

    user: User
    accounts: list[Account]
    credit_cards: list[CreditCard]
    loans: list[Loan]


class UserService:
    """Manage user-related operations."""

    def __init__(
        self,
        repository: UserRepository,
        accounts: AccountRepository,
        credit_cards: CreditCardRepository,
        loans: LoanRepository,
    ) -> None:
        """Create the service with user and product repositories."""
        repositories = (accounts, credit_cards, loans)
        if any(
            item.connection is not repository.connection
            for item in repositories
        ):
            raise ValueError("User data must share a database connection.")
        self._repository = repository
        self._accounts = accounts
        self._credit_cards = credit_cards
        self._loans = loans

    def create_user(
        self, first_name: str, last_name: str, email: str | None = None
    ) -> User:
        """Create and store a user."""
        with self._repository.connection:
            return self._repository.create(
                User(first_name=first_name, last_name=last_name, email=email)
            )

    def get_user(self, user_id: int) -> User:
        """Return a user or raise an error if missing."""
        user = self._repository.get(user_id)
        if user is None:
            raise BankException(f"User {user_id} was not found.")
        return user

    def list_users(self) -> list[User]:
        """Return all stored users."""
        return self._repository.list_all()

    def get_user_details(self, user_id: int) -> UserDetails:
        """Return a user and all accounts, cards, and loans they own."""
        user = self.get_user(user_id)
        return UserDetails(
            user=user,
            accounts=self._accounts.list_for_user(user_id),
            credit_cards=self._credit_cards.list_for_user(user_id),
            loans=self._loans.list_for_user(user_id),
        )