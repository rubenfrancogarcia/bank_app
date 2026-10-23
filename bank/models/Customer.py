"""Customer model."""

from dataclasses import dataclass
from typing import Literal

from bank.models.user import User


@dataclass
class Customer(User):
    """Represent a bank customer."""

    role: Literal["customer"] = "customer"
