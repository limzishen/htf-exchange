from htf_engine.order_book import OrderBook

class TestOwnImplementation:
    def test_own_testcase(self, ob):
        """Try your own test cases, for differnt scenarios, market orders etc."""
        # Edit this for your own test cases
        for args in [
            ("limit", "buy", 10, 100),
            ("limit", "buy", 10, 100),
            ("limit", "buy", 10, 100),
            ("limit", "sell", 1, 100),
            ("limit", "sell", 1, 100),
            ("limit", "sell", 1, 100),
            ("limit", "sell", 1, 100),
        ]:
            ob.add_order(*args)

        # Optional: assert a pre-whatever state (helps debugging)
        # After 4 sells of 1 against 3 buys of 10 => total bid qty 30 - 4 = 26 remaining at 100
        assert ob.best_bid() == 100
        assert ob.best_ask() is None
        assert sum(o.qty for o in ob.bids[100]) == 26

        # ========================================================
        #                         TEST SOME EVENT
        ob.add_order("fok", "sell", 20, 100)
        # ========================================================
        
        # This is the expected that should pass your test case
        expected = OrderBook("GOOG")
        for args in [
            ("limit", "buy", 10, 100),
            ("limit", "buy", 10, 100),
            ("limit", "buy", 10, 100),
            ("limit", "sell", 1, 100),
            ("limit", "sell", 1, 100),
            ("limit", "sell", 1, 100),
            ("limit", "sell", 1, 100),
            ("fok",   "sell", 20, 100),
        ]:
            expected.add_order(*args)
            
        # ---- Assert (state equality) ----
        assert ob == expected

        # If FOK succeeds, it should take 20 from the remaining 26 bids -> 6 left at 100
        # If FOK fails (not enough liquidity), it should leave 26 unchanged.
        remaining = sum(o.qty for o in ob.bids[100])
        assert remaining in (6, 26)

        if remaining == 6:
            # FOK succeeded
            assert ob.last_price == 100
            assert ob.best_bid() == 100
            assert ob.best_ask() is None
        else:
            # FOK failed (no change)
            assert ob.best_bid() == 100
            assert ob.best_ask() is None