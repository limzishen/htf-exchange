from typing import Optional

from .order_book import OrderBook
from .user.user import User
from .orders.order import Order
from .trades.trade import Trade


class Exchange:
    def __init__(self, fee=0):
        self.users = {}          # user_id -> User
        self.order_books = {}    # instrument -> OrderBook
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
        ob.cleanup_discarded_order_callback = lambda order: self.cleanup_discarded_order(order, ob.instrument)

    def place_order(
            self,
            user_id: str,
            instrument: str,
            order_type: str,
            side: str,
            qty: int,
            price: Optional[float] = None
    ) -> str:
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
        ob = self.order_books[instrument]
        order_id = ob.add_order(order_type, side, qty, price, user_id=user_id)
        return order_id

    def modify_order(
            self,
            user_id: str,
            instrument: str,
            order_id: str,
            new_qty: int,
            new_price: float
    ) -> str: 
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if instrument not in self.order_books: 
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
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
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
            
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
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

    def process_trade(self, trade: Trade, instrument:str) -> None:
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
        user = self.users.get(order.user_id)

        if order.is_buy_order():
            user.reduce_outstanding_buys(instrument, order.qty)
        else:
            user.reduce_outstanding_sells(instrument, order.qty)

    def _earn_fee(self) -> None:
        self.balance += self.fee
    
    def change_fee(self, new_fee: int) -> None:
        self.fee = new_fee
    
    # Read Operations
        
    def get_user_positions(self, user_id):
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        user = self.users[user_id]

        user_positions = user.get_positions()
        return user_positions

    def get_user_cash_balance(self, user_id):
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        user = self.users[user_id]
        
        user_cash_balance = user.get_cash_balance()
        return user_cash_balance

    def get_user_realised_pnl(self, user_id):
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        user = self.users[user_id]
        
        user_realised_pnl = user.get_realised_pnl()
        return user_realised_pnl

    def get_user_unrealised_pnl_for_inst(self, user_id, inst):
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if inst not in self.order_books: 
            raise ValueError(f"Instrument '{inst}' does not exist in the exchange.")
        
        user = self.users[user_id]

        if inst not in user.positions:
            raise ValueError(f"User {user.user_id} has no position in {inst}")

        ob = self.order_books.get(inst)
        if ob is None or ob.last_price is None:
            return 0.0

        qty = user.positions[inst]
        avg = user.average_cost[inst]

        user_unrealised_pnl_for_inst = qty * (ob.last_price - avg)
        return user_unrealised_pnl_for_inst

    def get_user_unrealised_pnl(self, user_id) -> float:
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")

        user = self.users[user_id]
        total = 0.0

        for inst in user.positions:
            total += self.get_user_unrealised_pnl_for_inst(user_id, inst)

        return total
    
    def get_user_exposure_for_inst(self, user_id, inst):
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if inst not in self.order_books: 
            raise ValueError(f"Instrument '{inst}' does not exist in the exchange.")
        
        user = self.users[user_id]

        if inst not in user.positions:
            raise ValueError(f"User {user.user_id} has no position in {inst}")

        ob = self.order_books.get(inst)
        if ob is None or ob.last_price is None:
            return 0.0

        qty = user.positions[inst]

        return abs(qty) * ob.last_price
    
    def get_user_exposure(self, user_id):
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")

        user = self.users[user_id]
        total = 0.0

        for inst in user.positions:
            total += self.get_user_exposure_for_inst(user_id, inst)
        
        return total
    
    def get_user_remaining_quota_for_inst(self, user_id: str, inst: str) -> dict:
        """
        Returns how much more the user can buy or sell for a given instrument
        without breaching the position limit.

        Returns:
            dict: {"buy_quota": int, "sell_quota": int}
        """
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if inst not in self.order_books: 
            raise ValueError(f"Instrument '{inst}' does not exist in the exchange.")
        
        user = self.users[user_id]

        user_remaining_quota_for_inst = user.get_remaining_quota(inst)
        return user_remaining_quota_for_inst
    
    def get_L1_data(self, user_id, inst):
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
        """
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if inst not in self.order_books:
            raise ValueError(f"Instrument '{inst}' does not exist in the exchange.")

        ob = self.order_books[inst]

        best_bid = ob.best_bid()
        best_ask = ob.best_ask()

        best_bid_qty = (
            sum(o.qty for o in ob.bids[best_bid] if o.order_id not in ob.cancelled_orders)
            if best_bid is not None else 0
        )
        best_ask_qty = (
            sum(o.qty for o in ob.asks[best_ask] if o.order_id not in ob.cancelled_orders)
            if best_ask is not None else 0
        )

        return {
            "instrument": inst,
            "best_bid": best_bid,
            "best_bid_qty": best_bid_qty,
            "best_ask": best_ask,
            "best_ask_qty": best_ask_qty,
            "last_price": ob.last_price,
            "last_qty": ob.last_quantity,
            "timestamp": ob.last_time.isoformat() if ob.last_time else None,
        }

    def get_L2_data(self, user_id, inst, depth: int = 5):
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
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        user = self.users[user_id]

        if user.get_permission_level() < 2:
            raise ValueError(f"User '{user_id}' does not have access to L2 market data!")
        
        if inst not in self.order_books:
            raise ValueError(f"Instrument '{inst}' does not exist in the exchange.")

        ob = self.order_books[inst]

        bids = []
        asks = []

        # Bids: highest price first
        for price in sorted(ob.bids.keys(), reverse=True)[:depth]:
            total_qty = sum(
                o.qty for o in ob.bids[price]
                if o.order_id not in ob.cancelled_orders
            )
            if total_qty > 0:
                bids.append({
                    "price": price,
                    "quantity": total_qty
                })

        # Asks: lowest price first
        for price in sorted(ob.asks.keys())[:depth]:
            total_qty = sum(
                o.qty for o in ob.asks[price]
                if o.order_id not in ob.cancelled_orders
            )
            if total_qty > 0:
                asks.append({
                    "price": price,
                    "quantity": total_qty
                })

        return {
            "instrument": inst,
            "bids": bids,
            "asks": asks,
        }

    def get_L3_data(self, user_id, inst):
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
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        user = self.users[user_id]

        if user.get_permission_level() < 3:
            raise ValueError(f"User '{user_id}' does not have access to L3 market data!")
        
        if inst not in self.order_books:
            raise ValueError(f"Instrument '{inst}' does not exist in the exchange.")

        ob = self.order_books[inst]

        def serialize_side(side_dict, reverse=False):
            levels = []
            for price in sorted(side_dict.keys(), reverse=reverse):
                orders = []
                for o in side_dict[price]:
                    if o.order_id in ob.cancelled_orders:
                        continue
                    orders.append({
                        "order_id": o.order_id,
                        "qty": o.qty,
                        "user_id": o.user_id,
                        "order_type": o.__class__.__name__,
                        "timestamp": o.timestamp.isoformat(),
                    })
                if orders:
                    levels.append({
                        "price": price,
                        "orders": orders
                    })
            return levels

        return {
            "instrument": inst,
            "bids": serialize_side(ob.bids, reverse=True),
            "asks": serialize_side(ob.asks, reverse=False),
        }
