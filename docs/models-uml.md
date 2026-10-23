# Models UML

```mermaid
classDiagram
    class User {
        +int user_id
        +str first_name
        +str last_name
        +str email
        +str role
        +str full_name
    }

    class Customer
    class Employee

    class Account {
        +int account_id
        +int user_id
        +str owner_name
        +str account_type
        +Decimal balance
        +deposit(amount)
        +withdraw(amount)
    }

    class FinancialProduct {
        +int product_id
        +int user_id
    }

    class CreditCard {
        +int account_id
        +Decimal credit_limit
        +Decimal balance
        +Decimal available_credit
        +charge(amount)
        +pay(amount)
    }

    class Loan {
        +int account_id
        +Decimal principal
        +Decimal annual_rate
        +int term_months
        +Decimal balance
        +int payments_made
        +int remaining_months
        +Decimal monthly_payment
        +pay(amount)
    }

    User <|-- Customer
    User <|-- Employee
    FinancialProduct <|-- CreditCard
    FinancialProduct <|-- Loan
    User "1" --> "0..*" Account : owns
    User "1" --> "0..*" FinancialProduct : owns
    Account "1" --> "0..*" FinancialProduct : funds
```

`Customer` and `Employee` inherit the user fields and set the user's role.
Product IDs are assigned independently by the credit card and loan tables, so
the same numeric ID can identify one of each.
