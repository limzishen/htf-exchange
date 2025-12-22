from htf_engine.errors.exchange_errors.invalid_order_side_error import InvalidOrderSideError


class Order:
    VALID_SIDES = {"buy", "sell"}
    
    def __init__(
            self,
            order_id: str,
            side: str,
            qty: int,
            user_id: str,
            timestamp: str
    ):
        if side not in self.VALID_SIDES:
            raise InvalidOrderSideError(side)

        if qty <= 0:
            raise ValueError("Order quantity must be > 0.")
    
        self.order_id = order_id
        self.side = side
        self.qty = qty
        self.user_id = user_id
        self.timestamp = timestamp
        self.stop = False
    
    @property
    def order_type(self) -> str:
        raise NotImplementedError("Subclasses must define `order_type`")

    def is_buy_order(self) -> bool:
        return self.side == "buy"

    def is_sell_order(self) -> bool:
        return self.side == "sell"
    
    def is_stop(self): 
        return self.stop

    def __str__(self) -> str:
        raise NotImplementedError
    