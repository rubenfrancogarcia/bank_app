# Bank Project

## Project Overview

In this project, you will create a simpler version of a banking system. You will
design the banking system using Python object-oriented programming (OOP)
techniques.

Your bank model should include entities for:

- Customers
- Accounts
- Employees
- Services such as loans and credit cards

Each entity should have distinct properties. Decide which properties are
relevant for each entity. For example, customer records could include a
customer's first name, last name, and address. Accounts could include an
account type (checking or savings), deposit and withdrawal operations, and a
balance. Add getter and setter methods where they are needed.

## Data Storage

Choose how to store project data. Options include a SQL database, CSV, JSON, or
another format. Persistent storage is recommended. Keeping data only in memory
is not recommended because information may be lost if the program encounters
an error.

## Command-Line Application

The application runs from the command line:

```text
python main.py
```

It stores account records in SQLite (`bank.db` by default). The tables are
initialized from [`schema.sql`](./bank/repositories/schema.sql). Set
`BANK_DB_PATH` to use another database file. The CLI supports:

- `user-create "Alex" "Example" "alex@example.com"`
- `user-list`
- `user-info <user_id>` (show the profile, accounts, cards, and loans)
- `create <user_id> <checking|savings>`
- `create checking "Alex Example"` (creates a user and account together)
- `list`
- `balance <account_id>`
- `deposit <account_id> <amount>`
- `withdraw <account_id> <amount>`
- `card-create <account_id> <credit_limit>`
- `card-list`, `card-balance <card_id>`
- `card-charge <card_id> <amount>`, `card-pay <card_id> <amount>`
- `loan-create <account_id> <principal> <annual_rate_percent> <term_months>`
- `loan-list`, `loan-balance <loan_id>`, `loan-pay <loan_id> <amount>`
- `help` and `exit`

Users own accounts, and accounts fund their linked cards and loans. Both
product models extend `FinancialProduct`, which provides a `user_id` and
`product_id`; each retains its own card or loan behavior and database table.
Card charges cannot exceed the credit limit; card payments debit the linked
account. Creating a loan deposits its principal into the linked account, and
loan payments debit it.
Loan payments apply one monthly interest period per payment, using the APR and
remaining term to calculate the installment. This command-line app does not
track calendar due dates or late fees.

When the app opens an older database, it adds user links and creates user
records from existing account owner names. Those migrated users have no email
address.

Amounts must be positive and have no more than two decimal places. Withdrawals
and product payments cannot exceed the linked account's balance. Customer
Employee records are not yet implemented.

## Object-Oriented Example

The following is a simple example of a bank account class:

```python
#!/usr/bin/env python


class BankAccount:
    def __init__(self):
        self.balance = 0

    def withdraw(self, amount):
        self.balance -= amount
        return self.balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance
```

## Project Requirements

A successful project will:

- Follow PEP 8 style guidelines.
- Be readable and well documented, with inline comments and docstrings for
  functions and classes.
- Implement logging that prints messages on screen and writes errors and
  warnings to a file in the project's `logs` folder.
- Handle exceptions gracefully.
- Include a `README.md` file explaining how the program works.

## Deliverables

1. A UML diagram of the classes.
2. Code pushed to GitHub in the project structure outlined by the assignment,
   along with a Markdown README explaining the design and how the program works.
