def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())


class TestOrderCancellation:
    def test_cancel_single_pending_order(self, ob):
        """Cancel a single pending order."""
        oid = ob.add_order("limit", "buy", 10, 100)

        assert ob.cancel_order(oid) is True
        assert oid not in ob.order_map
        assert len(ob.bids[100]) == 0
        assert ob.best_bid() is None
        assert _total_resting(ob.bids) == 0

    def test_cancel_order_not_found(self, ob):
        """Attempt to cancel a non-existent order."""
        assert ob.cancel_order(999) is False

    def test_cancel_middle_of_queue_preserves_order(self, ob):
        """Cancel an order in the middle of a same-price queue."""
        oid1 = ob.add_order("limit", "buy", 10, 100)
        oid2 = ob.add_order("limit", "buy", 20, 100)
        oid3 = ob.add_order("limit", "buy", 30, 100)

        assert ob.cancel_order(oid2) is True

        q = ob.bids[100]
        assert len(q) == 2
        assert q[0].order_id == oid1
        assert q[1].order_id == oid3
        assert oid2 not in ob.order_map
    
    def test_cancel_last_order_at_price_level_removes_level(self, ob):
        """Canceling last order at a level removes it from best heap (not necessarily dict key)."""
        oid1 = ob.add_order("limit", "buy", 10, 100)
        ob.add_order("limit", "buy", 20, 99)

        ob.cancel_order(oid1)

        assert ob.best_bid() == 99
        assert len(ob.bids[100]) == 0    
        assert _total_resting(ob.bids) == 1


    def test_cancel_all_orders_clears_book(self, ob):
        """Canceling all orders leaves no resting orders."""
        ids = [
            ob.add_order("limit", "buy", 10, 100),
            ob.add_order("limit", "buy", 20, 99),
            ob.add_order("limit", "sell", 10, 101),
        ]

        for oid in ids:
            ob.cancel_order(oid)

        assert len(ob.order_map) == 0
        assert _total_resting(ob.bids) == 0 
        assert _total_resting(ob.asks) == 0 
        assert ob.best_bid() is None
        assert ob.best_ask() is None
    

