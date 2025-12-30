from dataclasses import dataclass
from typing import Optional

from .user_action import UserAction


@dataclass(frozen=True)
class RecordStopTrigger(UserAction):
    instrument_id: str
    order_type: str
    underlying_order_type: str
    side: str
    quantity: int
    stop_price: float
    price: Optional[float]

    def __str__(self) -> str:
        parent_str = super().__str__()

        return f"{self.underlying_order_type} TRIGGERED AT {self.stop_price} | {parent_str}"
