from .order import Order


class LimitOrder(Order):
    def __init__(self, order_id, side, price, qty):
        super().__init__(order_id, side, qty)
        self.price = price

    def __str__(self):
        return f"[ID {self.order_id}] {self.side.upper()} {self.price} x {self.qty}"