from contextlib import closing

from bank.repositories.database import connect


def main():
    with closing(connect()) as connection:
        connection.execute("SELECT 1")

    print("Bank CLI")
    print("Type 'help' for available commands or 'exit' to quit.")

    while True:
        try:
            command = input("> ").strip().lower()
        except EOFError:
            print()
            break

        if command in {"exit", "quit"}:
            break
        if command == "help":
            print("Available commands: help, exit")
        elif command:
            print(f"Unknown command: {command}. Type 'help' for available commands.")