import pytest
from htf_engine.orders.limit_order import LimitOrder
from htf_engine.orders.market_order import MarketOrder

class TestOrderInitialisation:
    def test_limit_order_creation(self):
        """Test limit order creation."""
        order = LimitOrder(order_id=1, side="buy", price=100, qty=10)
        assert order.order_id == 1
        assert order.side == "buy"
        assert order.price == 100
        assert order.qty == 10
        assert order.is_buy_order() is True
        assert order.is_sell_order() is False

    def test_market_order_creation(self):
        """Test market order creation."""
        order = MarketOrder(order_id=2, side="sell", qty=5)
        assert order.order_id == 2
        assert order.side == "sell"
        assert order.qty == 5
        assert order.is_buy_order() is False
        assert order.is_sell_order() is True

    def test_invalid_order_quantity_zero(self):
        """Test that zero quantity raises ValueError."""
        with pytest.raises(ValueError, match="Order quantity must be > 0"):
            LimitOrder(1, "buy", 100, 0)
        with pytest.raises(ValueError, match="Order quantity must be > 0"):
            MarketOrder(1, "buy", 0)

    def test_invalid_order_quantity_negative(self):
        """Test that negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="Order quantity must be > 0"):
            LimitOrder(1, "buy", 100, -5)
        with pytest.raises(ValueError, match="Order quantity must be > 0"):
            MarketOrder(1, "buy", -5)
