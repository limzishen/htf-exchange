import heapq
from Matcher import Matcher

class LimitOrderMatcher(Matcher):
    def match(self, order_book, order):
        if order.is_buy_order():
            best_prices_heap = order_book.best_asks
            book = order_book.asks
            price_cmp = lambda best_price: best_price <= order.price
        else:
            best_prices_heap = order_book.best_bids
            book = order_book.bids
            price_cmp = lambda best_price: best_price >= order.price

        while order.qty > 0 and best_prices_heap:
            best_price = best_prices_heap[0] if order.is_buy_order() else -best_prices_heap[0]
            if not price_cmp(best_price):
                break

            resting_order = book[best_price][0]
            traded_qty = min(order.qty, resting_order.qty)
            order.qty -= traded_qty
            resting_order.qty -= traded_qty

            trade_price = resting_order.price
            print(f"TRADE {traded_qty} @ {trade_price}")
            order_book.last_price = trade_price

            if resting_order.qty == 0:
                book[best_price].popleft()
                del order_book.order_map[resting_order.order_id]

                if not book[best_price]:  # only pop heap if price level empty
                    del book[best_price]
                    heapq.heappop(best_prices_heap)
