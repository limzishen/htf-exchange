from datetime import datetime, timezone
from .trade import Trade


class TradeLog:
    VALID_AGGRESSORS = {"buy", "sell"}

    def __init__(self):
        self._trades = []

    def record(
        self,
        price: float,
        qty: int,
        buy_user_id: str,
        sell_user_id: str,
        buy_order_id: str,
        sell_order_id: str,
        aggressor: str
    ):
        if aggressor not in self.VALID_AGGRESSORS:
            raise ValueError(f"Invalid aggressor: {aggressor}")

        trade = Trade(
            timestamp=datetime.now(timezone.utc),
            price=price,
            qty=qty,
            buy_user_id=buy_user_id,
            sell_user_id=sell_user_id,
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            aggressor=aggressor,
        )
        self._trades.append(trade)
        return trade

    def retrieve_log(self) -> tuple:
        return tuple(self._trades)        # defensive copy
    
    def retrieve_simple_log(self) -> tuple:
        return tuple(map(str, self._trades))

    def __str__(self):
        return "\n".join(str(trade) for trade in self._trades)