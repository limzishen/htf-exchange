from collections import defaultdict, deque
import heapq
import itertools
from LimitMatcher import LimitOrderMatcher
from LimitOrder import LimitOrder

class OrderBook:
    def __init__(self):
        self.bids = defaultdict(deque)
        self.asks = defaultdict(deque)
        self.order_map = {}
        self.best_bids = []
        self.best_asks = []
        self.order_id_counter = itertools.count()

        self.matchers = {
            "limit": LimitOrderMatcher()
        }

    def _add_to_book(self, order):
        """Add a resting order (limit/IOC/FOK) to the book without matching yet."""
        if order.side == "buy":
            self.bids[order.price].append(order)
            heapq.heappush(self.best_bids, -order.price)
        else:
            self.asks[order.price].append(order)
            heapq.heappush(self.best_asks, order.price)

    def add_order(self, order_type, side, qty, price=None):
        oid = next(self.order_id_counter)
        # create order object
        if order_type == "limit":
            order = LimitOrder(oid, side, price, qty)
        # elif order_type == "market":
        #     order = MarketOrder(oid, side, qty)
        # elif order_type == "ioc":
        #     order = IOCOrder(oid, side, price, qty)
        # elif order_type == "fok":
        #     order = FOKOrder(oid, side, price, qty)

        # Execute matching first
        self.matchers[order_type].match(self, order)

        # Add remaining resting quantity to the book if needed
        if order_type in ("limit", "ioc", "fok") and order.qty > 0:
            self._add_to_book(order)
            self.order_map[oid] = order

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
        queue = self.bids[order.price] if order.side == "buy" else self.asks[order.price]

        try:
            queue.remove(order)
        except ValueError:
            pass

        if not queue:
            if order.side == "buy":
                self.best_bids.remove(-order.price)
                heapq.heapify(self.best_bids)
            else:
                self.best_asks.remove(order.price)
                heapq.heapify(self.best_asks)

        del self.order_map[order_id]
        return True

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
