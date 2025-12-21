from .order import Order 
from .stop_order import StopOrder

class StopLimitOrder(StopOrder):
    def __init__(self, order_id: str, side: str, stop_price: float, limit_price: float, qty: int, user_id: str, timestamp: str):
        super().__init__(order_id, side, stop_price, qty, user_id, timestamp)
        self.order_type = "stop-limit"
        self.limit_price = limit_price

    def __str__(self):
        return f"[ID {self.order_id}] STOP-LIMIT (Trigger: {self.stop_price}, Limit: {self.limit_price}) {self.side.upper()} {self.qty}"