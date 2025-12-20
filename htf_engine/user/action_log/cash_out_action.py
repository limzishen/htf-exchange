from dataclasses import dataclass
from .user_action import UserAction

@dataclass(frozen=True)
class CashOutAction(UserAction):
    amount_removed: float
    curr_balance: float

    def __str__(self):
        parent_str = super().__str__()
        return f"{parent_str} | Removed: {self.amount_removed} | Current Balance: {self.curr_balance}"