import heapq
class Matcher:

    """Base class for all matchers."""

    def match(self, order_book, order) -> None:
        raise NotImplementedError
    
    def _execute_match(
        self,
        order_book,
        order,
        price_cmp=lambda best_price: True, 
        place_leftover_fn=None
    ) -> None:
        """
        Core matching loop:
        - price_cmp: function to decide if a resting price can be traded
        - place_leftover_fn: function to handle leftover order if qty > 0
        """
        if self._would_self_trade(order_book, order, price_cmp):
            print(f"STP triggered: cancelling order {order.order_id}")
            order_book.cleanup_discarded_order(order)
            raise ValueError(f"STP triggered: cancelling order {order.order_id} from User {order.user_id}")

        if order.is_buy_order():
            best_prices_heap = order_book.best_asks
            book = order_book.asks
        else:
            best_prices_heap = order_book.best_bids
            book = order_book.bids

        while order.qty > 0 and best_prices_heap:
            order_book.clean_orders(best_prices_heap, book)

            best_price = best_prices_heap[0][0] if order.is_buy_order() else -best_prices_heap[0][0]

            if not price_cmp(best_price):
                break

            resting_order = book[best_price][0]
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
                book[best_price].popleft()
                del order_book.order_map[resting_order.order_id]
                heapq.heappop(best_prices_heap)
                if not book[best_price]:
                    del book[best_price]

        if order.qty > 0 and place_leftover_fn:
            place_leftover_fn(order_book, order)

    def _would_self_trade(self, order_book, incoming_order, price_cmp) -> bool:
        if not order_book.enable_stp:
            return False
        
        if incoming_order.is_buy_order():
            if not order_book.best_asks:
                return False
            book = order_book.asks
            prices = sorted(book.keys())
        else:
            if not order_book.best_bids:
                return False
            book = order_book.bids
            prices = sorted(book.keys(), reverse=True)

        remaining = incoming_order.qty

        for price in prices:
            if not price_cmp(price):
                break

            for resting in book[price]:
                if resting.user_id == incoming_order.user_id:
                    return True  # 🚨 STP violation

                remaining -= resting.qty
                if remaining <= 0:
                    return False

        return False
