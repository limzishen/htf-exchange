def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())


class TestOrderCancellation:
    def test_cancel_single_pending_order(self, ob):
        """Canceling a single resting order adds it to the cancelled set."""
        oid = ob.add_order("limit", "buy", 10, 100)
        assert ob.cancel_order(oid) is True
        assert oid in ob.cancelled_orders
        assert ob.best_bid() is None
        assert _total_resting(ob.bids) == 0

    def test_cancel_order_is_removed_from_canceled_order(self, ob):
        """Canceling a single resting order removes it from the cancelled set."""
        oid = ob.add_order("limit", "buy", 10, 100)
        assert ob.cancel_order(oid) is True
        assert oid in ob.cancelled_orders
        assert ob.best_bid() is None
        assert oid not in ob.cancelled_orders
        assert _total_resting(ob.bids) == 0

    def test_cancel_non_existent_order_returns_false(self, ob):
        """Canceling an unknown order id should return False."""
        assert ob.cancel_order(999) is False

    def test_cancel_middle_of_fifo_queue_preserves_order(self, ob):
        """Canceling a middle order preserves FIFO order of remaining orders and order is not removed"""
        oid1 = ob.add_order("limit", "buy", 10, 100)
        oid2 = ob.add_order("limit", "buy", 20, 100)
        oid3 = ob.add_order("limit", "buy", 30, 100)

        assert ob.cancel_order(oid2) is True
        oid4 = ob.add_order("limit", "buy", 40, 100)

        q = ob.bids[100]
        assert len(q) == 4
        assert q[0].order_id == oid1
        assert q[1].order_id == oid2
        assert q[2].order_id == oid3
        assert q[3].order_id == oid4
        assert oid2 in ob.order_map

    def test_order_is_removed_in_correct_sequence(self, ob):
        """Canceling an order and ensuring the heap and queue order match"""
        oid1 = ob.add_order("limit", "buy", 10, 100)
        oid2 = ob.add_order("limit", "buy", 10, 100)
        assert ob.bids[100][0].order_id == oid1
        assert ob.bids[100][1].order_id == oid2
        assert ob.cancel_order(oid1) is True
        assert oid1 in ob.cancelled_orders

        best_bid_price = ob.best_bid()
        assert best_bid_price == 100
        assert len(ob.bids[100]) == 1
        assert ob.bids[100][0].order_id == oid2



    def test_cancel_last_order_at_price_level_updates_best_price(self, ob):
        """Canceling the last order at a price level updates best bid/ask."""
        oid1 = ob.add_order("limit", "buy", 10, 100)
        ob.add_order("limit", "buy", 20, 99)

        ob.cancel_order(oid1)

        assert ob.best_bid() == 99
        assert sum(o.qty for o in ob.bids[100]) == 0
        assert _total_resting(ob.bids) == 1

    def test_cancel_all_orders_clears_book(self, ob):
        """Canceling all resting orders leaves the book empty."""
        ids = [
            ob.add_order("limit", "buy", 10, 100),
            ob.add_order("limit", "buy", 20, 99),
            ob.add_order("limit", "sell", 10, 101),
        ]

        for oid in ids:
            assert ob.cancel_order(oid) is True
        assert ob.best_ask() is None
        assert ob.best_bid() is None
        assert len(ob.order_map) == 0
        assert _total_resting(ob.bids) == 0
        assert _total_resting(ob.asks) == 0

    def test_cancel_order_after_partial_fill(self, ob):
        """An order partially filled by matching can still be cancelled."""
        oid_sell = ob.add_order("limit", "sell", 20, 100)
        ob.add_order("limit", "buy", 10, 100)  # partial fill, 10 remains

        assert oid_sell in ob.order_map
        assert ob.order_map[oid_sell].qty == 10

        assert ob.cancel_order(oid_sell) is True
        assert ob.best_ask() is None
        assert oid_sell not in ob.order_map
        assert _total_resting(ob.asks) == 0


    def test_cancel_does_not_affect_other_side(self, ob):
        """Canceling bids should not affect resting asks (and vice versa)."""
        bid_id = ob.add_order("limit", "buy", 10, 100)
        ask_id = ob.add_order("limit", "sell", 10, 105)

        ob.cancel_order(bid_id)

        assert ob.best_bid() is None
        assert bid_id not in ob.order_map
        assert ask_id in ob.order_map
        assert _total_resting(ob.bids) == 0
        assert _total_resting(ob.asks) == 1
        assert ob.best_ask() == 105
