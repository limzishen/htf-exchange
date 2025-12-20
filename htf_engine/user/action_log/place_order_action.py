from dataclasses import dataclass
from .user_action import UserAction

@dataclass(frozen=True)
class PlaceOrderAction(UserAction):
    instrument_id: str
    order_type: str
    side: str
    quantity: int
    price: float

    def __str__(self):
        parent_str = super().__str__()
        return f"{parent_str} | {self.order_type} | {self.side} | {self.quantity} | {self.price} for {self.instrument_id}"