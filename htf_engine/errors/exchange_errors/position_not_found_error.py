from .exchange_error import ExchangeError


class PositionNotFoundError(ExchangeError):
    error_code = "POSITION_NOT_FOUND"

    def __init__(self, instrument: str, user_id: str):
        self.instrument = instrument
        self.user_id = user_id
        super().__init__()

    def default_message(self) -> str:
        return f"User {self.user_id} has no position in {self.instrument}"
