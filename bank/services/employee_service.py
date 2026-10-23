"""Business operations for bank employees."""

from bank.models.employee import Employee
from bank.repositories.user_repository import UserRepository


class EmployeeService:
    """Create and list employee records."""

    def __init__(self, repository: UserRepository) -> None:
        """Create the service with a user repository."""
        self._repository = repository

    def create_employee(
        self, first_name: str, last_name: str, email: str | None = None
    ) -> Employee:
        """Create and store an employee."""
        with self._repository.connection:
            employee = Employee(
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            self._repository.create(employee)
            return employee

    def list_employees(self) -> list[Employee]:
        """Return all stored employees."""
        users = self._repository.list_by_role("employee")
        return [user for user in users if isinstance(user, Employee)]
