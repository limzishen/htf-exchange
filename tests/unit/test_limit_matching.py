def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())


class TestLimitOrderOperations:
    def test_add_single_buy_limit(self, ob):
        """Add a single buy limit order to the order book."""
        oid = ob.add_order("limit", "buy", 10, 100)
        assert oid in ob.order_map
        assert ob.best_bid() == 100
        assert ob.best_ask() is None
        assert len(ob.bids[100]) == 1
        assert ob.order_map[oid].qty == 10

    def test_add_single_sell_limit(self, ob):
        """Add a single sell limit order to the order book."""
        oid = ob.add_order("limit", "sell", 10, 100)
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
    def test_full_match_clears_book(self, ob):
        """Buy and sell at same price fully match, nothing rests."""
        ob.add_order("limit", "sell", 10, 100)
        ob.add_order("limit", "buy", 10, 100)

        assert _total_resting(ob.asks) == 0
        assert _total_resting(ob.bids) == 0
        assert len(ob.order_map) == 0
        assert ob.last_price == 100
        assert ob.best_bid() is None
        assert ob.best_ask() is None

    def test_partial_fill_leaves_remainder_on_ask(self, ob):
        """Buy partially fills an ask; remainder stays on ask side."""
        oid_sell = ob.add_order("limit", "sell", 20, 100)
        ob.add_order("limit", "buy", 10, 100)

        assert oid_sell in ob.order_map
        assert ob.order_map[oid_sell].qty == 10
        assert sum(o.qty for o in ob.asks[100]) == 10
        assert _total_resting(ob.bids) == 0
        assert ob.best_ask() == 100
        assert ob.last_price == 100

    def test_partial_fill_leaves_remainder_on_bid(self, ob):
        """Sell partially fills a bid; remainder stays on bid side."""
        oid_buy = ob.add_order("limit", "buy", 20, 100)
        ob.add_order("limit", "sell", 10, 100)

        assert oid_buy in ob.order_map
        assert ob.order_map[oid_buy].qty == 10
        assert sum(o.qty for o in ob.bids[100]) == 10
        assert _total_resting(ob.asks) == 0
        assert ob.best_bid() == 100
        assert ob.last_price == 100

    def test_no_match_when_prices_do_not_cross(self, ob):
        """No trade when buy price is below best ask; both orders rest."""
        oid_buy = ob.add_order("limit", "buy", 10, 99)
        oid_sell = ob.add_order("limit", "sell", 10, 100)

        assert oid_buy in ob.order_map
        assert oid_sell in ob.order_map
        assert ob.best_bid() == 99
        assert ob.best_ask() == 100
        assert sum(o.qty for o in ob.bids[99]) == 10
        assert sum(o.qty for o in ob.asks[100]) == 10
        assert ob.last_price is None

    def test_buy_crosses_multiple_ask_levels_up_to_limit(self, ob):
        """Buy crosses multiple ask levels up to its limit price and does not touch higher asks."""
        ob.add_order("limit", "sell", 5, 100)
        ob.add_order("limit", "sell", 5, 101)
        ob.add_order("limit", "sell", 5, 102)
        ob.add_order("limit", "sell", 5, 103)

        oid_buy = ob.add_order("limit", "buy", 13, 102)  # fills 5@100 + 5@101 + 3@102

        # Incoming buy fully filled -> should not rest
        assert oid_buy not in ob.order_map

        # Remaining asks: 2@102 and 5@103 (103 untouched)
        assert sum(o.qty for o in ob.asks[102]) == 2
        assert sum(o.qty for o in ob.asks[103]) == 5
        assert ob.best_ask() == 102
        assert ob.last_price == 102

    def test_sell_crosses_multiple_bid_levels_down_to_limit(self, ob):
        """Sell crosses multiple bid levels down to its limit price and does not touch lower bids."""
        ob.add_order("limit", "buy", 5, 103)
        ob.add_order("limit", "buy", 5, 102)
        ob.add_order("limit", "buy", 5, 101)
        ob.add_order("limit", "buy", 5, 100)

        oid_sell = ob.add_order("limit", "sell", 13, 101)  # fills 5@103 + 5@102 + 3@101

        # Incoming sell fully filled -> should not rest
        assert oid_sell not in ob.order_map

        # Remaining bids: 2@101 and 5@100 (100 untouched)
        assert sum(o.qty for o in ob.bids[101]) == 2
        assert sum(o.qty for o in ob.bids[100]) == 5
        assert ob.best_bid() == 101
        assert ob.last_price == 101

    def test_crossing_buy_sweeps_asks_and_rests_remainder(self, ob):
        """Crossing buy consumes all asks it can and rests remaining qty at its limit price."""
        ob.add_order("limit", "buy", 5, 100)
        ob.add_order("limit", "buy", 3, 99)
        ob.add_order("limit", "sell", 4, 105)
        ob.add_order("limit", "sell", 2, 110)

        oid_buy = ob.add_order("limit", "buy", 20, 110)  # consumes 4@105 + 2@110 => 6 filled

        assert ob.best_ask() is None
        assert ob.best_bid() == 110
        assert oid_buy in ob.order_map
        assert ob.order_map[oid_buy].qty == 14
        assert sum(o.qty for o in ob.bids[110]) == 14
        assert ob.last_price == 110  # last fill occurred at 110

    def test_last_price_updates_on_newer_trades(self, ob):
        """last_price should reflect the most recent trade price."""
        ob.add_order("limit", "sell", 10, 100)
        ob.add_order("limit", "buy", 10, 100)
        assert ob.last_price == 100

        ob.add_order("limit", "sell", 10, 99)
        ob.add_order("limit", "buy", 10, 99)
        assert ob.last_price == 99
    
    def test_large_imbalance_same_price(self, ob):
        """Many same-price orders get matched FIFO; remainder rests."""
        # 3 buys of 10 @ 100 => 30 bid qty
        b1 = ob.add_order("limit", "buy", 10, 100)
        b2 = ob.add_order("limit", "buy", 10, 100)
        b3 = ob.add_order("limit", "buy", 10, 100)

        # 4 sells of 1 @ 100 then 100 @ 100 => total sell 104
        ob.add_order("limit", "sell", 1, 100)
        ob.add_order("limit", "sell", 1, 100)
        ob.add_order("limit", "sell", 1, 100)
        ob.add_order("limit", "sell", 1, 100)
        oid_big = ob.add_order("limit", "sell", 100, 100)

        # All 30 bid should be gone; sell remainder should rest at 100
        assert _total_resting(ob.bids) == 0
        assert ob.best_bid() is None
        assert ob.best_ask() == 100
        assert oid_big in ob.order_map
        # total sell 104 - 30 matched = 74 resting (depending on how you treat the earlier 1-lots, could be split across multiple orders)
        assert sum(o.qty for o in ob.asks[100]) == 74
        assert ob.last_price == 100
