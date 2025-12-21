from .invalid_order_error import InvalidOrderError


class PostOnlyViolationError(InvalidOrderError):
    error_code = "POST_ONLY_VIOLATION"

    def default_message(self) -> str:
        return self.header_string() + "Post-only order would take liquidity and was rejected."
    