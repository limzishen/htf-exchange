import heapq
from .matcher import Matcher

class MarketOrderMatcher(Matcher):
    def match(self, order_book, order) -> None:
        self._execute_match(
            order_book,
            order,
            place_leftover_fn=lambda ob, o: ob.cleanup_discarded_order(o)
        )