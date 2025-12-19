import heapq
from .matcher import Matcher


class LimitOrderMatcher(Matcher):
    def match(self, order_book, order) -> None:
        def leftover(order_book, order):
            if order.is_buy_order():
                order_book.bids[order.price].append(order)
                heapq.heappush(order_book.best_bids, (-order.price, order.timestamp, order.order_id))
            else:
                order_book.asks[order.price].append(order)
                heapq.heappush(order_book.best_asks, (order.price, order.timestamp, order.order_id))
            order_book.order_map[order.order_id] = order

        self._execute_match(
            order_book,
            order,
            price_cmp=lambda p: p <= order.price if order.is_buy_order() else p >= order.price,
            place_leftover_fn=leftover
        )