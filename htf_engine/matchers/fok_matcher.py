import heapq
from .matcher import Matcher


class FOKOrderMatcher(Matcher):
    def match(self, order_book, order):
        if order.is_buy_order():
            best_prices_heap = order_book.best_asks
            book = order_book.asks
            price_cmp = lambda best_price: best_price <= order.price
        else:
            best_prices_heap = order_book.best_bids
            book = order_book.bids
            price_cmp = lambda best_price: best_price >= order.price

        # Simulate fill
        available_qty = 0
        for price in sorted(book.keys(), reverse=order.is_sell_order()):
            if not price_cmp(price):
                break
            level_qty = sum(o.qty for o in book[price])
            available_qty += level_qty
            if available_qty >= order.qty:
                break

        if available_qty < order.qty:
            print(f"FOK order {order.order_id} cancelled due to insufficient liquidity")
            return

        while order.qty > 0 and best_prices_heap:
            order_book.clean_orders(best_prices_heap, book)
            best_price = best_prices_heap[0][0] if order.is_buy_order() else -best_prices_heap[0][0]
            
            if not price_cmp(best_price): # by right this should never run, since we checked that theres enough liquidity
                break

            resting_order = book[best_price][0]  # first order in deque
            traded_qty = min(order.qty, resting_order.qty)
            order.qty -= traded_qty
            resting_order.qty -= traded_qty

            trade_price = resting_order.price

            if order.is_buy_order():
                order_book.record_trade(
                    price=best_price,
                    qty=traded_qty,
                    buy_order=order,
                    sell_order=resting_order,
                    aggressor="buy",
                )
            else:
                order_book.record_trade(
                    price=best_price,
                    qty=traded_qty,
                    buy_order=resting_order,
                    sell_order=order,
                    aggressor="sell",
                )
            
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
