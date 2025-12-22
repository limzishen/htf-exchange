from collections import defaultdict
import pytest

from htf_engine.errors.exchange_errors.fok_insufficient_liquidity_error import FOKInsufficientLiquidityError
from htf_engine.errors.exchange_errors.post_only_violation_error import PostOnlyViolationError


class TestExchange:
    def _nice_snapshot(self, ob):
        snap = ob.snapshot()
        bids = defaultdict(int)
        asks = defaultdict(int)

        for price, orders in snap['bids']:
            bids[price] = sum(o[3] for o in orders if o not in ob.cancelled_orders)  # o[3] is qty
        for price, orders in snap['asks']:
            asks[price] = sum(o[3] for o in orders if o not in ob.cancelled_orders)
        
        return bids, asks, snap['last_price'], snap['last_quantity']
        
    def test_exchange(self, exchange, u1, u2, u3):
        # Register 3 users
        exchange.register_user(u1)
        exchange.register_user(u2, 2)
        exchange.register_user(u3, 3)

        inst = "Stock A"

        ob = exchange.order_books[inst]
        assert ob.enable_stp

        # User 1 wants to limit buy 50 Stock A at $10
        id_user1_order1 = u1.place_order(inst, "limit", "buy", 50, 10)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 50 }
        assert u1.get_outstanding_sells() == {}
        assert u1.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 100 }

        # User 1 wants to post-only sell 70 Stock A at $30
        id_user1_order2 = u1.place_order(inst, "post-only", "sell", 70, 30)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[30] == 0
        assert asks[10] == 0
        assert asks[30] == 70
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 50 }
        assert u1.get_outstanding_sells() == { inst: 70 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 30 }

        # User 1 wants to modify the previous order to: post-only sell 70 Stock A at $20
        id_user1_order3 = exchange.modify_order(u1.user_id, inst, id_user1_order2, 70, 20)

        assert id_user1_order2 != id_user1_order3

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert bids[30] == 0
        assert asks[10] == 0
        assert asks[20] == 70
        assert asks[30] == 0
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 50 }
        assert u1.get_outstanding_sells() == { inst: 70 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 30 }

        # User 1 wants to modify the previous order to: post-only sell 50 Stock A at $20
        id_user1_order4 = exchange.modify_order(u1.user_id, inst, id_user1_order3, 50, 20)

        assert id_user1_order3 == id_user1_order4       # order_id should be the same since only quantity decreased

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert bids[30] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert asks[30] == 0
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 50 }
        assert u1.get_outstanding_sells() == { inst: 50 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 50 }

        # User 1 wants to buy more (but still within the exchange limit)
        u1.place_order(inst, "limit", "buy", 50, 10)  

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 100 }
        assert u1.get_outstanding_sells() == { inst: 50 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 0, "sell_quota": 50 } 

        # User 1 wants to sell more (but still within the exchange limit)
        u1.place_order(inst, "limit", "sell", 50, 20) 

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 100 }
        assert u1.get_outstanding_sells() == { inst: 100 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 0, "sell_quota": 0 }

        # User 1 tries to breach the limit of 100 by placing a limit buy
        with pytest.raises(ValueError, match=f"User {u1.user_id} cannot place order: would exceed position limit"):
            u1.place_order(inst, "limit", "buy", 50, 10)
        
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 100 }
        assert u1.get_outstanding_sells() == { inst: 100 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 0, "sell_quota": 0 }
  
        # User 1 tries to breach the limit of 100 by placing a market sell
        with pytest.raises(ValueError, match=f"User {u1.user_id} cannot place order: would exceed position limit"):
            u1.place_order(inst, "market", "sell", 50, 20)
        
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 100 }
        assert u1.get_outstanding_sells() == { inst: 100 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 0, "sell_quota": 0 }
        
        # User 1 cancels id_user1_order4
        u1.cancel_order(id_user1_order4, inst)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 100 }
        assert u1.get_outstanding_sells() == { inst: 50 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 0, "sell_quota": 50 }

        # User 1 cancels id_user1_order1
        u1.cancel_order(id_user1_order1, inst)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert last_quantity is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { inst: 50 }
        assert u1.get_outstanding_sells() == { inst: 50 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 50 }

        # User 2 wants to sell 50 Stock A at $10, matching User 1's limit buy order
        u2.place_order(inst, "limit", "sell", 50, 10)
        
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price == 10
        assert last_quantity == 50
        assert exchange.balance == 20

        assert u1.positions == { inst: 50 }
        assert u1.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0     # Prices haven't moved yet
        assert exchange.get_user_exposure(u1.user_id) == 500   # User 1 owns 50 shares @ $10 each
        assert u1.get_cash_balance() == 4490
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { inst: 50 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 100 }   # Can sell up to 150 shares now, but 50 quota already used in existing order
        
        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u2.user_id) == 0     # Prices haven't moved yet
        assert exchange.get_user_exposure(u2.user_id) == 500   # User 2 owns -50 shares @ $10 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        # User 3 wants to FOK buy 25 Stock A at $20, matching User 1's limit sell order
        u3.place_order(inst, "fok", "buy", 25, 20)
        
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 25
        assert last_price == 20
        assert last_quantity == 25
        assert exchange.balance == 40

        assert u1.positions == { inst: 25 }
        assert u1.get_realised_pnl() == 250     # User 1 sold 25 shares, earning $10 profit per share
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 250   # User 1 has 25 shares with cost basis of $10 (current price = $20)
        assert exchange.get_user_exposure(u1.user_id) == 500
        assert u1.get_cash_balance() == 4980
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { inst: 25 }
        assert u1.get_remaining_quota(inst) == { "buy_quota": 75, "sell_quota": 100 }  # Can sell up to 125 shares now, but 25 quota already used in existing order

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500  # User 2 is short 50 shares with unrealised loss of $10 per share
        assert exchange.get_user_exposure(u2.user_id) == 1000  # User 2 owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 25 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0     # Prices haven't moved yet
        assert exchange.get_user_exposure(u3.user_id) == 500   # User 3 owns 25 shares @ $20 each
        assert u3.get_cash_balance() == 4490
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota(inst) == { "buy_quota": 75, "sell_quota": 125 }

        # User 3 wants to limit buy another 15 Stock A at $22, matching User 1's limit sell order at $20
        u3.place_order(inst, "limit", "buy", 15, 22)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 10
        assert last_price == 20                     # The trade still goes through at $20, which is the best ask
        assert last_quantity == 15
        assert exchange.balance == 60

        assert u1.positions == { inst: 10 }    # User 1 sold all their shares
        assert u1.get_realised_pnl() == 400         # User 1 sold another 15 shares, earning $10 profit per share
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 100       # User 1 is holding 10 shares with cost basis of $10 (current price = $20)
        assert exchange.get_user_exposure(u1.user_id) == 200     
        assert u1.get_cash_balance() == 5270
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { inst: 10 }  
        assert u1.get_remaining_quota(inst) == { "buy_quota": 90, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500      # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert exchange.get_user_exposure(u2.user_id) == 1000      # User 2 still owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}  
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 40 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         # Prices haven't moved yet
        assert exchange.get_user_exposure(u3.user_id) == 800       # User 3 owns 40 shares @ $20 each
        assert u3.get_cash_balance() == 4180
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}  
        assert u3.get_remaining_quota(inst) == { "buy_quota": 60, "sell_quota": 140 }

        # User 3 wants to market buy another 5 Stock A
        u3.place_order(inst, "market", "buy", 5)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 5
        assert last_price == 20
        assert last_quantity == 5
        assert exchange.balance == 80                 

        assert u1.positions == { inst: 5 }     # User 1 sold 5 shares
        assert u1.get_realised_pnl() == 450         # User 1 sold another 5 shares, earning $10 profit per share
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 50        # User 1 is holding 10 shares with cost basis of $10 (current price = $20)
        assert exchange.get_user_exposure(u1.user_id) == 100
        assert u1.get_cash_balance() == 5360     
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { inst: 5 }   
        assert u1.get_remaining_quota(inst) == { "buy_quota": 95, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500      # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert exchange.get_user_exposure(u2.user_id) == 1000      # User 2 still owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 45 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         # Prices haven't moved yet
        assert exchange.get_user_exposure(u3.user_id) == 900       # User 3 owns 40 shares @ $20 each
        assert u3.get_cash_balance() == 4070
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota(inst) == { "buy_quota": 55, "sell_quota": 145 }

        # User 3 wants to market buy another 20 Stock A (but remaining ask liquidity is 5 only)
        u3.place_order(inst, "market", "buy", 20)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price == 20
        assert last_quantity == 5
        assert exchange.balance == 100                   

        assert u1.positions == {}                   # User 1 sold all shares
        assert u1.get_realised_pnl() == 500         # User 1 sold another 5 shares, earning $10 profit per share
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500      # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert exchange.get_user_exposure(u2.user_id) == 1000      # User 2 still owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 50 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         # Prices haven't moved yet
        assert exchange.get_user_exposure(u3.user_id) == 1000      # User 3 owns 50 shares @ $20 each
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 150 }

        # User 3 tries to breach the limit of 50 by placing a limit buy
        with pytest.raises(ValueError, match=f"User {u3.user_id} cannot place order: would exceed position limit"):
            u3.place_order(inst, "limit", "buy", 75, 15)
        
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price == 20
        assert last_quantity == 5
        assert exchange.balance == 100                

        assert u1.positions == {}                
        assert u1.get_realised_pnl() == 500      
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500     
        assert exchange.get_user_exposure(u2.user_id) == 1000     
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 50 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         
        assert exchange.get_user_exposure(u3.user_id) == 1000      
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 150 }
        
        # User 3 wants to limit sell 30 Stock A at $100
        u3.place_order(inst, "limit", "sell", 30, 100)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 30
        assert last_price == 20
        assert last_quantity == 5
        assert exchange.balance == 100                

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500      
        assert exchange.get_user_exposure(u2.user_id) == 1000   
        assert u2.get_cash_balance() == 5490  
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 50 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         
        assert exchange.get_user_exposure(u3.user_id) == 1000     
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == { inst: 30 }
        assert u3.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 120 }

        # User 2 tries to post-only buy another 50 Stock A at $105 (but it is rejected, as it matches User 3's limit sell order at $100)
        with pytest.raises(PostOnlyViolationError) as e1:
            u2.place_order(inst, "post-only", "buy", 50, 105)
        
        assert str(e1.value) == "[POST_ONLY_VIOLATION] Invalid Order: Post-only order would take liquidity and was rejected."
       
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 30
        assert last_price == 20
        assert last_quantity == 5
        assert exchange.balance == 100                

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500      
        assert exchange.get_user_exposure(u2.user_id) == 1000   
        assert u2.get_cash_balance() == 5490  
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 50 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         
        assert exchange.get_user_exposure(u3.user_id) == 1000     
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == { inst: 30 }
        assert u3.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 120 }

        # User 2 tries to FOK buy another 50 Stock A at $101 (but it is rejected, as there are only 30 shares of ask liquidity <= $101)
        with pytest.raises(FOKInsufficientLiquidityError) as e2:
            u2.place_order(inst, "fok", "buy", 50, 101)
        
        assert str(e2.value) == "[FOK_INSUFFICIENT_LIQUIDITY] Invalid Order: FOK order had insufficient liquidity and was cancelled."
        
        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 30
        assert last_price == 20
        assert last_quantity == 5
        assert exchange.balance == 100                

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -50 }
        assert u2.get_realised_pnl() == 0             
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -500      
        assert exchange.get_user_exposure(u2.user_id) == 1000   
        assert u2.get_cash_balance() == 5490  
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { inst: 50 }
        assert u3.get_realised_pnl() == 0
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 0         
        assert exchange.get_user_exposure(u3.user_id) == 1000     
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == { inst: 30 }
        assert u3.get_remaining_quota(inst) == { "buy_quota": 50, "sell_quota": 120 }

        # User 2 wants to IOC buy another 50 Stock A at $120, matching User 3's limit sell order at $100 (but only 30 shares are transacted)
        u2.place_order(inst, "ioc", "buy", 50, 120)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert bids[120] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 0
        assert asks[120] == 0
        assert last_price == 100            # The trade still goes through at $100, which is the best ask
        assert last_quantity == 30
        assert exchange.balance == 120                   

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -20 }
        assert u2.get_realised_pnl() == -2700       # User 2 bought 30 shares at $100 each, incurring $90 loss per share   
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -1800     # User 2 is still short -20 shares with cost basis of $10 (current price = $100)
        assert exchange.get_user_exposure(u2.user_id) == 2000     
        assert u2.get_cash_balance() == 2480
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 120, "sell_quota": 80 }

        assert u3.positions == { inst: 20 }
        assert u3.get_realised_pnl() == 2400        # User 3 sold 30 shares at $100 each, earning $80 profit per share   
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 1600      # User 3 still holds 20 shares with cost basis of $20 (current price = $100)
        assert exchange.get_user_exposure(u3.user_id) == 2000 
        assert u3.get_cash_balance() == 6950  
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota(inst) == { "buy_quota": 80, "sell_quota": 120 }
        
        # User 1 wants to IOC buy another 25 Stock A at $500, but nothing happens as there is zero liquidity in the market
        u1.place_order(inst, "ioc", "buy", 25, 500)

        bids, asks, last_price, last_quantity = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert bids[120] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 0
        assert asks[120] == 0
        assert last_price == 100
        assert last_quantity == 30
        assert exchange.balance == 120                   

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert exchange.get_user_unrealised_pnl(u1.user_id) == 0         
        assert exchange.get_user_exposure(u1.user_id) == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota(inst) == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { inst: -20 }
        assert u2.get_realised_pnl() == -2700
        assert exchange.get_user_unrealised_pnl(u2.user_id) == -1800
        assert exchange.get_user_exposure(u2.user_id) == 2000     
        assert u2.get_cash_balance() == 2480
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota(inst) == { "buy_quota": 120, "sell_quota": 80 }

        assert u3.positions == { inst: 20 }
        assert u3.get_realised_pnl() == 2400        
        assert exchange.get_user_unrealised_pnl(u3.user_id) == 1600
        assert exchange.get_user_exposure(u3.user_id) == 2000 
        assert u3.get_cash_balance() == 6950  
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota(inst) == { "buy_quota": 80, "sell_quota": 120 }
        