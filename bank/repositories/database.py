import os
import sqlite3
from pathlib import Path


def connect() -> sqlite3.Connection:
    database_path = Path(os.environ.get("BANK_DB_PATH", "bank.db"))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(database_path)