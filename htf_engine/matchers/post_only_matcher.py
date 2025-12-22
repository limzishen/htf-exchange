import heapq
from .matcher import Matcher
from typing import TYPE_CHECKING

from htf_engine.errors.exchange_errors.matcher_type_mismatch_error import MatcherTypeMismatchError
from htf_engine.errors.exchange_errors.post_only_violation_error import PostOnlyViolationError
from htf_engine.orders.order import Order  
from htf_engine.orders.post_only_order import PostOnlyOrder

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook


class PostOnlyOrderMatcher(Matcher):
    @property
    def matcher_type(self) -> str:
        return "post-only"

    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, PostOnlyOrder):
            raise MatcherTypeMismatchError(order.order_type, self.matcher_type)
        
        # Check if the incoming order matches existing orders
        if order.is_buy_order():
            if order_book.best_asks:
                best_ask = order_book.best_asks[0][0]
                if order.price >= best_ask:
                    order_book.cleanup_discarded_order(order)
                    raise PostOnlyViolationError()
        else:
            if order_book.best_bids:
                best_bid = -order_book.best_bids[0][0]
                if order.price <= best_bid:
                    order_book.cleanup_discarded_order(order)
                    raise PostOnlyViolationError()
        
        def leftover(order_book: "OrderBook", order: Order):
            if not isinstance(order, PostOnlyOrder):
                raise MatcherTypeMismatchError(order.order_type, self.matcher_type)
            
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
            price_cmp=lambda p: False,  # The loop shouldn't run. (We can use the price_cmp function from limitorder, but it will eval to False anyway)
            place_leftover_fn=leftover
        )
        