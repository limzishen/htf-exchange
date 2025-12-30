from datetime import datetime, timezone
import pytest

from htf_engine.errors.exchange_errors.invalid_order_quantity_error import (
    InvalidOrderQuantityError,
)
from htf_engine.errors.exchange_errors.invalid_stop_price_error import (
    InvalidStopPriceError,
)
from htf_engine.orders.limit_order import LimitOrder
from htf_engine.orders.market_order import MarketOrder


class TestOrderInitialisation:
    def test_limit_order_creation(self):
        """Test limit order creation."""
        timestamp = datetime.now(timezone.utc)
        order = LimitOrder(
            order_id="1",
            side="buy",
            price=100,
            qty=10,
            user_id="u1",
            timestamp=str(timestamp),
        )
        assert order.order_id == "1"
        assert order.side == "buy"
        assert order.price == 100
        assert order.qty == 10
        assert order.is_buy_order()
        assert not order.is_sell_order()

    def test_market_order_creation(self):
        """Test market order creation."""
        timestamp = datetime.now(timezone.utc)
        order = MarketOrder(
            order_id="2", side="sell", qty=5, user_id="u1", timestamp=str(timestamp)
        )
        assert order.order_id == "2"
        assert order.side == "sell"
        assert order.qty == 5
        assert not order.is_buy_order()
        assert order.is_sell_order()

    def test_invalid_order_quantity_zero(self):
        """Test that zero quantity raises ValueError."""
        timestamp = datetime.now(timezone.utc)

        with pytest.raises(InvalidOrderQuantityError) as e1:
            LimitOrder("1", "buy", 100, 0, user_id="u1", timestamp=str(timestamp))

        assert (
            str(e1.value)
            == "[INVALID_ORDER_QUANTITY] Invalid Order: Order quantity must be positive (received=0)."
        )

        with pytest.raises(InvalidOrderQuantityError) as e2:
            MarketOrder("1", "buy", 0, user_id="u1", timestamp=str(timestamp))

        assert (
            str(e2.value)
            == "[INVALID_ORDER_QUANTITY] Invalid Order: Order quantity must be positive (received=0)."
        )

    def test_invalid_order_quantity_negative(self):
        """Test that negative quantity raises ValueError."""
        timestamp = datetime.now(timezone.utc)

        with pytest.raises(InvalidOrderQuantityError) as e3:
            LimitOrder("1", "buy", 100, -1, user_id="u1", timestamp=str(timestamp))

        assert (
            str(e3.value)
            == "[INVALID_ORDER_QUANTITY] Invalid Order: Order quantity must be positive (received=-1)."
        )

        with pytest.raises(InvalidOrderQuantityError) as e4:
            MarketOrder("1", "buy", -67, user_id="u1", timestamp=str(timestamp))

        assert (
            str(e4.value)
            == "[INVALID_ORDER_QUANTITY] Invalid Order: Order quantity must be positive (received=-67)."
        )


def test_stop_limit_buy_order_creation(ob):
    oid = ob.add_order("stop-limit", "buy", 10, price=100, user_id=None, stop_price=200)
    assert oid in ob.order_map
    assert ob.stop_bids_price[0][2] == oid
    assert ob.stop_bids_price[0][0] == -200
    assert ob.stop_bids[200][0].order_id == oid
    assert ob.stop_bids[200][0].qty == 10
    assert ob.stop_bids[200][0].side == "buy"
    assert ob.stop_bids[200][0].price == 100
    assert ob.stop_bids[200][0].user_id == "TESTING: NO_USER_ID"


def test_stop_limit_sell_order_creation(ob):
    oid = ob.add_order(
        "stop-limit", "sell", 10, price=100, user_id=None, stop_price=200
    )
    assert oid in ob.order_map
    assert ob.stop_asks_price[0][2] == oid
    assert ob.stop_asks_price[0][0] == 200
    assert ob.stop_asks[200][0].order_id == oid
    assert ob.stop_asks[200][0].qty == 10
    assert ob.stop_asks[200][0].side == "sell"
    assert ob.stop_asks[200][0].price == 100
    assert ob.stop_asks[200][0].user_id == "TESTING: NO_USER_ID"


