def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())


class TestMarketOrderMatching:
    def test_market_buy_consumes_available_asks(self, ob):
        """Market buy order consumes existing sell limit order fully."""
        ob.add_order("limit", "sell", 10, 100)
        oid = ob.add_order("market", "buy", 10)

        # market orders do not rest
        assert oid not in ob.order_map
        assert _total_resting(ob.asks) == 0
        assert ob.last_price == 100

    def test_market_buy_insufficient_liquidity_does_not_rest(self, ob):
        """Market buy with insufficient ask liquidity consumes what it can and does not rest."""
        ob.add_order("limit", "sell", 5, 100)
        oid = ob.add_order("market", "buy", 10)
        
        assert oid not in ob.order_map
        # All asks consumed
        assert _total_resting(ob.asks) == 0
        assert ob.best_ask() is None

        # Trade happened at 100
        assert ob.last_price == 100


    def test_market_sell_insufficient_liquidity_does_not_rest(self, ob):
        """Market sell with insufficient bid liquidity consumes what it can and does not rest."""
        ob.add_order("limit", "buy", 5, 100)
        oid = ob.add_order("market", "sell", 10)

        assert oid not in ob.order_map
        # All bids consumed
        assert _total_resting(ob.bids) == 0
        assert ob.best_bid() is None

        # Trade happened at 100
        assert ob.last_price == 100

    def test_market_order_no_liquidity(self, ob):
        """Market order when no liquidity exists does not rest."""
        oid = ob.add_order("market", "buy", 10)
        assert oid not in ob.order_map
        assert _total_resting(ob.asks) == 0
        assert _total_resting(ob.bids) == 0
        assert ob.last_price is None
    
    def test_market_buy_crosses_multiple_price_levels(self, ob):
        """Market buy sweeps multiple ask levels; remainder does not rest."""
        ob.add_order("limit", "sell", 5, 100)
        ob.add_order("limit", "sell", 5, 101)
        ob.add_order("limit", "sell", 5, 102)
        ob.add_order("limit", "sell", 5, 103)

        oid_market = ob.add_order("market", "buy", 13)

        assert oid_market not in ob.order_map

        # Expected: 5@100 + 5@101 + 3@102, leaving 2@102 and all of 103 untouched
        assert sum(o.qty for o in ob.asks[102]) == 2
        assert sum(o.qty for o in ob.asks[103]) == 5

        # Best ask should now be 102 (since 100/101 are cleared)
        assert ob.best_ask() == 102
        # Last traded price should be the last level it hit
        assert ob.last_price == 102
        # Total resting asks: 2 (at 102) + 5 (at 103) = 7
        assert _total_resting(ob.asks) == 2  # number of resting ask orders
        assert sum(o.qty for q in ob.asks.values() for o in q) == 7  # total resting ask qty


    def test_market_sell_crosses_multiple_price_levels(self, ob):
        """Market sell sweeps multiple bid levels; remainder does not rest."""
        ob.add_order("limit", "buy", 5, 100)
        ob.add_order("limit", "buy", 5, 99)
        ob.add_order("limit", "buy", 5, 98)

        oid_market = ob.add_order("market", "sell", 13)

        assert oid_market not in ob.order_map

        # Expected: 5@100 + 5@99 + 3@98, leaving 2@98
        assert sum(o.qty for o in ob.bids[98]) == 2
        assert ob.best_bid() == 98
        # Last traded price should be the last level it hit
        assert ob.last_price == 98
        # Total resting bid qty should be 2
        assert sum(o.qty for q in ob.bids.values() for o in q) == 2

    