from .order import Order

class StopOrder(Order):
    def __init__(
            self, 
            order_id: str, 
            side: str, 
            stop_price: float, 
            qty: int, 
            user_id: str, 
            timestamp: str
    ):
        super().__init__(order_id, side, qty, user_id, timestamp)
        self.stop_price = stop_price
        self.stop = True
    
    @property
    def underlying_order_type(self) -> str: 
        raise NotImplementedError("Subclasses must define `underlying_order_type`")
    
    def __str__(self):
        return f"[ID {self.order_id}] {self.side.upper()} {self.stop_price} x {self.qty} at {self.timestamp}"

