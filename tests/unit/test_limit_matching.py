def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())


class TestLimitOrderOperations:
    def test_add_single_buy_limit(self, ob):
        """Add a single buy limit order to the order book."""
        oid = ob.add_order("limit", "buy", 10, 100)
        assert oid == 0
        assert oid in ob.order_map
        assert ob.best_bid() == 100
        assert ob.best_ask() is None
        assert len(ob.bids[100]) == 1
        assert ob.order_map[oid].qty == 10

    def test_add_single_sell_limit(self, ob):
        """Add a single sell limit order to the order book."""
        oid = ob.add_order("limit", "sell", 10, 100)
        assert oid == 0
        assert oid in ob.order_map
        assert ob.best_bid() is None
        assert ob.best_ask() == 100
        assert len(ob.asks[100]) == 1
        assert ob.order_map[oid].qty == 10

    def test_multiple_orders_same_price_fifo_queue(self, ob):
        """Multiple orders at the same price are queued FIFO."""
        oid1 = ob.add_order("limit", "buy", 10, 100)
        oid2 = ob.add_order("limit", "buy", 20, 100)
        q = ob.bids[100]
        assert q[0].order_id == oid1
        assert q[1].order_id == oid2

    def test_best_bid_with_multiple_levels(self, ob):
        """Best bid updates correctly with multiple price levels."""
        ob.add_order("limit", "buy", 10, 100)
        ob.add_order("limit", "buy", 15, 101)
        ob.add_order("limit", "buy", 5, 99)
        assert ob.best_bid() == 101
        # Add a higher bid
        ob.add_order("limit", "buy", 5, 103)
        assert ob.best_bid() == 103

    def test_best_ask_with_multiple_levels(self, ob):
        """Best ask updates correctly with multiple price levels."""
        ob.add_order("limit", "sell", 10, 105)
        ob.add_order("limit", "sell", 8, 104)
        ob.add_order("limit", "sell", 12, 106)
        assert ob.best_ask() == 104
        # Add a lower ask
        ob.add_order("limit", "sell", 7, 102)
        assert ob.best_ask() == 102  


class TestLimitOrderMatching:
    def test_buy_order_matches_sell_order(self, ob):
        """1 Buy limit order matches existing 1 sell limit order."""
        ob.add_order("limit", "sell", 10, 100)
        ob.add_order("limit", "buy", 10, 100)

        assert _total_resting(ob.asks) == 0
        assert _total_resting(ob.bids) == 0
        assert len(ob.order_map) == 0
        assert ob.last_price == 100
        assert ob.best_bid() is None
        assert ob.best_ask() is None

    def test_buy_partial_fill_leaves_remainder(self, ob):
        """Buy limit order partially fills existing sell limit order, leaving the rest in order book."""
        oid_sell = ob.add_order("limit", "sell", 20, 100)
        ob.add_order("limit", "buy", 10, 100)

        # Sell side should have 10 qty remaining
        assert oid_sell in ob.order_map
        assert ob.order_map[oid_sell].qty == 10
        assert len(ob.asks[100]) == 1
        assert _total_resting(ob.bids) == 0
        assert ob.last_price == 100
    

    def test_sell_partial_fill_leaves_remainder(self, ob):
        """Buy limit order partially fills existing sell limit order, leaving the rest in order book."""
        oid_buy = ob.add_order("limit", "buy", 20, 100)
        ob.add_order("limit", "sell", 10, 100)

        # Buy side should have 10 qty remaining
        assert oid_buy in ob.order_map
        assert ob.order_map[oid_buy].qty == 10
        assert len(ob.bids[100]) == 1
        assert _total_resting(ob.asks) == 0
        assert ob.last_price == 100

    def test_no_match_when_not_crossing(self, ob):
        """Buy limit order does not match when price is below best ask."""
        oid_buy = ob.add_order("limit", "buy", 10, 99)
        ob.add_order("limit", "sell", 10, 100)

        assert oid_buy in ob.order_map
        assert ob.best_bid() == 99
        assert ob.best_ask() == 100
        assert len(ob.bids[99]) == 1
        assert len(ob.asks[100]) == 1
        
    def test_buy_crosses_multiple_matching_ask_levels(self, ob):
        """Test buy order crossing multiple ask price levels."""
        ob.add_order("limit", "sell", 5, 100)
        ob.add_order("limit", "sell", 5, 101)
        ob.add_order("limit", "sell", 5, 102)
        ob.add_order("limit", "sell", 5, 103)
        
        # Buy 13 units at 102, should cross three levels
        oid_buy = ob.add_order("limit", "buy", 13, 102)

        # Incoming buy is fully filled -> should not rest
        assert oid_buy not in ob.order_map

        # Remaining asks: 2 @ 102
        assert sum(o.qty for o in ob.asks[102]) == 2
        assert sum(o.qty for o in ob.asks[103]) == 5

        assert ob.best_ask() == 102
        assert ob.last_price == 102

    def test_sell_crosses_multiple_matching_bid_levels(self, ob):
        """Test sell order crossing multiple bid price levels."""
        ob.add_order("limit", "buy", 5, 103)
        ob.add_order("limit", "buy", 5, 102)
        ob.add_order("limit", "buy", 5, 101)
        ob.add_order("limit", "buy", 5, 100)
        
        # Sell 13 units at 101, should cross three levels
        oid_sell = ob.add_order("limit", "sell", 13, 101)

        # Incoming sell is fully filled -> should not rest
        assert oid_sell not in ob.order_map

        # Remaining bids: 2 @ 101
        assert sum(o.qty for o in ob.bids[101]) == 2
        assert sum(o.qty for o in ob.bids[100]) == 5

        assert ob.best_bid() == 101
        assert ob.last_price == 101

    def test_last_price_tracking(self, ob):
        """Test that last_price is updated on each trade."""
        ob.add_order("limit", "sell", 10, 100)
        ob.add_order("limit", "buy", 10, 100)
        assert ob.last_price == 100
        
        ob.add_order("limit", "sell", 10, 99)
        ob.add_order("limit", "buy", 10, 99)
        assert ob.last_price == 99