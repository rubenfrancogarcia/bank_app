"""Tests for accounts, credit cards, loans, and the command-line app."""

import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from unittest.mock import patch

from bank.cli import main
from bank.models.account import Account
from bank.models.financial_product import FinancialProduct
from bank.models.user import User
from bank.repositories.account_repository import AccountRepository
from bank.repositories.credit_card_repository import CreditCardRepository
from bank.repositories.database import initialize_database
from bank.repositories.loan_repository import LoanRepository
from bank.repositories.user_repository import UserRepository
from bank.services.account_service import AccountService
from bank.services.credit_service import CreditService
from bank.services.loan_service import LoanService
from bank.services.user_service import UserService
from bank.utils.bank_exception import BankException


class AccountTests(unittest.TestCase):
    """Check the main banking workflows."""

    def setUp(self) -> None:
        """Create an in-memory database and services for each test."""
        self.connection = sqlite3.connect(":memory:")
        initialize_database(self.connection)
        self.users = UserRepository(self.connection)
        self.accounts = AccountRepository(self.connection)
        self.cards = CreditCardRepository(self.connection)
        self.loans = LoanRepository(self.connection)
        self.user_service = UserService(
            self.users, self.accounts, self.cards, self.loans
        )
        self.service = AccountService(self.accounts, self.users)
        self.credit_service = CreditService(
            self.cards, self.accounts
        )
        self.loan_service = LoanService(
            self.loans, self.accounts
        )

    def create_account(self, owner_name: str = "Alex Example") -> Account:
        """Create a user and checking account for a test."""
        first_name, last_name = owner_name.split(maxsplit=1)
        user = self.user_service.create_user(first_name, last_name)
        return self.service.create_account(user.user_id)

    def tearDown(self) -> None:
        """Close the in-memory database."""
        self.connection.close()

    def test_user_properties_can_be_updated(self) -> None:
        """Check user names and email use working properties."""
        user = User("Alex", "Example", "alex@example.com")

        user.first_name = "Alexandra"
        user.last_name = "Smith"
        user.email = "alexandra@example.com"

        self.assertEqual(user.first_name, "Alexandra")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.email, "alexandra@example.com")

    def test_products_share_user_and_product_ids(self) -> None:
        """Check loans and cards use the shared product identity."""
        account = self.create_account()
        card = self.credit_service.create_card(
            account.account_id, Decimal("50.00")
        )
        loan = self.loan_service.create_loan(
            account.account_id,
            Decimal("100.00"),
            Decimal("0.00"),
            10,
        )

        self.assertEqual(card.user_id, account.user_id)
        self.assertEqual(loan.user_id, account.user_id)
        self.assertIsInstance(card, FinancialProduct)
        self.assertIsInstance(loan, FinancialProduct)
        self.assertEqual(card.product_id, 1)
        self.assertEqual(loan.product_id, 1)
        self.assertEqual(
            self.service.get_account(account.account_id).user_id,
            account.user_id,
        )
        self.assertEqual(
            self.credit_service.get_card(card.product_id).user_id,
            account.user_id,
        )
        self.assertEqual(
            self.loan_service.get_loan(loan.product_id).user_id,
            account.user_id,
        )

    def test_user_details_include_only_the_users_records(self) -> None:
        """Show the user's accounts, cards, and loans without other users' data."""
        account = self.create_account()
        self.service.deposit(account.account_id, Decimal("100.00"))
        card = self.credit_service.create_card(
            account.account_id, Decimal("50.00")
        )
        loan = self.loan_service.create_loan(
            account.account_id, Decimal("100.00"), Decimal("0.00"), 10
        )
        other_account = self.create_account("Jamie Doe")
        self.credit_service.create_card(
            other_account.account_id, Decimal("20.00")
        )

        details = self.user_service.get_user_details(account.user_id)

        self.assertEqual(details.user.full_name, "Alex Example")
        self.assertEqual([item.account_id for item in details.accounts],
                         [account.account_id])
        self.assertEqual([item.product_id for item in details.credit_cards],
                         [card.product_id])
        self.assertEqual([item.product_id for item in details.loans],
                         [loan.product_id])

    def test_initializes_schema_with_foreign_keys_enabled(self) -> None:
        """Check that schema setup enables foreign-key enforcement."""
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1
        )
        user = self.user_service.create_user("Alex", "Example")
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO credit_cards (
                    user_id, account_id, credit_limit_cents
                )
                VALUES (?, ?, ?)
                """,
                (user.user_id, 999, 1000),
            )

    def test_migrates_existing_accounts_and_products_to_users(self) -> None:
        """Connect old account and product rows to generated users."""
        legacy = sqlite3.connect(":memory:")
        legacy.executescript(
            """
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                balance_cents INTEGER NOT NULL
            );
            CREATE TABLE credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                credit_limit_cents INTEGER NOT NULL,
                balance_cents INTEGER NOT NULL
            );
            CREATE TABLE loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                original_principal_cents INTEGER NOT NULL,
                balance_cents INTEGER NOT NULL,
                annual_rate_basis_points INTEGER NOT NULL,
                term_months INTEGER NOT NULL,
                payments_made INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO accounts
                (owner_name, account_type, balance_cents)
            VALUES ('Alex Example', 'checking', 2500);
            INSERT INTO credit_cards
                (account_id, credit_limit_cents, balance_cents)
            VALUES (1, 5000, 1000);
            INSERT INTO loans (
                account_id, original_principal_cents, balance_cents,
                annual_rate_basis_points, term_months
            )
            VALUES (1, 10000, 9000, 500, 12);
            """
        )

        initialize_database(legacy)

        account = AccountRepository(legacy).get(1)
        card = CreditCardRepository(legacy).get(1)
        loan = LoanRepository(legacy).get(1)
        user = UserRepository(legacy).get(account.user_id)

        self.assertEqual(user.full_name, "Alex Example")
        self.assertEqual(card.user_id, user.user_id)
        self.assertEqual(loan.user_id, user.user_id)
        legacy.close()

    def test_create_deposit_and_withdraw_account(self) -> None:
        """Check account creation and balance changes."""
        account = self.create_account()

        self.assertIsNotNone(account.account_id)
        self.assertEqual(account.balance, Decimal("0.00"))

        self.service.deposit(account.account_id, Decimal("25.50"))
        account = self.service.withdraw(account.account_id, Decimal("5.25"))

        self.assertEqual(account.balance, Decimal("20.25"))
        self.assertEqual(
            self.service.get_account(account.account_id).balance,
            Decimal("20.25"),
        )

    def test_rejects_nonpositive_deposit(self) -> None:
        """Check that deposits must be positive."""
        account = self.create_account()

        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.service.deposit(account.account_id, Decimal("0"))

    def test_rejects_withdrawal_that_exceeds_balance(self) -> None:
        """Check that accounts cannot be overdrawn."""
        account = self.create_account()

        with self.assertRaisesRegex(BankException, "Insufficient funds"):
            self.service.withdraw(account.account_id, Decimal("1.00"))

        self.assertEqual(
            self.service.get_account(account.account_id).balance,
            Decimal("0.00"),
        )

    def test_rejects_unsupported_account_type(self) -> None:
        """Check that only supported account types can be created."""
        user = self.user_service.create_user("Alex", "Example")
        with self.assertRaisesRegex(ValueError, "checking or savings"):
            self.service.create_account(user.user_id, "investment")

    def test_credit_card_charges_and_payments_are_persisted(self) -> None:
        """Check card charges and payments update stored balances."""
        account = self.create_account()
        self.service.deposit(account.account_id, Decimal("100.00"))
        card = self.credit_service.create_card(
            account.account_id, Decimal("50.00")
        )

        card = self.credit_service.charge(card.product_id, Decimal("30.00"))
        self.assertEqual(card.available_credit, Decimal("20.00"))
        card = self.credit_service.pay(card.product_id, Decimal("20.00"))

        self.assertEqual(card.balance, Decimal("10.00"))
        self.assertEqual(
            self.service.get_account(account.account_id).balance,
            Decimal("80.00"),
        )
        self.assertEqual(
            self.credit_service.get_card(card.product_id).balance,
            Decimal("10.00"),
        )

    def test_card_payment_is_atomic_when_funding_account_is_short(
        self,
    ) -> None:
        """Check failed card payments do not change the card balance."""
        account = self.create_account()
        card = self.credit_service.create_card(
            account.account_id, Decimal("50.00")
        )
        self.credit_service.charge(card.product_id, Decimal("20.00"))

        with self.assertRaisesRegex(BankException, "Insufficient funds"):
            self.credit_service.pay(card.product_id, Decimal("10.00"))

        self.assertEqual(
            self.credit_service.get_card(card.product_id).balance,
            Decimal("20.00"),
        )

    def test_loan_disbursal_and_apr_payment(self) -> None:
        """Check loan disbursal and monthly-interest payments."""
        account = self.create_account()
        loan = self.loan_service.create_loan(
            account.account_id,
            Decimal("1000.00"),
            Decimal("12.00"),
            12,
        )
        self.assertEqual(account.balance, Decimal("0.00"))
        self.assertEqual(
            self.service.get_account(account.account_id).balance,
            Decimal("1000.00"),
        )
        self.assertEqual(loan.monthly_payment, Decimal("88.85"))

        loan = self.loan_service.pay(loan.product_id, loan.monthly_payment)

        self.assertEqual(loan.balance, Decimal("921.15"))
        self.assertEqual(loan.payments_made, 1)
        self.assertEqual(
            self.loan_service.get_loan(loan.product_id).balance,
            Decimal("921.15"),
        )
        self.assertEqual(
            self.service.get_account(account.account_id).balance,
            Decimal("911.15"),
        )

    def test_loan_payment_is_atomic_when_funding_account_is_short(
        self,
    ) -> None:
        """Check failed loan payments leave balances unchanged."""
        account = self.create_account()
        loan = self.loan_service.create_loan(
            account.account_id,
            Decimal("100.00"),
            Decimal("0.00"),
            10,
        )
        self.service.withdraw(account.account_id, Decimal("100.00"))

        with self.assertRaisesRegex(BankException, "Insufficient funds"):
            self.loan_service.pay(loan.product_id, loan.monthly_payment)

        self.assertEqual(
            self.loan_service.get_loan(loan.product_id).balance,
            Decimal("100.00"),
        )
        self.assertEqual(
            self.service.get_account(account.account_id).balance,
            Decimal("0.00"),
        )

    def test_cli_supports_a_persistent_account_workflow(
        self,
    ) -> None:
        """Check the CLI can run a stored banking workflow."""
        with tempfile.TemporaryDirectory() as directory:
            database_path = os.path.join(directory, "bank.db")
            commands = [
                'user-create "Alex" "Example" "alex@example.com"',
                "create 1 checking",
                'create savings "Jamie Doe"',
                "deposit 1 10.50",
                "balance 1",
                "card-create 1 50.00",
                "card-charge 1 25.00",
                "card-pay 1 10.00",
                "loan-create 1 100.00 0.00 10",
                "loan-pay 1 10.00",
                "user-info 1",
                "exit",
            ]
            output = io.StringIO()
            with (
                patch.dict(os.environ, {"BANK_DB_PATH": database_path}),
                patch("builtins.input", side_effect=commands),
                redirect_stdout(output),
            ):
                main()

            self.assertIn(
                "Created account: #1 Alex Example", output.getvalue()
            )
            self.assertIn("Created user #1: Alex Example", output.getvalue())
            self.assertIn("Created account: #2 Jamie Doe", output.getvalue())
            self.assertIn("New balance: 10.50", output.getvalue())
            self.assertIn("balance: 10.50", output.getvalue())
            self.assertIn("Created Card #1", output.getvalue())
            self.assertIn("Paid 10.00. Card #1", output.getvalue())
            self.assertIn("Created Loan #1", output.getvalue())
            self.assertIn("balance: 90.00", output.getvalue())
            self.assertIn("Email: alex@example.com", output.getvalue())
            self.assertIn("Accounts:", output.getvalue())
            self.assertIn("Credit cards:", output.getvalue())
            self.assertIn("Loans:", output.getvalue())
            self.assertIn("Loan #1 (user #1, account #1)", output.getvalue())


if __name__ == "__main__":
    unittest.main()
