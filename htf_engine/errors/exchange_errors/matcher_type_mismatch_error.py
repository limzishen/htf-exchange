from .exchange_error import ExchangeError


class MatcherTypeMismatchError(ExchangeError):
    error_code = "MATCHER_TYPE_MISMATCH"

    def __init__(self, order_type: str, matcher_type: str):
        self.order_type = order_type
        self.matcher_type = matcher_type
        super().__init__()

    def default_message(self) -> str:
        return f"Order of type '{self.order_type}' passed into matcher of type '{self.matcher_type}'."
