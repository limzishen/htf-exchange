from collections import defaultdict, deque
import heapq
import itertools
from .matchers.fok_matcher import FOKOrderMatcher
from .matchers.ioc_matcher import IOCOrderMatcher
from .matchers.limit_matcher import LimitOrderMatcher
from .matchers.market_matcher import MarketOrderMatcher
from .orders.fok_order import FOKOrder
from .orders.ioc_order import IOCOrder
from .orders.limit_order import LimitOrder
from .orders.market_order import MarketOrder
from .trades.trade_log import TradeLog


class OrderBook:
    def __init__(self):
        self.bids = defaultdict(deque)
        self.asks = defaultdict(deque)
        self.order_map = {}
        self.best_bids = []
        self.best_asks = []
        self.order_id_counter = itertools.count()
        self.last_price = None

        self.matchers = {
            "fok": FOKOrderMatcher(),
            "ioc": IOCOrderMatcher(),
            "limit": LimitOrderMatcher(),
            "market": MarketOrderMatcher(),
        }

        self.trade_log = TradeLog()

    def add_order(self, order_type, side, qty, price=None):
        oid = next(self.order_id_counter)
        # create order object
        if order_type == "limit":
            order = LimitOrder(oid, side, price, qty)
        elif order_type == "market":
            order = MarketOrder(oid, side, qty)
        elif order_type == "ioc":
            order = IOCOrder(oid, side, price, qty)
        elif order_type == "fok":
            order = FOKOrder(oid, side, price, qty)

        # Execute matching
        self.matchers[order_type].match(self, order)

        return oid

    def best_bid(self):
        return -self.best_bids[0] if self.best_bids else None

    def best_ask(self):
        return self.best_asks[0] if self.best_asks else None

    def get_all_pending_orders(self):
        return list(map(str, self.order_map.values()))

    def cancel_order(self, order_id):
        if order_id not in self.order_map:
            print("Order not found!!")
            return False

        order = self.order_map[order_id]
        queue = self.bids[order.price] if order.is_buy_order() else self.asks[order.price]

        try:
            queue.remove(order)
        except ValueError:
            print(f"[WARN] Order {order_id} not found inside its price level queue.")
            return False

        if not queue:
            if order.is_buy_order():
                self.best_bids.remove(-order.price)
                heapq.heapify(self.best_bids)
            else:
                self.best_asks.remove(order.price)
                heapq.heapify(self.best_asks)

        del self.order_map[order_id]
        return True

    def record_trade(self, price, qty, buy_order, sell_order, aggressor):
        return self.trade_log.record(
            price=price,
            qty=qty,
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
            aggressor=aggressor,
        )
    
    def __str__(self):
        bid_levels = sorted(self.bids.items(), key=lambda x: -x[0])
        ask_levels = sorted(self.asks.items(), key=lambda x: x[0])

        bid_lines = []
        ask_lines = []

        for price, orders in bid_levels:
            total_qty = sum(o.qty for o in orders)
            if total_qty > 0:
                bid_lines.append(f"{price:>5} : {total_qty:<5}")

        for price, orders in ask_levels:
            total_qty = sum(o.qty for o in orders)
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
