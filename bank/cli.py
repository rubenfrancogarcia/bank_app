"""Command-line interface for the bank application."""

import shlex
from contextlib import closing
from decimal import Decimal, InvalidOperation

from bank.models.account import Account
from bank.models.credit_card import CreditCard
from bank.models.loan import Loan
from bank.repositories.account_repository import AccountRepository
from bank.repositories.credit_card_repository import CreditCardRepository
from bank.repositories.database import connect, initialize_database
from bank.repositories.loan_repository import LoanRepository
from bank.repositories.user_repository import UserRepository
from bank.services.account_service import AccountService
from bank.services.credit_service import CreditService
from bank.services.employee_service import EmployeeService
from bank.services.loan_service import LoanService
from bank.services.user_service import UserService
from bank.utils.bank_exception import BankException


def _format_account(account: Account) -> str:
    return (
        f"#{account.account_id} {account.owner_name} "
        f"({account.account_type}) balance: {account.balance:.2f}"
    )


def _format_card(card: CreditCard) -> str:
    return (
        f"Card #{card.product_id} (user #{card.user_id}, "
        f"account #{card.account_id}) "
        f"balance: {card.balance:.2f}, "
        f"available: {card.available_credit:.2f}, "
        f"limit: {card.credit_limit:.2f}"
    )


def _format_loan(loan: Loan) -> str:
    return (
        f"Loan #{loan.product_id} (user #{loan.user_id}, "
        f"account #{loan.account_id}) "
        f"balance: {loan.balance:.2f}, APR: {loan.annual_rate:.2f}%, "
        f"monthly payment: {loan.monthly_payment:.2f}, "
        f"term: {loan.term_months} months"
    )


def _parse_account_id(value: str) -> int:
    try:
        account_id = int(value)
    except ValueError as error:
        raise ValueError("Account ID must be a whole number.") from error
    if account_id <= 0:
        raise ValueError("Account ID must be greater than zero.")
    return account_id


def _parse_positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{label} must be a whole number.") from error
    if parsed <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return parsed


