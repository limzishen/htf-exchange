from .order import Order


class FOKOrder(Order):
    def __init__(self, order_id: str, side: str, price: float, qty: int, user_id: str, timestamp: str):
        super().__init__(order_id, side, qty, user_id, timestamp)
        self.order_type = "fok"
        self.price = price

    def __str__(self):
        return f"[ID {self.order_id}] {self.side.upper()} {self.price} x {self.qty} at {self.timestamp}"