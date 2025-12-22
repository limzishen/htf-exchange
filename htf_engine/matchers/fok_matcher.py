from .matcher import Matcher
from typing import TYPE_CHECKING

from htf_engine.errors.exchange_errors.fok_insufficient_liquidity_error import FOKInsufficientLiquidityError
from htf_engine.errors.exchange_errors.matcher_type_mismatch_error import MatcherTypeMismatchError
from htf_engine.orders.order import Order  
from htf_engine.orders.fok_order import FOKOrder

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook


class FOKOrderMatcher(Matcher):
    @property
    def matcher_type(self) -> str:
        return "fok"
    
    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, FOKOrder):
            raise MatcherTypeMismatchError(order.order_type, self.matcher_type)

        # Simulate available quantity first
        book = order_book.asks if order.is_buy_order() else order_book.bids
        price_cmp = lambda p: p <= order.price if order.is_buy_order() else p >= order.price
        
        available_qty = sum(
            sum(o.qty for o in orders)
            for price, orders in book.items()
            if price_cmp(price)
        )

        if available_qty < order.qty:
            order_book.cleanup_discarded_order(order)
            raise FOKInsufficientLiquidityError()

        self._execute_match(
            order_book,
            order,
            price_cmp=price_cmp
        )