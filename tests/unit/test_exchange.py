from collections import defaultdict
import pytest

from htf_engine.errors.exchange_errors.permission_denied_error import PermissionDeniedError


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
        exchange.register_user(u2, 2)
        exchange.register_user(u3, 3)

        assert len(exchange.users) == 3
        assert exchange.users[u1.user_id] is u1
        assert exchange.users[u2.user_id] is u2
        assert exchange.users[u3.user_id] is u3
        assert exchange.fee == 10
        assert exchange.balance == 0

    def test_L1_L2_L3_permissions(self, exchange, u1, u2, u3):
        # Register users
        exchange.register_user(u1)
        exchange.register_user(u2, permission_level=2)
        exchange.register_user(u3, permission_level=3)

        inst = "Stock A"

        # --- L1: Everyone can access ---
        for user in [u1, u2, u3]:
            data = exchange.get_L1_data(user.user_id, inst)
            assert "best_bid" in data
            assert "best_ask" in data
            assert "last_price" in data

        # --- L2: Only permission >=2 can access ---
        # u1 should fail
        with pytest.raises(PermissionDeniedError) as e1:
            exchange.get_L2_data(u1.user_id, inst)
            
        assert str(e1.value) == "[PERMISSION_DENIED] User 'ceo_of_fumbling' does not have sufficient permissions (required=2, actual=1)."

        # u2 should succeed
        data2 = exchange.get_L2_data(u2.user_id, inst)
        assert "bids" in data2
        assert "asks" in data2

        # u3 should succeed
        data3 = exchange.get_L2_data(u3.user_id, inst)
        assert "bids" in data3
        assert "asks" in data3

        # --- L3: Only permission >=3 can access ---
        # u1 fails
        with pytest.raises(PermissionDeniedError) as e1:
            exchange.get_L3_data(u1.user_id, inst)

        assert str(e1.value) == "[PERMISSION_DENIED] User 'ceo_of_fumbling' does not have sufficient permissions (required=3, actual=1)."

        # u2 fails
        with pytest.raises(PermissionDeniedError) as e2:
            exchange.get_L3_data(u2.user_id, inst)

        assert str(e2.value) == "[PERMISSION_DENIED] User 'cheater6767' does not have sufficient permissions (required=3, actual=2)."

        # u3 succeeds
        data3 = exchange.get_L3_data(u3.user_id, inst)
        assert "bids" in data3
        assert "asks" in data3
        for side in ["bids", "asks"]:
            for level in data3[side]:
                assert "price" in level
                for order in level["orders"]:
                    assert "order_id" in order
                    assert "qty" in order
                    assert "user_id" in order
                    assert "order_type" in order
                    assert "timestamp" in order
