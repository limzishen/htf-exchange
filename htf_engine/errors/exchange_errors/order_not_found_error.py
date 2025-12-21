from .exchange_error import ExchangeError


class OrderNotFoundError(ExchangeError):
    error_code = "ORDER_NOT_FOUND"

    def __init__(self, order_id: str):
        self.order_id = order_id
        super().__init__()

    def default_message(self) -> str:
        return f"Order '{self.order_id}' was not found."
