from dataclasses import dataclass
from .user_action import UserAction

@dataclass(frozen=True)
class RegisterUserAction(UserAction):
    user_balance: float

    def __str__(self):
        parent_str = super().__str__()
        return f"{parent_str} | Current Balance: {self.user_balance}"