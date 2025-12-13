from collections import defaultdict, deque
import heapq
import itertools
from .matchers.limit_matcher import LimitOrderMatcher
from .matchers.market_matcher import MarketOrderMatcher
from .orders.limit_order import LimitOrder
from .orders.market_order import MarketOrder
# dirty flag oid
# cleaning dirty flag;

# remove in (matching)
# remove from bids
# remove from asks

# remove in best_bid() and best_ask()
# remove from best_bids
# remove from best_ask
# remove in order_map

# further optimization
# somehow remove the cancelled trades from the set

# Pending fix
# all pending orders
class OrderBook:
    def __init__(self):
        self.bids = defaultdict(deque) # {order price: deque[order....] }
        self.asks = defaultdict(deque)
        self.order_map = {} # {oid: order}
        self.best_bids = [] # (order price, oid)
        self.best_asks = [] # (order price, oid)
        self.order_id_counter = itertools.count()
        self.last_price = None
        self.cancelled_orders = set()

        self.matchers = {
            "limit": LimitOrderMatcher(),
            "market": MarketOrderMatcher()
        }

    def add_order(self, order_type, side, qty, price=None):
        oid = next(self.order_id_counter)
        # create order object
        if order_type == "limit":
            order = LimitOrder(oid, side, price, qty)
        elif order_type == "market":
            order = MarketOrder(oid, side, qty)
        # elif order_type == "ioc":
        #     TODO
        # elif order_type == "fok":
        #     TODO

        # Execute matching first
        self.matchers[order_type].match(self, order)

        # Add remaining resting quantity to the book if needed (eg limit order)
        if order_type in ("limit",) and order.qty > 0:
            if order.is_buy_order():
                self.bids[order.price].append(order)
                heapq.heappush(self.best_bids, (-order.price, oid))
            else:
                self.asks[order.price].append(order)
                heapq.heappush(self.best_asks, (order.price, oid))
            self.order_map[oid] = order

        return oid

    def clean_orders(self, order_heap, queue_dict):
        while order_heap and order_heap[0][1] in self.cancelled_orders:
            if queue_dict == self.bids:
                order_price, oid_to_clean = -order_heap[0][0], order_heap[0][1]
            else:
                order_price, oid_to_clean = order_heap[0]
            removed_order = queue_dict[order_price].popleft()

            if oid_to_clean in self.order_map:
                del self.order_map[oid_to_clean]
            heapq.heappop(order_heap)
            self.cancelled_orders.remove(oid_to_clean)
            print(f"{removed_order.order_id} removed from queue, {oid_to_clean} removed from heap")


    def best_bid(self):
        self.clean_orders(self.best_bids, self.bids)
        return -self.best_bids[0][0] if self.best_bids else None

    def best_ask(self):
        self.clean_orders(self.best_asks, self.asks)
        return self.best_asks[0][0] if self.best_asks else None

    def get_all_pending_orders(self):
        return [str(v) for v in self.order_map.values() if v.order_id not in self.cancelled_orders]

    def cancel_order(self, order_id):
        if order_id in self.order_map:
            self.cancelled_orders.add(order_id)
            return True
        print("Order not found!!")
        return False

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
