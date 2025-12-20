from dataclasses import dataclass
from .user_action import UserAction

@dataclass(frozen=True)
class CashInAction(UserAction):
    amount_added: float
    curr_balance: float

    def __str__(self):
        parent_str = super().__str__()
        return f"{parent_str}| Added: {self.amount_added} | Current Balance: {self.curr_balance}"