import heapq
from .matcher import Matcher 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook
    from htf_engine.orders.order import Order

# stop price > last traded price - buy 
# stop sell < last traded price - sell 
class StopOrderMatcher(Matcher): 
    def match(self, order_book: "OrderBook", order: "Order") -> None:
        if order.is_buy_order():
            if order.stop_price >  order_book.last_price:
                order_book.stop_bids[order.stop_price].append(order)
                heapq.heappush(order_book.stop_bids, (-order.stop_price, order.timestamp, order.order_id))
            else: 
                raise ValueError(f"Stop price less the last traded price")
        
        elif order.is_sell_order():
            if order.stop_price <  order_book.last_price:
                order_book.stop_asks[order.stop_price].append(order)
                heapq.heappush(order_book.stop_asks, (order.stop_price, order.timestamp, order.order_id))
            else: 
                raise ValueError(f"Stop price greater the last traded price")
        order_book.order_map[order.order_id] = order