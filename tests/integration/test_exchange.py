from collections import defaultdict
import pytest

class TestExchange:
    def _nice_snapshot(self, ob):
        snap = ob.snapshot()
        bids = defaultdict(int)
        asks = defaultdict(int)

        for price, orders in snap['bids']:
            bids[price] = sum(o[3] for o in orders)  # o[3] is qty
        for price, orders in snap['asks']:
            asks[price] = sum(o[3] for o in orders)
        
        return bids, asks, snap['last_price']
        

    def test_exchange(self, exchange, u1, u2, u3):
        # Register 3 users
        exchange.register_user(u1)
        exchange.register_user(u2)
        exchange.register_user(u3)

        ob = exchange.order_books["Stock A"]

        # User 1 wants to buy 50 Stock A at $10 and sell 50 Stock A at $20
        id_user1_order1 = u1.place_order(exchange, "Stock A", "limit", "buy", 50, 10)
        id_user1_order2 =u1.place_order(exchange, "Stock A", "limit", "sell", 50, 20)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0

        # User 1 wants to buy and sell more (but still within the exchange limit)
        id_user1_order3 = u1.place_order(exchange, "Stock A", "limit", "buy", 50, 10)   
        id_user1_order4 = u1.place_order(exchange, "Stock A", "limit", "sell", 50, 20)  

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None

        # User 1 tries to breach the exchange limit of 100
        with pytest.raises(ValueError, match=f"User {u1.user_id} cannot place order: would exceed position limit"):
            u1.place_order(exchange, "Stock A", "limit", "buy", 50, 10)
  
        with pytest.raises(ValueError, match=f"User {u1.user_id} cannot place order: would exceed position limit"):
            u1.place_order(exchange, "Stock A", "limit", "sell", 50, 20)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None
        
        # User 1 cancels the first order
        u1.cancel_order(id_user1_order3)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None
        
        # User 1 cancels the second order
        u1.cancel_order(id_user1_order4)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None

        # User 2 wants to sell 50 Stock A at $10, matching User 1's limit buy order
        u2.place_order(exchange, "Stock A", "limit", "sell", 50, 10)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price == 10

        assert u1.positions == {"Stock A": 50}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u1.get_total_exposure() == 500   # User 1 owns 50 shares @ $10 each
        
        assert u2.positions == {"Stock A": -50}
        assert u2.get_realised_pnl() == 0
        assert u2.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u2.get_total_exposure() == 500   # User 2 owns -50 shares @ $10 each

        # User 3 wants to buy 25 Stock A at $20, matching User 1's limit sell order
        u3.place_order(exchange, "Stock A", "limit", "buy", 25, 20)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 25
        assert last_price == 20

        assert u1.positions == {"Stock A": 25}
        assert u1.get_realised_pnl() == 250     # User 1 sold 25 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 250   # User 1 has 25 shares with cost basis of $10 (current price = $20)
        assert u1.get_total_exposure() == 500   

        assert u2.positions == {"Stock A": -50}
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500  # User 2 is short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000  # User 2 owns -50 shares @ $20 each

        assert u3.positions == {"Stock A": 25}
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u3.get_total_exposure() == 500   # User 3 owns 25 shares @ $20 each

        # User 3 wants to buy another 25 Stock A at $22, matching User 1's limit sell order at $20
        u3.place_order(exchange, "Stock A", "limit", "buy", 25, 22)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price == 20                 # The trade still goes through at $20, which is the best ask

        assert u1.positions == {}               # User 1 sold all their shares
        assert u1.get_realised_pnl() == 500     # User 1 sold another 25 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 0     # User 1 has zero positions, so the unrealised PnL must be zero
        assert u1.get_total_exposure() == 0     # User 1 has zero positions, so the total exposure must be zero

        assert u2.positions == {"Stock A": -50}
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500  # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000  # User 2 still owns -50 shares @ $20 each

        assert u3.positions == {"Stock A": 50}
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u3.get_total_exposure() == 1000  # User 3 owns 50 shares @ $20 each

        
