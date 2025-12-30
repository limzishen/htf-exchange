from .stop_order import StopOrder


class StopLimitOrder(StopOrder):
    def __init__(
        self,
        order_id: str,
        side: str,
        stop_price: float,
        price: float,
        qty: int,
        user_id: str,
        timestamp: str,
    ):
        super().__init__(order_id, side, stop_price, qty, user_id, timestamp)
        self.price = price

    @property
    def order_type(self) -> str:
        return "stop-limit"

    @property
    def underlying_order_type(self) -> str:
        return "limit"

    def __str__(self) -> str:
        return f"[ID {self.order_id}] STOP-LIMIT (Trigger: {self.stop_price}, Limit: {self.price}) {self.side.upper()} {self.qty}"
