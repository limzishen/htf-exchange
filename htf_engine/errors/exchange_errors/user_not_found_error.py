from .exchange_error import ExchangeError


class UserNotFoundError(ExchangeError):
    error_code = "USER_NOT_FOUND"

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__()

    def default_message(self) -> str:
        return f"User '{self.user_id}' is not registered with the exchange."
