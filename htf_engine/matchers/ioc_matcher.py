import heapq
from .matcher import Matcher
from typing import TYPE_CHECKING

from htf_engine.orders.order import Order  
from htf_engine.orders.ioc_order import IOCOrder

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook


class IOCOrderMatcher(Matcher):
    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, IOCOrder):
            raise ValueError("Order and Matcher types do not match!")
    
        self._execute_match(
            order_book,
            order,
            price_cmp=lambda p: p <= order.price if order.is_buy_order() else p >= order.price,
            place_leftover_fn=lambda ob, o: ob.cleanup_discarded_order(o)
        )