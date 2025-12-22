from .exchange_error import ExchangeError


class InvalidAggressorError(ExchangeError):
    error_code = "INVALID_AGGRESSOR"

    def __init__(self, aggressor: str):
        self.aggressor = aggressor
        super().__init__()

    def default_message(self) -> str:
        return f"Invalid aggressor {self.aggressor} received. Must be 'buy' or 'sell'."
