"""Business operations for linked credit cards."""

from decimal import Decimal

from bank.models.account import Account
from bank.models.credit_card import CreditCard
from bank.repositories.account_repository import AccountRepository
from bank.repositories.credit_card_repository import CreditCardRepository
from bank.utils.bank_exception import BankException


class CreditService:
    """Apply credit card rules and coordinate account payments."""

    def __init__(
        self,
        cards: CreditCardRepository,
        accounts: AccountRepository,
    ) -> None:
        """Create the service with card and account repositories."""
        if cards.connection is not accounts.connection:
            raise ValueError(
                "Credit cards and accounts must share a database connection."
            )
        self._cards = cards
        self._accounts = accounts

    def create_card(
        self, account_id: int, credit_limit: Decimal
    ) -> CreditCard:
        """Create a card linked to an existing account."""
        with self._cards.connection:
            account = self._get_account(account_id)
            return self._cards.create(
                CreditCard(
                    user_id=account.user_id,
                    account_id=account_id,
                    credit_limit=credit_limit,
                )
            )

    def get_card(self, product_id: int) -> CreditCard:
        """Return a card or raise an error if it is missing."""
        card = self._cards.get(product_id)
        if card is None:
            raise BankException(f"Credit card {product_id} was not found.")
        return card

    def list_cards(self) -> list[CreditCard]:
        """Return all stored cards."""
        return self._cards.list_all()

    def charge(self, product_id: int, amount: Decimal) -> CreditCard:
        """Charge a card and save its new balance."""
        with self._cards.connection:
            card = self.get_card(product_id)
            card.charge(amount)
            self._cards.save(card)
            return card

    def pay(self, product_id: int, amount: Decimal) -> CreditCard:
        """Pay a card balance from its linked account."""
        with self._cards.connection:
            card = self.get_card(product_id)
            account = self._get_account(card.account_id)
            card.pay(amount)
            account.withdraw(amount)
            self._cards.save(card)
            self._accounts.save(account)
            return card

    def _get_account(self, account_id: int) -> Account:
        """Return the linked account or raise an error if it is missing."""
        account = self._accounts.get(account_id)
        if account is None:
            raise BankException(f"Account {account_id} was not found.")
        return account
