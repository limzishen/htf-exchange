from typing import Any, Optional

from .errors.exchange_errors.instrument_not_found_error import InstrumentNotFoundError
from .errors.exchange_errors.permission_denied_error import PermissionDeniedError
from .errors.exchange_errors.position_not_found_error import PositionNotFoundError
from .errors.exchange_errors.user_not_found_error import UserNotFoundError

from .order_book import OrderBook
from .user.user import User
from .orders.order import Order
from .orders.stop_order import StopOrder
from .trades.trade import Trade


class Exchange:
    users: dict[str, User]
    order_books: dict[str, OrderBook]
    fee: float
    balance: float

    def __init__(self, fee: float = 0):
        self.users = {}  # user_id -> User
        self.order_books = {}  # instrument -> OrderBook
        self.fee = fee
        self.balance = 0

    def register_user(self, user: User, permission_level=1) -> bool:
        if user.user_id in self.users:
            print(f"User {user.user_id} is already registered in exchange!")
            return False

        self.users[user.user_id] = user
        user.register(permission_level)
        user.place_order_callback = self.place_order
        user.cancel_order_callback = self.cancel_order
        user.modify_order_callback = self.modify_order
        return True

    def add_order_book(self, instrument: str, ob: OrderBook) -> None:
        self.order_books[instrument] = ob
        ob.on_trade_callback = lambda trade: self.process_trade(trade, ob.instrument)
        ob.cleanup_discarded_order_callback = (
            lambda order: self.cleanup_discarded_order(order, ob.instrument)
        )
        ob.record_stop_trigger_callback = (
            lambda user_id, instrument, order: self.record_stops_triggers(
                user_id, instrument, order
            )
        )

    def place_order(
        self,
        user_id: str,
        instrument: str,
        order_type: str,
        side: str,
        qty: int,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> str:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if instrument not in self.order_books:
            raise InstrumentNotFoundError(instrument)

        ob = self.order_books[instrument]
        order_id = ob.add_order(
            order_type=order_type,
            side=side,
            qty=qty,
            price=price,
            user_id=user_id,
            stop_price=stop_price,
        )
        return order_id

    def record_stops_triggers(self, user_id: str, instrument: str, order: StopOrder):
        user = self.users[user_id]
        user.log_stops_trigger(order, instrument)

    def modify_order(
        self,
        user_id: str,
        instrument: str,
        order_id: str,
        new_qty: int,
        new_price: float,
    ) -> str:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if instrument not in self.order_books:
            raise InstrumentNotFoundError(instrument)

        ob = self.order_books[instrument]
        if order_id not in ob.order_map:
            print("Order not found in order book!")
            return "False"

        prev_order = ob.order_map[order_id]
        qty_change = new_qty - prev_order.qty
        new_order_id = ob.modify_order(order_id, new_qty, new_price)

        # Update outstanding
        if prev_order.side == "buy":
            if qty_change > 0:
                self.users[user_id].increase_outstanding_buys(instrument, qty_change)

            if qty_change < 0:
                self.users[user_id].reduce_outstanding_buys(instrument, -qty_change)

        if prev_order.side == "sell":
            if qty_change > 0:
                self.users[user_id].increase_outstanding_sells(instrument, qty_change)

            if qty_change < 0:
                self.users[user_id].reduce_outstanding_sells(instrument, -qty_change)

        return new_order_id

    def cancel_order(self, user_id: str, instrument: str, order_id: str) -> bool:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if instrument not in self.order_books:
            raise InstrumentNotFoundError(instrument)

        ob = self.order_books[instrument]

        if order_id not in ob.order_map:
            print("Order not found in order book!")
            return False

        order = ob.order_map[order_id]

        # Remove from user's outstanding
        if order.side == "buy":
            self.users[user_id].reduce_outstanding_buys(instrument, order.qty)
        else:
            self.users[user_id].reduce_outstanding_sells(instrument, order.qty)

        # Cancel in order book
        return ob.cancel_order(order_id)

    def process_trade(self, trade: Trade, instrument: str) -> None:
        """Called by order book whenever a trade occurs"""
        buy_user = self.users.get(trade.buy_user_id)
        sell_user = self.users.get(trade.sell_user_id)
        if buy_user:
            buy_user.update_positions_and_cash_balance(trade, instrument, self.fee)
            self._earn_fee()
        if sell_user:
            sell_user.update_positions_and_cash_balance(trade, instrument, self.fee)
            self._earn_fee()

    def cleanup_discarded_order(self, order: Order, instrument: str) -> None:
        user_id = order.user_id

        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]

        if order.is_buy_order():
            user.reduce_outstanding_buys(instrument, order.qty)
        else:
            user.reduce_outstanding_sells(instrument, order.qty)

    def _earn_fee(self) -> None:
        self.balance += self.fee

    def change_fee(self, new_fee: float) -> None:
        self.fee = new_fee

    # GET Operations (for API)

    def get_user_positions(self, user_id: str) -> dict:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]

        user_positions = user.get_positions()
        return user_positions

    def get_user_cash_balance(self, user_id: str) -> float:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]

        user_cash_balance = user.get_cash_balance()
        return user_cash_balance

    def get_user_realised_pnl(self, user_id: str) -> float:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]

        user_realised_pnl = user.get_realised_pnl()
        return user_realised_pnl

    def get_user_unrealised_pnl_for_inst(self, user_id: str, inst: str) -> float:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if inst not in self.order_books:
            raise InstrumentNotFoundError(inst)

        user = self.users[user_id]

        if inst not in user.positions:
            raise PositionNotFoundError(user_id=user_id, instrument=inst)

        ob = self.order_books.get(inst)
        if ob is None or ob.last_price is None:
            return 0.0

        qty = user.positions[inst]
        avg = user.average_cost[inst]

        user_unrealised_pnl_for_inst = qty * (ob.last_price - avg)
        return user_unrealised_pnl_for_inst

    def get_user_unrealised_pnl(self, user_id: str) -> float:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]
        user_unrealised_pnl = 0.0

        for inst in user.positions:
            user_unrealised_pnl += self.get_user_unrealised_pnl_for_inst(user_id, inst)

        return user_unrealised_pnl

    def get_user_exposure_for_inst(self, user_id: str, inst: str) -> float:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if inst not in self.order_books:
            raise InstrumentNotFoundError(inst)

        user = self.users[user_id]

        if inst not in user.positions:
            raise PositionNotFoundError(user_id=user_id, instrument=inst)

        ob = self.order_books.get(inst)
        if ob is None or ob.last_price is None:
            return 0.0

        qty = user.positions[inst]

        # Exposure is always positive regardless of long or short
        user_exposure_for_inst = abs(qty) * ob.last_price
        return user_exposure_for_inst

    def get_user_exposure(self, user_id: str) -> float:
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]
        user_exposure = 0.0

        for inst in user.positions:
            user_exposure += self.get_user_exposure_for_inst(user_id, inst)

        return user_exposure

    def get_user_remaining_quota_for_inst(
        self, user_id: str, inst: str
    ) -> dict[str, int]:
        """
        Returns how much more the user can buy or sell for a given instrument
        without breaching the position limit.

        Returns:
            dict: {
                "buy_quota": int,
                "sell_quota": int
            }
        """
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if inst not in self.order_books:
            raise InstrumentNotFoundError(inst)

        user = self.users[user_id]

        user_remaining_quota_for_inst = user.get_remaining_quota(inst)
        return user_remaining_quota_for_inst

    def get_L1_data(self, user_id: str, inst: str) -> dict[str, Any]:
        """
        Level 1 (Top-of-Book) market data.

        Returns best bid / best ask and last traded information
        for a given instrument.

        JSON format:
        {
            "instrument": str,
            "best_bid": float | None,
            "best_bid_qty": int | None,
            "best_ask": float | None,
            "best_ask_qty": int | None,
            "last_price": float | None,
            "last_qty": int | None,
            "last_time": str | None
        }

        By default, all users are entitled to Level 1 market data.
        """
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        if inst not in self.order_books:
            raise InstrumentNotFoundError(inst)

        ob = self.order_books[inst]

        best_bid = ob.best_bid()
        best_ask = ob.best_ask()

        best_bid_qty = (
            sum(
                o.qty
                for o in ob.bids[best_bid]
                if o.order_id not in ob.cancelled_orders
            )
            if best_bid is not None
            else 0
        )
        best_ask_qty = (
            sum(
                o.qty
                for o in ob.asks[best_ask]
                if o.order_id not in ob.cancelled_orders
            )
            if best_ask is not None
            else 0
        )

        return {
            "instrument": inst,
            "best_bid": best_bid,
            "best_bid_qty": best_bid_qty,
            "best_ask": best_ask,
            "best_ask_qty": best_ask_qty,
            "last_price": ob.last_price,
            "last_qty": ob.last_quantity,
            "timestamp": ob.last_time if ob.last_time else None,
        }

    def get_L2_data(self, user_id: str, inst: str, depth: int = 5) -> dict[str, Any]:
        """
        Level 2 (Market Depth) data.

        Returns aggregated quantities at each price level
        for bids and asks, up to the specified depth.

        JSON format:
        {
            "instrument": str,
            "bids": [
                {"price": float, "quantity": int},
                ...
            ],
            "asks": [
                {"price": float, "quantity": int},
                ...
            ]
        }
        """
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]
        user_permission_level = user.get_permission_level()

        if user_permission_level < 2:
            raise PermissionDeniedError(
                user_id=user_id, required_level=2, actual_level=user_permission_level
            )

        if inst not in self.order_books:
            raise InstrumentNotFoundError(inst)

        ob = self.order_books[inst]

        def serialize_side(side_dict, reverse=False):
            levels = []
            for price in sorted(side_dict.keys(), reverse=reverse)[:depth]:
                total_qty = sum(
                    o.qty
                    for o in ob.bids[price]
                    if o.order_id not in ob.cancelled_orders
                )
                if total_qty > 0:
                    levels.append({"price": price, "quantity": total_qty})
            return levels

        return {
            "instrument": inst,
            "bids": serialize_side(ob.bids, reverse=True),
            "asks": serialize_side(ob.asks, reverse=False),
        }

    def get_L3_data(self, user_id: str, inst: str, depth: int = 5) -> dict[str, Any]:
        """
        Level 3 (Order-Level) market data.

        Returns all active orders in the order book,
        preserving FIFO order at each price level.

        JSON format:
        {
            "instrument": str,
            "bids": [
                {
                    "price": float,
                    "orders": [
                        {
                            "order_id": str,
                            "qty": int,
                            "user_id": str,
                            "order_type": str,
                            "timestamp": str
                        },
                        ...
                    ]
                },
                ...
            ],
            "asks": [
                {
                    "price": float,
                    "orders": [
                        {
                            "order_id": str,
                            "qty": int,
                            "user_id": str,
                            "order_type": str,
                            "timestamp": str
                        },
                        ...
                    ]
                },
                ...
            ]
        }
        """
        if user_id not in self.users:
            raise UserNotFoundError(user_id)

        user = self.users[user_id]
        user_permission_level = user.get_permission_level()

        if user_permission_level < 3:
            raise PermissionDeniedError(
                user_id=user_id, required_level=3, actual_level=user_permission_level
            )

        if inst not in self.order_books:
            raise InstrumentNotFoundError(inst)

        ob = self.order_books[inst]

        def serialize_side(side_dict, reverse=False):
            levels = []
            for price in sorted(side_dict.keys(), reverse=reverse)[:depth]:
                orders = []

                for o in side_dict[price]:
                    if o.order_id in ob.cancelled_orders:
                        continue
                    orders.append(
                        {
                            "order_id": o.order_id,
                            "qty": o.qty,
                            "user_id": o.user_id,
                            "order_type": o.__class__.__name__,
                            "timestamp": o.timestamp,
                        }
                    )

                if orders:
                    levels.append({"price": price, "orders": orders})

            return levels

        return {
            "instrument": inst,
            "bids": serialize_side(ob.bids, reverse=True),
            "asks": serialize_side(ob.asks, reverse=False),
        }
