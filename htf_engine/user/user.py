from collections import defaultdict
from typing import Any, Callable, Dict, Optional

from htf_engine.errors.exchange_errors.user_not_found_error import UserNotFoundError
from htf_engine.errors.exchange_errors.order_exceeds_position_limit_error import (
    OrderExceedsPositionLimitError,
)
from htf_engine.errors.user_errors.insufficient_balance_for_withdrawal_error import (
    InsufficientBalanceForWithdrawalError,
)
from htf_engine.user.user_log import UserLog
from htf_engine.trades.trade import Trade
from htf_engine.orders.stop_order import StopOrder


class User:
    user_id: str
    username: str
    cash_balance: float
    realised_pnl: float

    positions: Dict[str, int]
    average_cost: Dict[str, float]
    outstanding_buys: defaultdict[str, int]
    outstanding_sells: defaultdict[str, int]

    user_log: UserLog

    place_order_callback: Optional[
        Callable[[str, str, str, str, int, Optional[float], Optional[float]], str]
    ]
    cancel_order_callback: Optional[Callable[[str, str, str], bool]]
    modify_order_callback: Optional[Callable[[str, str, str, int, float], str]]

    permission_level: int

    def __init__(self, user_id: str, username: str, cash_balance: float = 0.0):
        self.user_id = user_id
        self.username = username
        self.cash_balance = cash_balance
        self.realised_pnl = 0.0

        self.positions = {}  # instrument -> quantity
        self.average_cost = {}  # instrument -> avg cost
        self.outstanding_buys = defaultdict(int)  # instrument -> qty
        self.outstanding_sells = defaultdict(int)  # instrument -> qty

        self.user_log = UserLog(user_id, username)

        self.place_order_callback = None
        self.cancel_order_callback = None
        self.modify_order_callback = None

        self.permission_level = 0

    def cash_in(self, amount: float) -> None:
        self._increase_cash_balance(amount)
        self.user_log.record_cash_in(amount, self.cash_balance)

    def register(self, permission_level: int) -> None:
        self.user_log.record_register_user(self.cash_balance)
        self.permission_level = permission_level

    def cash_out(self, amount: float) -> None:
        if amount > self.cash_balance:
            raise InsufficientBalanceForWithdrawalError(
                withdrawal_amt=amount, user_cash_balance=self.cash_balance
            )

        self._decrease_cash_balance(amount)
        self.user_log.record_cash_out(amount, self.cash_balance)

    def _can_place_order(self, instrument: str, side: str, qty: int) -> bool:
        quota = self.get_remaining_quota(instrument)
        return (
            qty <= quota["buy_quota"] if side == "buy" else qty <= quota["sell_quota"]
        )

    def log_stops_trigger(self, order: StopOrder, instrument_id: str):
        self.user_log.record_stops_trigger(
            instrument_id=instrument_id,
            order_type=order.order_type,
            underlying_order_type=order.underlying_order_type,
            side=order.side,
            quantity=order.qty,
            stop_price=order.stop_price,
            price=getattr(order, "price", None),
        )

    def place_order(
        self,
        instrument: str,
        order_type: str,
        side: str,
        qty: int,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> str:
        if self.place_order_callback is None:
            raise UserNotFoundError(self.user_id)

        # --- CHECK USER POSITION LIMITS ---
        if not self._can_place_order(instrument, side, qty):
            raise OrderExceedsPositionLimitError(
                inst=instrument,
                side=side,
                qty=qty,
                quota=self.get_remaining_quota(instrument),
            )

        # --- UPDATE OUTSTANDING BUYS/SELLS ---
        if side == "buy":
            self.increase_outstanding_buys(instrument, qty)
        else:
            self.increase_outstanding_sells(instrument, qty)

        # Place order
        order_id = self.place_order_callback(
            self.user_id, instrument, order_type, side, qty, price, stop_price
        )

        # Record the order in the log
        self.user_log.record_place_order(instrument, order_type, side, qty, price)

        return order_id

    def cancel_order(self, order_id: str, instrument: str) -> bool:
        if self.cancel_order_callback is None:
            raise UserNotFoundError(self.user_id)

        try:
            self.cancel_order_callback(self.user_id, instrument, order_id)
            self.user_log.record_cancel_order(order_id, instrument)
            return True
        except ValueError:
            return False

    def modify_order(
        self, instrument_id: str, order_id: str, new_qty: int, new_price: float
    ) -> bool:
        if self.modify_order_callback is None:
            raise UserNotFoundError(self.user_id)

        try:
            self.modify_order_callback(
                self.user_id, instrument_id, order_id, new_qty, new_price
            )
            self.user_log.record_modify_order(
                order_id, instrument_id, new_qty, self.cash_balance
            )
            return True
        except ValueError:
            return False

    def update_positions_and_cash_balance(
        self, trade: Trade, instrument: str, exchange_fee: float
    ) -> None:
        qty = trade.qty
        price = trade.price

        old_qty = self.positions.get(instrument, 0)
        old_avg = self.average_cost.get(instrument, 0.0)

        # BUY
        if trade.buy_user_id == self.user_id:
            self.reduce_outstanding_buys(instrument, qty)

            if old_qty >= 0:
                # increasing long OR opening long
                new_qty = old_qty + qty
                new_avg = (
                    (old_qty * old_avg + qty * price) / new_qty
                    if old_qty != 0
                    else price
                )
            else:
                # covering short
                realised = min(qty, -old_qty) * (old_avg - price)
                self.realised_pnl += realised
                new_qty = old_qty + qty
                new_avg = old_avg if new_qty < 0 else price

            cash_delta = qty * price

            self._decrease_cash_balance(cash_delta)
            self._decrease_cash_balance(exchange_fee)

        # SELL
        elif trade.sell_user_id == self.user_id:
            self.reduce_outstanding_sells(instrument, qty)

            if old_qty <= 0:
                # increasing short OR opening short
                new_qty = old_qty - qty
                new_avg = (
                    (abs(old_qty) * old_avg + qty * price) / abs(new_qty)
                    if old_qty != 0
                    else price
                )
            else:
                # selling long
                realised = min(qty, old_qty) * (price - old_avg)
                self.realised_pnl += realised
                new_qty = old_qty - qty
                new_avg = old_avg if new_qty > 0 else price

            cash_delta = qty * price

            self._increase_cash_balance(cash_delta)
            self._decrease_cash_balance(exchange_fee)

        # Cleanup
        if new_qty == 0:
            self.positions.pop(instrument, None)
            self.average_cost.pop(instrument, None)
        else:
            self.positions[instrument] = new_qty
            self.average_cost[instrument] = new_avg

    def get_positions(self) -> dict[str, Any]:
        """
        Returns:
        {
            instrument: {
                "quantity": int,
                "average_cost": float
            }
        }
        """
        return {
            inst: {"quantity": qty, "average_cost": self.average_cost[inst]}
            for inst, qty in self.positions.items()
        }

    def _increase_cash_balance(self, amount: float) -> None:
        self.cash_balance += amount

    def _decrease_cash_balance(self, amount: float) -> None:
        self.cash_balance -= amount

    def get_cash_balance(self) -> float:
        return self.cash_balance

    def get_realised_pnl(self) -> float:
        return self.realised_pnl

    def get_remaining_quota(self, instrument: str) -> dict[str, int]:
        """
        Returns how much more the user can buy or sell for a given instrument
        without breaching the position limit.

        Returns:
            dict: {
                "buy_quota": int,
                "sell_quota": int
            }
        """
        limit = 100  # TODO: make this configurable if needed

        current = self.positions.get(instrument, 0)

        outstanding_buy = self.outstanding_buys.get(instrument, 0)
        outstanding_sell = self.outstanding_sells.get(instrument, 0)

        buy_quota = limit - current - outstanding_buy
        sell_quota = limit + current - outstanding_sell

        # Ensure non-negative quotas
        return {"buy_quota": max(0, buy_quota), "sell_quota": max(0, sell_quota)}

    def increase_outstanding_buys(self, instrument: str, qty: int) -> None:
        self.outstanding_buys[instrument] += qty

    def increase_outstanding_sells(self, instrument: str, qty: int) -> None:
        self.outstanding_sells[instrument] += qty

    def reduce_outstanding_buys(self, instrument: str, qty: int) -> None:
        self.outstanding_buys[instrument] -= qty

        if self.outstanding_buys[instrument] == 0:
            self.outstanding_buys.pop(instrument)

    def reduce_outstanding_sells(self, instrument: str, qty: int) -> None:
        self.outstanding_sells[instrument] -= qty

        if self.outstanding_sells[instrument] == 0:
            self.outstanding_sells.pop(instrument)

    def get_outstanding_buys(self) -> dict[str, int]:
        return self.outstanding_buys

    def get_outstanding_sells(self) -> dict[str, int]:
        return self.outstanding_sells

    def get_permission_level(self) -> int:
        return self.permission_level
