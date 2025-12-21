from .exchange_error import ExchangeError


class InvalidOrderError(ExchangeError):
    error_code = "INVALID_ORDER"

    def default_message(self) -> str:
        return "The order is invalid."
    