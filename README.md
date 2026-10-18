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

The final project should be structured as outlined in the assignment and be
executable from the command line. It should accept user input and return
results in the command line.

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
