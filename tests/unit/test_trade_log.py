import pytest
from datetime import timezone

from htf_engine.errors.exchange_errors.invalid_aggressor_error import InvalidAggressorError
from htf_engine.trades.trade import Trade

class TestTradeLog:
    def test_record_valid_trade(self, trade_log):
        trade = trade_log.record(
            price=100.5,
            qty=10,
            buy_user_id="user1",
            sell_user_id="user2",
            buy_order_id="order1",
            sell_order_id="order2",
            aggressor="buy"
        )
        assert isinstance(trade, Trade)
        assert trade.price == 100.5
        assert trade.qty == 10
        assert trade.buy_user_id == "user1"
        assert trade.sell_user_id == "user2"
        assert trade.buy_order_id == "order1"
        assert trade.sell_order_id == "order2"
        assert trade.aggressor == "buy"
        assert trade.timestamp.tzinfo == timezone.utc
        assert len(trade_log.retrieve_log()) == 1

    def test_record_invalid_aggressor(self, trade_log):
        with pytest.raises(InvalidAggressorError) as e1:
            trade_log.record(
                price=50,
                qty=5,
                buy_user_id="user1",
                sell_user_id="user2",
                buy_order_id="order1",
                sell_order_id="order2",
                aggressor="hold"
            )
        assert str(e1.value) == "[INVALID_AGGRESSOR] Invalid aggressor hold received. Must be 'buy' or 'sell'."

    def test_retrieve_simple_log(self, trade_log):
        trade_log.record(
            price=200,
            qty=1,
            buy_user_id="u1",
            sell_user_id="u2",
            buy_order_id="oid1",
            sell_order_id="oid2",
            aggressor="sell"
        )
        
        trade_log.record(
            price=200,
            qty=1,
            buy_user_id="u3",
            sell_user_id="u4",
            buy_order_id="oid3",
            sell_order_id="oid4",
            aggressor="buy"
        )

        trade_log.record(
            price=200,
            qty=1,
            buy_user_id="u5",
            sell_user_id="u6",
            buy_order_id="oid5",
            sell_order_id="oid6",
            aggressor="sell"
        )

        simple_log = trade_log.retrieve_simple_log()

        assert isinstance(simple_log, tuple)
        assert all(isinstance(t, str) for t in simple_log)

        assert "u1" in simple_log[0]
        assert "u2" in simple_log[0]
        assert "oid1" in simple_log[0]
        assert "oid2" in simple_log[0]

        assert "u3" in simple_log[1]
        assert "u4" in simple_log[1]
        assert "oid3" in simple_log[1]
        assert "oid4" in simple_log[1]

        assert "u5" in simple_log[2]
        assert "u6" in simple_log[2]
        assert "oid5" in simple_log[2]
        assert "oid6" in simple_log[2]

    def test_str_representation(self, trade_log):
        trade_log.record(
            price=10,
            qty=3,
            buy_user_id="b1",
            sell_user_id="s1",
            buy_order_id="o1",
            sell_order_id="o2",
            aggressor="buy"
        )

        trade_log.record(
            price=20,
            qty=50,
            buy_user_id="b3",
            sell_user_id="s3",
            buy_order_id="o3",
            sell_order_id="o4",
            aggressor="sell"
        )

        log_str = str(trade_log)

        assert isinstance(log_str, str)
        
        log_strs = log_str.split("\n")
        
        assert "b1" in log_strs[0]
        assert "s1" in log_strs[0]
        assert "o1" in log_strs[0]
        assert "o2" in log_strs[0]
        assert "BUY" in log_strs[0]         # Must be in CAPS, otherwise it will always return true due to buy_uid and buy_oid
        assert "b3" not in log_strs[0]
        assert "s3" not in log_strs[0]
        assert "o3" not in log_strs[0]
        assert "o4" not in log_strs[0]
        assert "SELL" not in log_strs[0]    # Must be in CAPS, same reason as above

        assert "b3" in log_strs[1]
        assert "s3" in log_strs[1]
        assert "o3" in log_strs[1]
        assert "o4" in log_strs[1]
        assert "SELL" in log_strs[1]
        assert "b1" not in log_strs[1]
        assert "s1" not in log_strs[1]
        assert "o1" not in log_strs[1]
        assert "o2" not in log_strs[1]
        assert "BUY" not in log_strs[1]
