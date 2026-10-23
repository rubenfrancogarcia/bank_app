BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'customer'
        CHECK (role IN ('customer', 'employee'))
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_name TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    account_type TEXT NOT NULL
        CHECK (account_type IN ('checking', 'savings')),
    balance_cents INTEGER NOT NULL DEFAULT 0
        CHECK (balance_cents >= 0)
);

CREATE TABLE IF NOT EXISTS credit_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    credit_limit_cents INTEGER NOT NULL CHECK (credit_limit_cents > 0),
    balance_cents INTEGER NOT NULL DEFAULT 0
        CHECK (balance_cents >= 0 AND balance_cents <= credit_limit_cents)
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    original_principal_cents INTEGER NOT NULL CHECK (original_principal_cents > 0),
    balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0),
    annual_rate_basis_points INTEGER NOT NULL CHECK (annual_rate_basis_points >= 0),
    term_months INTEGER NOT NULL CHECK (term_months > 0),
    payments_made INTEGER NOT NULL DEFAULT 0 CHECK (payments_made >= 0)
);

COMMIT;
