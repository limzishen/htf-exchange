class TestExchange:
    def test_exchange(self, exchange, u1, u2, u3):
        exchange.register_user(u1)
        exchange.register_user(u2)
        exchange.register_user(u3)

        # User 1 wants to buy 50 Stock A at $10 and sell 50 Stock A at $20
        u1.place_order(exchange, "Stock A", "limit", "buy", 50, 10)
        u1.place_order(exchange, "Stock A", "limit", "sell", 50, 20)

        assert exchange.order_books["Stock A"].last_price is None

        assert len(u1.positions) == 0
        assert u1.realised_pnl == 0
        assert u1.get_unrealised_pnl() == 0
        assert u1.get_total_exposure() == 0

        # User 2 wants to sell 50 Stock A at $10, matching User 1's limit buy order
        u2.place_order(exchange, "Stock A", "limit", "sell", 50, 10)
        
        assert exchange.order_books["Stock A"].last_price == 10

        assert len(u1.positions) == 1
        assert u1.realised_pnl == 0
        assert u1.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u1.get_total_exposure() == 500   # User 1 owns 50 shares @ $10 each
        
        assert len(u2.positions) == 1
        assert u2.realised_pnl == 0
        assert u2.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u2.get_total_exposure() == 500   # User 2 owns -50 shares @ $10 each

        # User 3 wants to buy 25 Stock A at $20, matching User 1's limit sell order
        u3.place_order(exchange, "Stock A", "limit", "buy", 25, 20)
        
        assert exchange.order_books["Stock A"].last_price == 20

        assert len(u1.positions) == 1
        assert u1.realised_pnl == 250           # User 1 sold 25 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 250   # User 1 has 25 shares with cost basis of $10 (current price = $20)
        assert u1.get_total_exposure() == 500   

        assert len(u2.positions) == 1
        assert u2.realised_pnl == 0             
        assert u2.get_unrealised_pnl() == -500  # User 2 is short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000  # User 2 owns -50 shares @ $20 each

        assert len(u3.positions) == 1
        assert u3.realised_pnl == 0
        assert u3.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u3.get_total_exposure() == 500   # User 3 owns 25 shares @ $20 each

        # User 3 wants to buy another 25 Stock A at $20, matching User 1's limit sell order
        u3.place_order(exchange, "Stock A", "limit", "buy", 25, 20)

        assert exchange.order_books["Stock A"].last_price == 20

        assert len(u1.positions) == 0           # User 1 sold all their shares
        assert u1.realised_pnl == 500           # User 1 sold another 25 shares, earning $10 profit per share
        assert u1.get_unrealised_pnl() == 0     # User 1 has zero positions, so the unrealised PnL must be zero
        assert u1.get_total_exposure() == 0     # User 1 has zero positions, so the total exposure must be zero

        assert len(u2.positions) == 1
        assert u2.realised_pnl == 0             
        assert u2.get_unrealised_pnl() == -500  # User 2 is still short 50 shares with unrealised loss of $10 per share
        assert u2.get_total_exposure() == 1000  # User 2 still owns -50 shares @ $20 each

        assert len(u3.positions) == 1
        assert u3.realised_pnl == 0
        assert u3.get_unrealised_pnl() == 0     # Prices haven't moved yet
        assert u3.get_total_exposure() == 1000   # User 3 owns 50 shares @ $20 each

        
