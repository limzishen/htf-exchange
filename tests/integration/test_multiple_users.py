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
        assert ob.enable_stp

        # User 1 wants to buy 50 Stock A at $10 and sell 50 Stock A at $20
        id_user1_order1 = u1.place_order("Stock A", "limit", "buy", 50, 10)
        id_user1_order2 = u1.place_order("Stock A", "post-only", "sell", 50, 20)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 50 }
        assert u1.get_outstanding_sells() == { "Stock A": 50 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 50 }

        # User 1 wants to buy more (but still within the exchange limit)
        u1.place_order("Stock A", "limit", "buy", 50, 10)  

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 100 }
        assert u1.get_outstanding_sells() == { "Stock A": 50 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 0, "sell_quota": 50 } 

        # User 1 wants to sell more (but still within the exchange limit)
        u1.place_order("Stock A", "limit", "sell", 50, 20) 

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None 
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 100 }
        assert u1.get_outstanding_sells() == { "Stock A": 100 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 0, "sell_quota": 0 }

        # User 1 tries to breach the limit of 100 by placing a limit buy
        with pytest.raises(ValueError, match=f"User {u1.user_id} cannot place order: would exceed position limit"):
            u1.place_order("Stock A", "limit", "buy", 50, 10)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None 
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 100 }
        assert u1.get_outstanding_sells() == { "Stock A": 100 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 0, "sell_quota": 0 }
  
        # User 1 tries to breach the limit of 100 by placing a market sell
        with pytest.raises(ValueError, match=f"User {u1.user_id} cannot place order: would exceed position limit"):
            u1.place_order("Stock A", "market", "sell", 50, 20)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 100
        assert last_price is None 
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 100 }
        assert u1.get_outstanding_sells() == { "Stock A": 100 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 0, "sell_quota": 0 }
        
        # User 1 cancels the second order
        u1.cancel_order(id_user1_order2, "Stock A")

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 100
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 100 }
        assert u1.get_outstanding_sells() == { "Stock A": 50 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 0, "sell_quota": 50 }

        # User 1 cancels the first order
        u1.cancel_order(id_user1_order1, "Stock A")

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 50
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price is None
        assert exchange.balance == 0

        assert u1.positions == {}
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5000
        assert u1.get_outstanding_buys() == { "Stock A": 50 }
        assert u1.get_outstanding_sells() == { "Stock A": 50 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 50 }

        # User 2 wants to sell 50 Stock A at $10, matching User 1's limit buy order
        u2.place_order("Stock A", "limit", "sell", 50, 10)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 50
        assert last_price == 10
        assert exchange.balance == 20

        assert u1.positions == { "Stock A": 50 }
        assert u1.get_realised_pnl() == 0
        assert u1.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u1.get_total_exposure() == 500   # User 1 owns 50 shares @ $10 each
        assert u1.get_cash_balance() == 4490
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { "Stock A": 50 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 100 }   # Can sell up to 150 shares now, but 50 quota already used in existing order
        
        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0
        assert u2.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u2.get_total_exposure() == 500   # User 2 owns -50 shares @ $10 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        # User 3 wants to FOK buy 25 Stock A at $20, matching User 1's limit sell order
        u3.place_order("Stock A", "fok", "buy", 25, 20)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 25
        assert last_price == 20
        assert exchange.balance == 40

        assert u1.positions == { "Stock A": 25 }
        assert u1.get_realised_pnl() == 250     # User 1 sold 25 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 250   # User 1 has 25 shares with cost basis of $10 (current price = $20)
        assert u1.get_total_exposure() == 500
        assert u1.get_cash_balance() == 4980
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { "Stock A": 25 }
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 75, "sell_quota": 100 }  # Can sell up to 125 shares now, but 25 quota already used in existing order

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500  # User 2 is short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000  # User 2 owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 25 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u3.get_total_exposure() == 500   # User 3 owns 25 shares @ $20 each
        assert u3.get_cash_balance() == 4490
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 75, "sell_quota": 125 }

        # User 3 wants to limit buy another 15 Stock A at $22, matching User 1's limit sell order at $20
        u3.place_order("Stock A", "limit", "buy", 15, 22)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 10
        assert last_price == 20                     # The trade still goes through at $20, which is the best ask
        assert exchange.balance == 60

        assert u1.positions == { "Stock A": 10 }    # User 1 sold all their shares
        assert u1.get_realised_pnl() == 400         # User 1 sold another 15 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 100       # User 1 is holding 10 shares with cost basis of $10 (current price = $20)
        assert u1.get_total_exposure() == 200     
        assert u1.get_cash_balance() == 5270
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { "Stock A": 10 }  
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 90, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500      # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000      # User 2 still owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}  
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 40 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         # Prices haven't moved yet
        assert u3.get_total_exposure() == 800       # User 3 owns 40 shares @ $20 each
        assert u3.get_cash_balance() == 4180
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}  
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 60, "sell_quota": 140 }

        # User 3 wants to market buy another 5 Stock A
        u3.place_order("Stock A", "market", "buy", 5)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 5
        assert last_price == 20    
        assert exchange.balance == 80                 

        assert u1.positions == { "Stock A": 5 }     # User 1 sold 5 shares
        assert u1.get_realised_pnl() == 450         # User 1 sold another 5 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 50        # User 1 is holding 10 shares with cost basis of $10 (current price = $20)
        assert u1.get_total_exposure() == 100
        assert u1.get_cash_balance() == 5360     
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == { "Stock A": 5 }   
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 95, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500      # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000      # User 2 still owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 45 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         # Prices haven't moved yet
        assert u3.get_total_exposure() == 900       # User 3 owns 40 shares @ $20 each
        assert u3.get_cash_balance() == 4070
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 55, "sell_quota": 145 }

        # User 3 wants to market buy another 20 Stock A (but remaining ask liquidity is 5 only)
        u3.place_order("Stock A", "market", "buy", 20)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price == 20  
        assert exchange.balance == 100                   

        assert u1.positions == {}                   # User 1 sold all shares
        assert u1.get_realised_pnl() == 500         # User 1 sold another 5 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 0         
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500      # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000      # User 2 still owns -50 shares @ $20 each
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 50 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         # Prices haven't moved yet
        assert u3.get_total_exposure() == 1000      # User 3 owns 50 shares @ $20 each
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 150 }

        # User 3 tries to breach the limit of 50 by placing a limit buy
        with pytest.raises(ValueError, match=f"User {u3.user_id} cannot place order: would exceed position limit"):
            u3.place_order("Stock A", "limit", "buy", 75, 15)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert last_price == 20     
        assert exchange.balance == 100                

        assert u1.positions == {}                
        assert u1.get_realised_pnl() == 500      
        assert u1.get_unrealised_pnl() == 0         
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500     
        assert u2.get_total_exposure() == 1000     
        assert u2.get_cash_balance() == 5490
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 50 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         
        assert u3.get_total_exposure() == 1000      
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 150 }
        
        # User 3 wants to limit sell 30 Stock A at $100
        u3.place_order("Stock A", "limit", "sell", 30, 100)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 30
        assert last_price == 20     
        assert exchange.balance == 100                

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert u1.get_unrealised_pnl() == 0         
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500      
        assert u2.get_total_exposure() == 1000   
        assert u2.get_cash_balance() == 5490  
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 50 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         
        assert u3.get_total_exposure() == 1000     
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == { "Stock A": 30 }
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 120 }

        # User 2 tries to post-only buy another 50 Stock A at $105 (but it is rejected, as it matches User 3's limit sell order at $100)
        with pytest.raises(ValueError, match=f"Post-only buy would take liquidity"):  
            u2.place_order("Stock A", "post-only", "buy", 50, 105)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 30
        assert last_price == 20     
        assert exchange.balance == 100                

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert u1.get_unrealised_pnl() == 0         
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500      
        assert u2.get_total_exposure() == 1000   
        assert u2.get_cash_balance() == 5490  
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 50 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         
        assert u3.get_total_exposure() == 1000     
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == { "Stock A": 30 }
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 120 }

        # User 2 tries to FOK buy another 50 Stock A at $101 (but it is rejected, as there are only 30 shares of ask liquidity <= $101)
        with pytest.raises(ValueError, match=f"Insufficient Liquidity for FOK order: cancelling order .* from User {u2.user_id}"):  
            u2.place_order("Stock A", "fok", "buy", 50, 101)
        
        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 30
        assert last_price == 20     
        assert exchange.balance == 100                

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert u1.get_unrealised_pnl() == 0         
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -50 }
        assert u2.get_realised_pnl() == 0             
        assert u2.get_unrealised_pnl() == -500      
        assert u2.get_total_exposure() == 1000   
        assert u2.get_cash_balance() == 5490  
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 150, "sell_quota": 50 }

        assert u3.positions == { "Stock A": 50 }
        assert u3.get_realised_pnl() == 0
        assert u3.get_unrealised_pnl() == 0         
        assert u3.get_total_exposure() == 1000     
        assert u3.get_cash_balance() == 3960
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == { "Stock A": 30 }
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 50, "sell_quota": 120 }

        # User 2 wants to IOC buy another 50 Stock A at $120, matching User 3's limit sell order at $100 (but only 30 shares are transacted)
        u2.place_order("Stock A", "ioc", "buy", 50, 120)

        bids, asks, last_price = self._nice_snapshot(ob)
        assert bids[10] == 0
        assert bids[20] == 0
        assert bids[100] == 0
        assert bids[120] == 0
        assert asks[10] == 0
        assert asks[20] == 0
        assert asks[100] == 0
        assert asks[120] == 0
        assert last_price == 100            # The trade still goes through at $100, which is the best ask 
        assert exchange.balance == 120                   

        assert u1.positions == {}                   
        assert u1.get_realised_pnl() == 500         
        assert u1.get_unrealised_pnl() == 0         
        assert u1.get_total_exposure() == 0
        assert u1.get_cash_balance() == 5450
        assert u1.get_outstanding_buys() == {}
        assert u1.get_outstanding_sells() == {}        
        assert u1.get_remaining_quota("Stock A") == { "buy_quota": 100, "sell_quota": 100 }

        assert u2.positions == { "Stock A": -20 }
        assert u2.get_realised_pnl() == -2700       # User 2 bought 30 shares at $100 each, incurring $90 loss per share   
        assert u2.get_unrealised_pnl() == -1800     # User 2 is still short -20 shares with cost basis of $10 (current price = $100)
        assert u2.get_total_exposure() == 2000     
        assert u2.get_cash_balance() == 2480
        assert u2.get_outstanding_buys() == {}
        assert u2.get_outstanding_sells() == {}
        assert u2.get_remaining_quota("Stock A") == { "buy_quota": 120, "sell_quota": 80 }

        assert u3.positions == { "Stock A": 20 }
        assert u3.get_realised_pnl() == 2400        # User 3 sold 30 shares at $100 each, earning $80 profit per share   
        assert u3.get_unrealised_pnl() == 1600      # User 3 still holds 20 shares with cost basis of $20 (current price = $100)
        assert u3.get_total_exposure() == 2000 
        assert u3.get_cash_balance() == 6950  
        assert u3.get_outstanding_buys() == {}
        assert u3.get_outstanding_sells() == {}
        assert u3.get_remaining_quota("Stock A") == { "buy_quota": 80, "sell_quota": 120 }
        