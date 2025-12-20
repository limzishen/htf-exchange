from dataclasses import dataclass
from .user_action import UserAction

@dataclass(frozen=True)
class CancelOrderAction(UserAction):
    order_id: str
    instrument_id: str

    def __str__(self):
        parent_str = super().__str__()
        return f"{parent_str}| Order Cancelled: {self.order_id} | Instrument ID: {self.instrument_id}"