def test_stop_market_buy_order_creation(ob):
    oid = ob.add_order("stop-market", "buy", 10, user_id=None, stop_price=200)
    assert oid in ob.order_map
    assert ob.stop_bids_price[0][2] == oid
    assert ob.stop_bids_price[0][0] == -200
    assert ob.stop_bids[200][0].order_id == oid
    assert ob.stop_bids[200][0].qty == 10
    assert ob.stop_bids[200][0].side == "buy"


def test_stop_market_sell_order_creation(ob):
    oid = ob.add_order("stop-market", "sell", 10, user_id=None, stop_price=200)
    assert oid in ob.order_map
    assert ob.stop_asks_price[0][2] == oid
    assert ob.stop_asks_price[0][0] == 200
    assert ob.stop_asks[200][0].order_id == oid
    assert ob.stop_asks[200][0].qty == 10
    assert ob.stop_asks[200][0].side == "sell"


def test_check_stop_orders(ob):
    ob.add_order("stop-limit", "buy", 10, user_id=None, stop_price=200, price=200)
    ob.add_order("limit", "buy", 10, price=200, user_id=None)
    ob.add_order("limit", "sell", 10, price=200, user_id=None)
    assert ob.bids[200][0].is_buy_order()
    assert ob.bids[200][0].order_type == "limit"
    assert ob.bids[200][0].qty == 10
    assert ob.bids[200][0].side == "buy"
    assert ob.bids[200][0].price == 200


def test_modify_stop_orders(ob):
    oid = ob.add_order("stop-limit", "buy", 10, user_id=None, stop_price=200, price=200)
    new_oid = ob.modify_order(oid, 20, 200, new_stop_price=200)

    assert ob.stop_bids_price[0][0] == -200
    assert len(ob.stop_bids_price) == 2
    assert ob.order_map[new_oid].qty == 20

    ob.add_order("limit", "buy", 10, price=200, user_id=None)
    ob.add_order("limit", "sell", 10, price=200, user_id=None)

    assert len(ob.stop_bids_price) == 0

    oid = ob.add_order("stop-limit", "buy", 10, user_id=None, stop_price=201, price=200)
    new_oid = ob.modify_order(oid, new_qty=10, new_price=200, new_stop_price=300)

    assert len(ob.stop_bids_price) == 2
    assert ob.order_map[new_oid].qty == 10

    ob.add_order("limit", "buy", 10, price=200, user_id=None)
    ob.add_order("limit", "sell", 10, price=200, user_id=None)

    assert new_oid in ob.order_map
    assert len(ob.stop_bids_price) == 2
    assert ob.order_map[new_oid].qty == 10
    assert ob.order_map[new_oid].price == 200
    assert ob.order_map[new_oid].side == "buy"
    assert ob.order_map[new_oid].user_id == "TESTING: NO_USER_ID"
    assert ob.order_map[new_oid].order_type == "stop-limit"
    assert ob.order_map[new_oid].stop_price == 300

    ob.add_order("limit", "buy", 10, price=300, user_id=None)
    ob.add_order("limit", "sell", 10, price=300, user_id=None)

    assert len(ob.stop_bids_price) == 0
    assert len(ob.bids[200]) == 3
    assert ob.bids[200][0].order_id != new_oid


def test_error_stop_orders(ob):
    ob.add_order("limit", "buy", 10, price=200, user_id=None)
    ob.add_order("limit", "sell", 10, price=200, user_id=None)

    with pytest.raises(
        InvalidStopPriceError,
        match="Stop price less than or equal to last traded price",
    ):
        ob.add_order("stop-limit", "buy", 10, price=200, user_id=None, stop_price=200)
