import heapq
from .matcher import Matcher


class IOCOrderMatcher(Matcher):
    def match(self, order_book, order) -> None:
        self._execute_match(
            order_book,
            order,
            price_cmp=lambda p: p <= order.price if order.is_buy_order() else p >= order.price,
            place_leftover_fn=lambda ob, o: ob.cleanup_discarded_order(o)
        )