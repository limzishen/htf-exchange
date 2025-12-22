import heapq
from .matcher import Matcher 
from typing import TYPE_CHECKING

from htf_engine.errors.exchange_errors.invalid_stop_price_error import InvalidStopPriceError
from htf_engine.errors.exchange_errors.matcher_type_mismatch_error import MatcherTypeMismatchError
from htf_engine.orders.order import Order
from htf_engine.orders.stop_order import StopOrder

if TYPE_CHECKING:
    from htf_engine.order_book import OrderBook


class StopOrderMatcher(Matcher): 
    @property
    def matcher_type(self) -> str:
        return "stop"
    
    def match(self, order_book: "OrderBook", order: Order) -> None:
        if not isinstance(order, StopOrder):
            raise MatcherTypeMismatchError(order.order_type, self.matcher_type)
        
        if order.is_buy_order():
            if not order_book.last_price or order.stop_price > order_book.last_price:
                order_book.stop_bids[order.stop_price].append(order)

                heapq.heappush(
                    order_book.stop_bids_price,
                    (-order.stop_price, order.timestamp, order.order_id)
                )
            else: 
                raise InvalidStopPriceError(is_buy_order=True)
        
        elif order.is_sell_order():
            if not order_book.last_price or order.stop_price < order_book.last_price:
                order_book.stop_asks[order.stop_price].append(order)

                heapq.heappush(
                    order_book.stop_asks_price,
                    (order.stop_price, order.timestamp, order.order_id)
                )
            else: 
                raise InvalidStopPriceError(is_buy_order=False)
            
        order_book.order_map[order.order_id] = order
        