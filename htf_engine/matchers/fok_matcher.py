from .matcher import Matcher
from typing import TYPE_CHECKING

from htf_engine.orders.order import Order  
from htf_engine.orders.fok_order import FOKOrder

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook


class FOKOrderMatcher(Matcher):
    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, FOKOrder):
            raise ValueError("Order and Matcher types do not match!")

        # Simulate available quantity first
        book = order_book.asks if order.is_buy_order() else order_book.bids
        price_cmp = lambda p: p <= order.price if order.is_buy_order() else p >= order.price
        
        available_qty = sum(
            sum(o.qty for o in orders)
            for price, orders in book.items()
            if price_cmp(price)
        )

        if available_qty < order.qty:
            print(f"FOK order {order.order_id} cancelled due to insufficient liquidity")
            order_book.cleanup_discarded_order(order)
            raise ValueError(f"Insufficient Liquidity for FOK order: cancelling order {order.order_id} from User {order.user_id}")

        self._execute_match(
            order_book,
            order,
            price_cmp=price_cmp
        )