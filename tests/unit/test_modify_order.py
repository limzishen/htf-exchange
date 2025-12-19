def _total_resting(levels) -> int:
    """Total number of resting orders across all price levels."""
    return sum(len(q) for q in levels.values())

class TestModifyOrder:
    def test_modify_one_order_price(self, ob):
        """Modify order price."""
        target = ob.add_order("limit", "sell", 10, 100)
        new_target = ob.modify_order(target, 10, 120)

        assert new_target != target
        assert target in ob.cancelled_orders
        assert new_target in ob.order_map
        assert ob.order_map[new_target].price == 120
        assert ob.order_map[new_target].qty == 10

    def test_increasing_order_quantity(self, ob):
        """Increasing order quantity."""
        target = ob.add_order("limit", "sell", 10, 100)
        new_target = ob.modify_order(target, 20, 100)

        assert new_target != target
        assert target in ob.cancelled_orders
        assert new_target in ob.order_map
        assert ob.order_map[new_target].price == 100
        assert ob.order_map[new_target].qty == 20

    def test_decreasing_order_quantity(self, ob):
        """Decreasing order quantity."""
        target = ob.add_order("limit", "sell", 20, 100)
        new_target = ob.modify_order(target, 10, 100)

        assert new_target == target
        assert target not in ob.cancelled_orders
        assert new_target in ob.order_map
        assert ob.order_map[new_target].price == 100
        assert ob.order_map[new_target].qty == 10

    def test_no_change(self, ob):
        """No change to order."""
        target = ob.add_order("limit", "sell", 10, 100)
        new_target = ob.modify_order(target, 10, 100)
        assert new_target == target
        assert target not in ob.cancelled_orders
        assert new_target in ob.order_map
        assert ob.order_map[new_target].price == 100
        assert ob.order_map[new_target].qty == 10

    def test_invalid_order(self, ob):
        """Invalid order."""
        assert ob.modify_order("false", 10, 100) == "False"