def _parse_amount(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Amount must be a valid number.") from error
    if not amount.is_finite():
        raise ValueError("Amount must be a finite number.")
    return amount


def _run_command(
    service: AccountService,
    credit_service: CreditService,
    loan_service: LoanService,
    user_service: UserService,
    employee_service: EmployeeService,
    command: str,
) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError as error:
        print(f"Invalid command: {error}")
        return True

    if not parts:
        return True

    action, *arguments = parts
    action = action.lower()
    if action in {"exit", "quit"}:
        return False
    if action == "help":
        print(
            "Commands:\n"
            '  create <checking|savings> "<owner name>"\n'
            "  create <user_id> <checking|savings>\n"
            '  user-create "<first name>" "<last name>" "<email>"\n'
            "  user-list\n"
            "  user-info <user_id>\n"
            '  employee-create "<first name>" "<last name>" "<email>"\n'
            "  employee-list\n"
            "  list\n"
            "  balance <account_id>\n"
            "  deposit <account_id> <amount>\n"
            "  withdraw <account_id> <amount>\n"
            "  card-create <account_id> <credit_limit>\n"
            "  card-list\n"
            "  card-balance <card_id>\n"
            "  card-charge <card_id> <amount>\n"
            "  card-pay <card_id> <amount>\n"
            "  loan-create <account_id> <principal> "
            "<annual_rate_percent> <term_months>\n"
            "  loan-list\n"
            "  loan-balance <loan_id>\n"
            "  loan-pay <loan_id> <amount>\n"
            "  help\n"
            "  exit"
        )
        return True

    try:
        if action == "user-create" and len(arguments) == 3:
            user = user_service.create_user(*arguments)
            if user.user_id is None:
                raise RuntimeError("Created user is missing its database ID.")
            print(f"Created user #{user.user_id}: {user.full_name}")
        elif action == "user-list" and not arguments:
            users = user_service.list_users()
            if not users:
                print("No users found.")
            else:
                for user in users:
                    email = user.email or "no email"
                    print(
                        f"#{user.user_id} {user.full_name} "
                        f"[{user.role}] ({email})"
                    )
        elif action == "employee-create" and len(arguments) == 3:
            employee = employee_service.create_employee(*arguments)
            print(
                f"Created employee #{employee.user_id}: "
                f"{employee.full_name}"
            )
        elif action == "employee-list" and not arguments:
            employees = employee_service.list_employees()
            if not employees:
                print("No employees found.")
            else:
                for employee in employees:
                    email = employee.email or "no email"
                    print(
                        f"#{employee.user_id} "
                        f"{employee.full_name} ({email})"
                    )
        elif action == "user-info" and len(arguments) == 1:
            details = user_service.get_user_details(
                _parse_positive_int(arguments[0], "User ID")
            )
            user = details.user
            print(f"User #{user.user_id}: {user.full_name}")
            print(f"Email: {user.email or 'not provided'}")
            print(f"Role: {user.role}")

            print("Accounts:")
            if details.accounts:
                for account in details.accounts:
                    print(f"  {_format_account(account)}")
            else:
                print("  None")

            print("Credit cards:")
            if details.credit_cards:
                for card in details.credit_cards:
                    print(f"  {_format_card(card)}")
            else:
                print("  None")

            print("Loans:")
            if details.loans:
                for loan in details.loans:
                    print(f"  {_format_loan(loan)}")
            else:
                print("  None")
        elif action == "create" and len(arguments) == 2:
            if arguments[0].lower() in {"checking", "savings"}:
                name_parts = arguments[1].strip().split(maxsplit=1)
                if len(name_parts) < 2:
                    raise ValueError("Enter both a first and last name.")
                user = user_service.create_user(name_parts[0], name_parts[1])
                if user.user_id is None:
                    raise RuntimeError(
                        "Created user is missing its database ID."
                    )
                account = service.create_account(
                    user.user_id, arguments[0].lower()
                )
            else:
                account = service.create_account(
                    _parse_account_id(arguments[0]), arguments[1].lower()
                )
            print(f"Created account: {_format_account(account)}")
        elif action == "list" and not arguments:
            accounts = service.list_accounts()
            if not accounts:
                print("No accounts found.")
            else:
                for account in accounts:
                    print(_format_account(account))
        elif action == "balance" and len(arguments) == 1:
            account_id = _parse_account_id(arguments[0])
            print(_format_account(service.get_account(account_id)))
        elif action in {"deposit", "withdraw"} and len(arguments) == 2:
            account_id = _parse_account_id(arguments[0])
            amount = _parse_amount(arguments[1])
            if action == "deposit":
                account = service.deposit(account_id, amount)
                print(
                    f"Deposited {amount:.2f}. "
                    f"New balance: {account.balance:.2f}"
                )
            else:
                account = service.withdraw(account_id, amount)
                print(
                    f"Withdrew {amount:.2f}. "
                    f"New balance: {account.balance:.2f}"
                )
        elif action == "card-create" and len(arguments) == 2:
            card = credit_service.create_card(
                _parse_account_id(arguments[0]), _parse_amount(arguments[1])
            )
            print(f"Created {_format_card(card)}")
        elif action == "card-list" and not arguments:
            cards = credit_service.list_cards()
            if not cards:
                print("No credit cards found.")
            else:
                for card in cards:
                    print(_format_card(card))
        elif action == "card-balance" and len(arguments) == 1:
            product_id = _parse_positive_int(arguments[0], "Card ID")
            print(_format_card(credit_service.get_card(product_id)))
        elif action in {"card-charge", "card-pay"} and len(arguments) == 2:
            product_id = _parse_positive_int(arguments[0], "Card ID")
            amount = _parse_amount(arguments[1])
            if action == "card-charge":
                card = credit_service.charge(product_id, amount)
                print(f"Charged {amount:.2f}. {_format_card(card)}")
            else:
                card = credit_service.pay(product_id, amount)
                print(f"Paid {amount:.2f}. {_format_card(card)}")
        elif action == "loan-create" and len(arguments) == 4:
            term_months = _parse_positive_int(arguments[3], "Loan term")
            loan = loan_service.create_loan(
                _parse_account_id(arguments[0]),
                _parse_amount(arguments[1]),
                _parse_amount(arguments[2]),
                term_months,
            )
            print(f"Created {_format_loan(loan)}")
        elif action == "loan-list" and not arguments:
            loans = loan_service.list_loans()
            if not loans:
                print("No loans found.")
            else:
                for loan in loans:
                    print(_format_loan(loan))
        elif action == "loan-balance" and len(arguments) == 1:
            product_id = _parse_positive_int(arguments[0], "Loan ID")
            print(_format_loan(loan_service.get_loan(product_id)))
        elif action == "loan-pay" and len(arguments) == 2:
            loan = loan_service.pay(
                _parse_positive_int(arguments[0], "Loan ID"),
                _parse_amount(arguments[1]),
            )
            print(f"Payment recorded. {_format_loan(loan)}")
        else:
            print(
                "Invalid command or arguments. "
                "Type 'help' for available commands."
            )
    except (BankException, ValueError) as error:
        print(f"Error: {error}")

    return True


def main() -> None:
    """Start the command prompt and handle user commands."""
    with closing(connect()) as connection:
        initialize_database(connection)
        users = UserRepository(connection)
        employee_service = EmployeeService(users)
        accounts = AccountRepository(connection)
        cards = CreditCardRepository(connection)
        loans = LoanRepository(connection)
        user_service = UserService(users, accounts, cards, loans)
        service = AccountService(accounts, users)
        credit_service = CreditService(
            cards, accounts
        )
        loan_service = LoanService(loans, accounts)
        print("Bank CLI")
        print("Type 'help' for commands or 'exit' to quit.")

        while True:
            try:
                command = input("> ")
            except EOFError:
                print()
                break
            if not _run_command(
                service,
                credit_service,
                loan_service,
                user_service,
                employee_service,
                command,
            ):
                break