from .order import Order 
from .stop_order import StopOrder


class StopMarketOrder(StopOrder):
    def __init__(
            self, 
            order_id: str, 
            side: str, 
            stop_price: float, 
            qty: int, 
            user_id: str, 
            timestamp: str
    ):
        super().__init__(order_id, side, stop_price, qty, user_id, timestamp)

    @property
    def order_type(self) -> str:
        return "stop-market"
    
    @property
    def underlying_order_type(self) -> str: 
        return "market"

    def __str__(self):
        return f"[ID {self.order_id}] STOP-LIMIT (Trigger: {self.stop_price}, {self.side.upper()} {self.qty}"