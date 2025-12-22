from .invalid_order_error import InvalidOrderError


class InvalidOrderQuantityError(InvalidOrderError):
    error_code = "INVALID_ORDER_QUANTITY"

    def __init__(self, order_quantity: int):
        self.order_quantity = order_quantity
        super().__init__()

    def default_message(self) -> str:
        return self.header_string() + f"Order quantity must be positive (received={self.order_quantity})."
    