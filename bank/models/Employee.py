"""Employee model."""

from dataclasses import dataclass
from typing import Literal

from bank.models.user import User


@dataclass
class Employee(User):
    """Represent a bank employee."""

    role: Literal["employee"] = "employee"
