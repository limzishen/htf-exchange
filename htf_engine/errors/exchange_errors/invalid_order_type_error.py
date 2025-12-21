from .invalid_order_error import InvalidOrderError


class InvalidOrderTypeError(InvalidOrderError):
    error_code = "INVALID_ORDER_TYPE"

    def __init__(self, order_type: str):
        self.order_type = order_type
        super().__init__()

    def default_message(self) -> str:
        return self.header_string() + f"Invalid order type {self.order_type} received."
    