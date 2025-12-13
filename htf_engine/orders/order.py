class Order:
    VALID_SIDES = {"buy", "sell"}
    
    def __init__(self, order_id, side, qty, user_id, timestamp):
        if side not in self.VALID_SIDES:
            raise ValueError(f"Invalid order side '{side}'. Must be 'buy' or 'sell'.")

        if qty <= 0:
            raise ValueError("Order quantity must be > 0.")
    
        self.order_id = order_id
        self.side = side
        self.qty = qty
        self.user_id = user_id
        self.timestamp = timestamp

    def is_buy_order(self):
        return self.side == "buy"

    def is_sell_order(self):
        return self.side == "sell"

    def __str__(self):
        raise NotImplementedError