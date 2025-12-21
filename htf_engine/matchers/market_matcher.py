from .matcher import Matcher
from typing import TYPE_CHECKING

from htf_engine.orders.market_order import MarketOrder
from htf_engine.orders.order import Order

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook


class MarketOrderMatcher(Matcher):
    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, MarketOrder):
            raise ValueError("Order and Matcher types do not match!")
        
        self._execute_match(
            order_book,
            order,
            place_leftover_fn=lambda ob, o: ob.cleanup_discarded_order(o)
        )