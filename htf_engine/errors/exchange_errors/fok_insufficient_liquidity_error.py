from .invalid_order_error import InvalidOrderError


class FOKInsufficientLiquidityError(InvalidOrderError):
    error_code = "FOK_INSUFFICIENT_LIQUIDITY"

    def default_message(self) -> str:
        return self.header_string() + "FOK order had insufficient liquidity and was cancelled."
    