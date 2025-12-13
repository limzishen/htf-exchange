from htf_engine.order_book import OrderBook

def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())


class TestOrderBookInitialization:
    def test_empty_orderbook(self, ob):
        """Empty order book has no orders and no best bid/ask."""
        assert _total_resting(ob.bids) == 0
        assert _total_resting(ob.asks) == 0
        assert len(ob.order_map) == 0
        assert ob.best_bid() is None
        assert ob.best_ask() is None
        assert ob.last_price is None

    def test_order_ids_increment(self, ob):
        """Check that order IDs are assigned incrementally."""
        id1 = ob.add_order("limit", "buy", 10, 100)
        id2 = ob.add_order("limit", "sell", 10, 101)
        id3 = ob.add_order("limit", "buy", 10, 99)
        assert (id1, id2, id3) == (0, 1, 2)
    
    def test_two_books_equal_after_same_ops(self, ob):
        ob2 = OrderBook()

        for ob in (ob, ob2):
            ob.add_order("limit", "buy", 5, 100)
            ob.add_order("limit", "sell", 3, 105)

        assert ob == ob2


class TestOrderBookState:
    def test_best_bid_best_ask_updates(self, ob):
        """Check best bid and ask after adding orders."""
        ob.add_order("limit", "buy", 10, 100)
        ob.add_order("limit", "buy", 10, 101)
        ob.add_order("limit", "sell", 10, 105)
        ob.add_order("limit", "sell", 10, 104)

        assert ob.best_bid() == 101
        assert ob.best_ask() == 104

    def test_get_all_pending_orders_empty(self, ob):
        """Get all pending orders from an empty order book."""
        assert ob.get_all_pending_orders() == []
    
    def test_noncrossing_orders_rest(self, ob):
        """Non-crossing orders remain resting in the book."""
        for args in [
            ("limit", "buy", 5, 95),
            ("limit", "buy", 3, 100),
            ("limit", "buy", 5, 90),
            ("limit", "sell", 4, 105),
            ("limit", "sell", 9, 123),
            ("limit", "sell", 2, 110),
        ]:
            ob.add_order(*args)

        expected = OrderBook()
        for args in [
            ("limit", "buy", 5, 95),
            ("limit", "buy", 3, 100),
            ("limit", "buy", 5, 90),
            ("limit", "sell", 4, 105),
            ("limit", "sell", 9, 123),
            ("limit", "sell", 2, 110),
        ]:
            expected.add_order(*args)

        assert ob == expected
        assert ob.best_bid() == 100
        assert ob.best_ask() == 105

    


