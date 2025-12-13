import heapq
from .matcher import Matcher


class MarketOrderMatcher(Matcher):
    def match(self, order_book, order):
        if order.is_buy_order():
            best_prices_heap = order_book.best_asks
            book = order_book.asks
        else:
            best_prices_heap = order_book.best_bids
            book = order_book.bids

        while order.qty > 0 and best_prices_heap:
            order_book.clean_orders(best_prices_heap, book)
            best_price = best_prices_heap[0][0] if order.is_buy_order() else -best_prices_heap[0][0]

            resting_order = book[best_price][0]  # first order in deque
            traded_qty = min(order.qty, resting_order.qty)
            order.qty -= traded_qty
            resting_order.qty -= traded_qty

            trade_price = resting_order.price
            print(f"TRADE {traded_qty} @ {trade_price}")
            order_book.last_price = trade_price

            if resting_order.qty == 0:
                # full order destroyed
                book[best_price].popleft()
                del order_book.order_map[resting_order.order_id]

                # pop one duplicate for this full order
                heapq.heappop(best_prices_heap)

                if not book[best_price]:  # no more orders at this price
                    del book[best_price]
