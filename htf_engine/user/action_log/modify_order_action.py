from dataclasses import dataclass
from .user_action import UserAction

@dataclass(frozen=True)
class ModifyOrderAction(UserAction):
    order_id: str
    instrument_id: str
    new_qty: int
    new_price: float

    def __str__(self) -> str:
        parent_str = super().__str__()

        return f"{parent_str} | {self.order_id} | {self.instrument_id} | Modified to: {self.new_qty} | {self.new_price}"