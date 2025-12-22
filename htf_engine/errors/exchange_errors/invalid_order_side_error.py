from .invalid_order_error import InvalidOrderError


class InvalidOrderSideError(InvalidOrderError):
    error_code = "INVALID_ORDER_TYPE"

    def __init__(self, order_side: str):
        self.order_side = order_side
        super().__init__()

    def default_message(self) -> str:
        return self.header_string() + f"Invalid order side {self.order_side} received. Must be 'buy' or 'sell'."
    