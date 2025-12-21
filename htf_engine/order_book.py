from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Callable, Dict, Deque, List, Optional, Set, Tuple

import uuid
import heapq
import itertools

from .matchers.fok_matcher import FOKOrderMatcher
from .matchers.ioc_matcher import IOCOrderMatcher
from .matchers.limit_matcher import LimitOrderMatcher
from .matchers.market_matcher import MarketOrderMatcher
from .matchers.post_only_matcher import PostOnlyOrderMatcher
from .matchers.stop_matcher import StopOrderMatcher
from .orders.fok_order import FOKOrder
from .orders.ioc_order import IOCOrder
from .orders.limit_order import LimitOrder
from .orders.market_order import MarketOrder
from .orders.stop_limit_order import StopLimitOrder
from .orders.stop_market_order import StopMarketOrder
from .orders.stop_order import StopOrder
from .orders.order import Order
from .orders.post_only_order import PostOnlyOrder
from .trades.trade import Trade
from .trades.trade_log import TradeLog


class OrderBook:
    bids: Dict[float, Deque[Order]]
    asks: Dict[float, Deque[Order]]
    order_map: Dict[str, Order]
    best_bids: List[Tuple[float, str, str]] 
    best_asks: List[Tuple[float, str, str]]
    last_price: Optional[float]
    last_quantity: Optional[int]
    last_time: Optional[str]
    cancelled_orders: Set[str]

    stop_bids: Dict[float, Deque[StopOrder]]
    stop_asks: Dict[float, Deque[StopOrder]]
    stop_bids_price: List[Tuple[float, str, str]]
    stop_asks_price: List[Tuple[float, str, str]]

    trade_log: TradeLog
    on_trade_callback: Optional[Callable[[Trade], None]]
    cleanup_discarded_order_callback: Optional[Callable[[Order], None]]

    def __init__(self, instrument: str, enable_stp: bool = True):
        self.instrument = instrument

        self.bids = defaultdict(deque)
        self.asks = defaultdict(deque)
        self.order_map = {}
        self.best_bids = [] #  (price , timestamp, uuid)
        self.best_asks = []
        self.order_counter = itertools.count()
        self.last_price = None
        self.last_quantity = None
        self.last_time = None
        self.cancelled_orders = set()

        self.stop_bids = defaultdict(deque)
        self.stop_asks = defaultdict(deque)
        self.stop_bids_price = []
        self.stop_asks_price = []

        self.matchers = {
            "fok": FOKOrderMatcher(),
            "ioc": IOCOrderMatcher(),
            "limit": LimitOrderMatcher(),
            "market": MarketOrderMatcher(),
            "post-only": PostOnlyOrderMatcher(),
            "stop-limit": StopOrderMatcher(),
            "stop-market": StopOrderMatcher()
        }

        self.trade_log = TradeLog()
        self.on_trade_callback = None  # Exchange handler!!
        self.cleanup_discarded_order_callback = None

        self.enable_stp = enable_stp

    def add_order(
        self,
        order_type: str,
        side: str,
        qty: int,
        price: Optional[float] = None,
        user_id: Optional[str] = None, 
        stop_price: Optional[float] = None
    ) -> str:
        order_count = next(self.order_counter)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %Z")
        data_string = (
            f"{order_count}|"
            f"{side}|"
            f"{self.instrument}|"
            f"{price}|"
            f"{user_id}"
            f"{timestamp}"
        )
        # Create a Unique ID for each order
        order_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, data_string))

        if user_id is None:
            user_id = "TESTING: NO_USER_ID"

        # create order object
        order: Order

        if order_type == "limit" and price is not None:
            order = LimitOrder(order_uuid, side, price, qty, user_id, timestamp)
        elif order_type == "market" and price is None:
            order = MarketOrder(order_uuid, side, qty, user_id, timestamp)
        elif order_type == "ioc" and price is not None:
            order = IOCOrder(order_uuid, side, price, qty, user_id, timestamp)
        elif order_type == "fok" and price is not None:
            order = FOKOrder(order_uuid, side, price, qty, user_id, timestamp)
        elif order_type == "post-only" and price is not None:
            order = PostOnlyOrder(order_uuid, side, price, qty, user_id, timestamp)
        elif order_type == "stop-limit" and stop_price is not None and price is not None:
            order = StopLimitOrder(order_uuid, side, stop_price, price, qty, user_id, timestamp)
        elif order_type == "stop-market" and stop_price is not None and price is None:
            order = StopMarketOrder(order_uuid, side, stop_price, qty, user_id, timestamp)
        else:
            raise ValueError(f"Error: Order cannot be created")

        # Execute matching
        self.matchers[order_type].match(self, order)

        return order_uuid

    def check_stop_orders(self) -> None: 
        if not self.last_price: 
            return 
        
        while self.stop_bids_price and -self.stop_bids_price[0][0] <= self.last_price:
            if self.stop_bids_price[0][2] not in self.cancelled_orders: 
                order = self.stop_bids[-self.stop_bids_price[0][0]].pop()
                self.add_order(
                    order_type=order.underlying_order_type, 
                    side=order.side, 
                    qty=order.qty,
                    price=getattr(order, "price", None), 
                    user_id=order.user_id
                )
            else: 
                self.cancelled_orders.remove(self.stop_bids_price[0][2])

            del self.order_map[self.stop_bids_price[0][2]]
            heapq.heappop(self.stop_bids_price)
        
        while self.stop_asks_price and self.stop_asks_price[0][0] >= self.last_price:
            if self.stop_asks_price[0][2] not in self.cancelled_orders:
                order = self.stop_asks[self.stop_asks_price[0][0]].pop()
                self.add_order(
                    order_type=order.underlying_order_type, 
                    side=order.side, 
                    qty=order.qty,
                    price=getattr(order, "price", None), 
                    user_id=order.user_id
                )
            else: 
                self.cancelled_orders.remove(self.stop_asks_price[0][2])

            del self.order_map[self.stop_asks_price[0][2]]
            heapq.heappop(self.stop_asks_price)


    def modify_order(
        self,
        order_id: str,
        new_qty: int,
        new_price: float, 
        new_stop_price: Optional[float] = None
    ) -> str:
        """Returns current order id if qty decrease and no change else new order_id"""
        if order_id not in self.order_map:
            print("Order not found!!")
            return "False"

        curr_order = self.order_map[order_id]

        if curr_order.stop: 
            self.cancel_order(curr_order.order_id)
            return self.add_order(
                curr_order.order_type, 
                curr_order.side, 
                new_qty, 
                new_price, 
                curr_order.user_id, 
                new_stop_price
            )

        if getattr(curr_order, "price", None) != new_price or new_qty > curr_order.qty:
            self.cancelled_orders.add(order_id)
            return self.add_order(curr_order.order_type, curr_order.side, new_qty, new_price, curr_order.user_id)

        if new_qty < curr_order.qty:
            curr_order.qty = new_qty
            print("Quantity updated!")
            return curr_order.order_id

        print("No change to order!")
        return order_id

    def clean_orders(
        self,
        order_heap: list,
        queue_dict: dict
    ) -> None:
        while order_heap and order_heap[0][2] in self.cancelled_orders:
            if queue_dict == self.bids:
                order_price, timestamp, oid_to_clean = -order_heap[0][0], order_heap[0][1], order_heap[0][2]
            else:
                order_price, timestamp, oid_to_clean = order_heap[0]
            
            removed_order = queue_dict[order_price].popleft()

            if oid_to_clean in self.order_map:
                del self.order_map[oid_to_clean]
            
            heapq.heappop(order_heap)
            self.cancelled_orders.remove(oid_to_clean)
            print(f"{removed_order.order_id} removed from queue, {oid_to_clean} removed from heap")
    
    def best_bid(self) -> Optional[float]:
        self.clean_orders(self.best_bids, self.bids)
        
        return -self.best_bids[0][0] if self.best_bids else None

    def best_ask(self) -> Optional[float]:
        self.clean_orders(self.best_asks, self.asks)
        
        return self.best_asks[0][0] if self.best_asks else None

    def get_all_pending_orders(self) -> list[str]:
        return [str(v) for v in self.order_map.values() if v.order_id not in self.cancelled_orders]

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.order_map:
            self.cancelled_orders.add(order_id)
            return True
        
        print("Order not found!!")
        return False

    def record_trade(
            self,
            price: float,
            qty: int,
            buy_order: Order,
            sell_order: Order,
            aggressor: str
    ) -> TradeLog:
        trade = self.trade_log.record(
            price=price,
            qty=qty,
            buy_user_id=buy_order.user_id,
            sell_user_id=sell_order.user_id,
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
            aggressor=aggressor,
        )

        self.last_price = trade.price
        self.last_quantity = trade.qty
        self.last_time = trade.timestamp
        
        if self.on_trade_callback:
            self.on_trade_callback(trade)  # Notify Exchange
        
        return trade

    def cleanup_discarded_order(self, order: Order) -> None:
        if self.cleanup_discarded_order_callback:
            self.cleanup_discarded_order_callback(order)
    
    def __str__(self):
        bid_levels = sorted(self.bids.items(), key=lambda x: -x[0])
        ask_levels = sorted(self.asks.items(), key=lambda x: x[0])

        bid_lines = []
        ask_lines = []

        for price, orders in bid_levels:
            total_qty = sum(o.qty for o in orders if o.order_id not in self.cancelled_orders)
            if total_qty > 0:
                bid_lines.append(f"{price:>5} : {total_qty:<5}")

        for price, orders in ask_levels:
            total_qty = sum(o.qty for o in orders if o.order_id not in self.cancelled_orders)
            if total_qty > 0:
                ask_lines.append(f"{price:>5} : {total_qty:<5}")

        # Pad lists to equal height
        h = max(len(bid_lines), len(ask_lines))
        bid_lines += [" " * 13] * (h - len(bid_lines))
        ask_lines += [" " * 13] * (h - len(ask_lines))

        rows = ["--------- ORDERBOOK ---------",
                "     BIDS     |     ASKS     ",
                "--------------|--------------"]

        for b, a in zip(bid_lines, ask_lines):
            rows.append(f"{b} | {a}")

        rows.append("-----------------------------")
        rows.append(f"Best Bid: {self.best_bid()}")
        rows.append(f"Best Ask: {self.best_ask()}")

        return "\n".join(rows)

    def _snapshot_side(self, side_levels: dict[float, deque[Order]]) -> tuple:
        """
        Representation of one side (bids or asks).
        Ignores empty price levels.
        Preserves FIFO at each price (deque order).
        """
        snap = []
        for price in sorted(side_levels.keys()):
            q = side_levels[price]
            if not q:
                continue

            orders = []
            for o in q:
                # capture only state that defines the book
                if o.order_id in self.cancelled_orders:   # skip cancelled orders
                    continue
                orders.append((
                    getattr(o, "order_id", None),
                    getattr(o, "side", None),
                    getattr(o, "price", None),
                    getattr(o, "qty", None),
                    o.__class__.__name__,  # "LimitOrder", "IOCOrder", etc.
                ))
            snap.append((price, tuple(orders)))
        return tuple(snap)

    def snapshot(self) -> dict:
        """
        Snapshot used for equality / tests.
        Does NOT rely on heap internal ordering.
        """
        return {
            "bids": self._snapshot_side(self.bids),
            "asks": self._snapshot_side(self.asks),
            "best_bid": self.best_bid(),
            "best_ask": self.best_ask(),
            "last_price": self.last_price,
            "last_quantity": self.last_quantity,
        }

    def __eq__(self, other):
        if not isinstance(other, OrderBook):
            return NotImplemented
        return self.snapshot() == other.snapshot()
