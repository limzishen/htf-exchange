import heapq
from .matcher import Matcher 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook
from htf_engine.orders.order import Order
from htf_engine.orders.stop_order import StopOrder

# stop price > last traded price - buy
# stop sell < last traded price - sell 
class StopOrderMatcher(Matcher): 
    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, StopOrder):
            raise ValueError("Order and Matcher types do not match!")
        
        if order.is_buy_order():
            if not order_book.last_price or order.stop_price > order_book.last_price:
                order_book.stop_bids[order.stop_price].append(order)
                heapq.heappush(order_book.stop_bids_price, (-order.stop_price, order.timestamp, order.order_id))
            else: 
                raise ValueError("Stop price less than or equal to last traded price")
        
        elif order.is_sell_order():
            if not order_book.last_price or order.stop_price < order_book.last_price:
                order_book.stop_asks[order.stop_price].append(order)
                heapq.heappush(order_book.stop_asks_price, (order.stop_price, order.timestamp, order.order_id))
            else: 
                raise ValueError("Stop price greater than or equal tolast traded price")
            
        order_book.order_map[order.order_id] = order
        