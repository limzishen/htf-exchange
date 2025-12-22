from .invalid_order_error import InvalidOrderError


class InvalidStopPriceError(InvalidOrderError):
    error_code = "INVALID_STOP_PRICE"

    def __init__(self, is_buy_order: bool):
        self.is_buy_order = is_buy_order
        super().__init__()

    def default_message(self) -> str:
        return self.header_string() + f"Stop price {"less" if self.is_buy_order else "greater"} than or equal to last traded price"
    