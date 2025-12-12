
class Order:
    def __init__(self, order_id, side, qty):
        self.order_id = order_id
        self.side = side
        self.qty = qty

    def __str__(self):
        raise NotImplementedError