from collections import defaultdict
from htf_engine.user.user_log import UserLog

from htf_engine.trades.trade import Trade


class User:
    def __init__(self, user_id: str, username: str, cash_balance: float=0.0):
        self.user_id = user_id
        self.username = username
        self.cash_balance = cash_balance            # TODO... can ignore for now
        self.realised_pnl = 0.0

        self.positions = {}                         # instrument -> quantity
        self.average_cost = {}                      # instrument -> avg cost
        self.outstanding_buys = defaultdict(int)     # instrument -> qty
        self.outstanding_sells = defaultdict(int)    # instrument -> qty

        self.user_log = UserLog(user_id, username)

        self.place_order_callback = None
        self.cancel_order_callback = None
        self.modify_order_callback = None

        self.permission_level = 0


    def cash_in(self, amount: float) -> None:
        self._increase_cash_balance(amount)
        self.user_log.record_cash_in(amount, self.cash_balance)

    def register(self, permission_level):
        self.user_log.record_register_user(self.cash_balance)
        self.permission_level = permission_level

    def cash_out(self, amount: float) -> None:
        if amount > self.cash_balance:
            raise ValueError("Insufficient balance")
        self._decrease_cash_balance(amount)
        self.user_log.record_cash_out(amount, self.cash_balance)
    
    def _can_place_order(self, instrument: str, side: str, qty: int) -> bool:
        quota = self.get_remaining_quota(instrument)
        return qty <= quota["buy_quota"] if side == "buy" else qty <= quota["sell_quota"]


    def place_order(self, instrument: str, order_type: str, side: str, qty: int, price: float=None) -> str:
        # --- CHECK LIMIT ---
        if not self._can_place_order(instrument, side, qty):
            raise ValueError(f"User {self.user_id} cannot place order: would exceed position limit")
        
        # --- UPDATE OUTSTANDING ---
        if side == "buy":
            self.increase_outstanding_buys(instrument, qty)
        else:
            self.increase_outstanding_sells(instrument, qty)

        # Place order
        order_id = self.place_order_callback(self.user_id, instrument, order_type, side, qty, price)
        self.user_log.record_place_order(instrument, order_type, side, qty, price)
        return order_id

    def cancel_order(self, order_id: str, instrument: str) -> bool:
        try:
            self.cancel_order_callback(self.user_id, instrument, order_id)
            self.user_log.record_cancel_order(order_id, instrument)
            return True
        except ValueError as e:
            return False
    
    def modify_order(self, instrument_id: str, order_id: str, new_qty: int, new_price: float) -> bool:
        try:
            self.modify_order_callback(self.user_id, instrument_id, order_id, new_qty, new_price)
            self.user_log.record_modify_order(order_id, instrument_id, new_qty, self.cash_balance)
            return True
        except ValueError as e:
            return False

    def update_positions_and_cash_balance(self, trade: Trade, instrument: str, exchange_fee: int) -> None:
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
                new_avg = (old_qty * old_avg + qty * price) / new_qty if old_qty != 0 else price
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
                new_avg = (abs(old_qty) * old_avg + qty * price) / abs(new_qty) if old_qty != 0 else price
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

    def get_positions(self) -> dict:
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
            inst: {
                "quantity": qty,
                "average_cost": self.average_cost[inst]
            }
            for inst, qty in self.positions.items()
        }

    def _increase_cash_balance(self, amount: int) -> None:
        self.cash_balance += amount

    def _decrease_cash_balance(self, amount: int) -> None:
        self.cash_balance -= amount

    def get_cash_balance(self) -> float:
        return self.cash_balance
    
    def get_realised_pnl(self) -> float:
        return self.realised_pnl
    
    def get_remaining_quota(self, instrument: str) -> dict:
        """
        Returns how much more the user can buy or sell for a given instrument
        without breaching the position limit.

        Returns:
            dict: {"buy_quota": int, "sell_quota": int}
        """
        limit = 100  # TODO: make this configurable if needed

        current = self.positions.get(instrument, 0)

        outstanding_buy = self.outstanding_buys.get(instrument, 0)
        outstanding_sell = self.outstanding_sells.get(instrument, 0)

        buy_quota = limit - current - outstanding_buy
        sell_quota = limit + current - outstanding_sell

        # Ensure non-negative quotas
        return {
            "buy_quota": max(0, buy_quota),
            "sell_quota": max(0, sell_quota)
        }
    
    def increase_outstanding_buys(self, instrument, qty):
        self.outstanding_buys[instrument] += qty

    def increase_outstanding_sells(self, instrument, qty):
        self.outstanding_sells[instrument] += qty

    def reduce_outstanding_buys(self, instrument, qty):
        self.outstanding_buys[instrument] -= qty

        if self.outstanding_buys[instrument] == 0:
            self.outstanding_buys.pop(instrument)

    def reduce_outstanding_sells(self, instrument, qty):
        self.outstanding_sells[instrument] -= qty

        if self.outstanding_sells[instrument] == 0:
            self.outstanding_sells.pop(instrument)

    def get_outstanding_buys(self) -> dict:
        return self.outstanding_buys
    
    def get_outstanding_sells(self) -> dict:
        return self.outstanding_sells
    
    def get_permission_level(self) -> int:
        return self.permission_level
