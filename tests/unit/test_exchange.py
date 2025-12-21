from collections import defaultdict


class TestExchange:
    def _nice_snapshot(self, ob):
        snap = ob.snapshot()
        bids = defaultdict(int)
        asks = defaultdict(int)

        for price, orders in snap['bids']:
            bids[price] = sum(o[3] for o in orders)  # o[3] is qty
        for price, orders in snap['asks']:
            asks[price] = sum(o[3] for o in orders)
        
        return bids, asks, snap['last_price'], snap['last_quantity']
        
    def test_exchange(self, exchange, u1, u2, u3):
        assert "Stock A" in exchange.order_books
        ob_A = exchange.order_books["Stock A"]
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob_A)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price is None
        assert last_quantity is None
        assert ob_A.on_trade_callback is not None
        assert ob_A.cleanup_discarded_order_callback is not None

        assert "Stock B" in exchange.order_books
        ob_B = exchange.order_books["Stock B"]
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob_B)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price is None
        assert last_quantity is None
        assert ob_B.on_trade_callback is not None
        assert ob_B.cleanup_discarded_order_callback is not None

        assert "Stock C" in exchange.order_books
        ob_C = exchange.order_books["Stock C"]
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob_C)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price is None
        assert last_quantity is None
        assert ob_C.on_trade_callback is not None
        assert ob_C.cleanup_discarded_order_callback is not None

        # Register 3 users
        exchange.register_user(u1)
        exchange.register_user(u2)
        exchange.register_user(u3)

        assert len(exchange.users) == 3
        assert exchange.users[u1.user_id] is u1
        assert exchange.users[u2.user_id] is u2
        assert exchange.users[u3.user_id] is u3
        assert exchange.fee == 10
        assert exchange.balance == 0

        