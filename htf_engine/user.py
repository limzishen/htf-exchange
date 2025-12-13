class User:
    def __init__(self, user_id, username, cash_balance=0.0):
        self.user_id = user_id
        self.username = username
        self.cash_balance = cash_balance
        self.positions = {}         # instrument -> quantity
        self.average_cost = {}      # instrument -> avg cost
        self.realised_pnl = 0.0
        self.unrealised_pnl = 0.0   # TODO: calculate this efficiently next time

        self.exchange = None  # injected later

    def cash_in(self, amount):
        self.cash_balance += amount

    def cash_out(self, amount):
        if amount > self.cash_balance:
            raise ValueError("Insufficient balance")
        self.cash_balance -= amount

    def place_order(self, exchange, instrument, order_type, side, qty, price=None):
        """Place order via exchange; exchange returns order id."""
        return exchange.place_order(self, instrument, order_type, side, qty, price)

    def update_positions(self, trade, instrument):
        qty = trade.qty
        price = trade.price

        old_qty = self.positions.get(instrument, 0)
        old_avg = self.average_cost.get(instrument, 0.0)

        # BUY
        if trade.buy_user_id == self.user_id:
            if old_qty >= 0:
                # increasing long OR opening long
                new_qty = old_qty + qty
                new_avg = (old_qty * old_avg + qty * price) / new_qty if old_qty != 0 else price
            else:
                # covering short
                realised = min(qty, -old_qty) * (old_avg - price)
                self.realised_pnl += realised
                new_qty = old_qty + qty
                new_avg = old_avg if new_qty < 0 else price

            self.cash_balance -= qty * price

        # SELL
        elif trade.sell_user_id == self.user_id:
            if old_qty <= 0:
                # increasing short OR opening short
                new_qty = old_qty - qty
                new_avg = (abs(old_qty) * old_avg + qty * price) / abs(new_qty) if old_qty != 0 else price
            else:
                # selling long
                realised = min(qty, old_qty) * (price - old_avg)
                self.realised_pnl += realised
                new_qty = old_qty - qty
                new_avg = old_avg if new_qty > 0 else price

            self.cash_balance += qty * price

        # Cleanup
        if new_qty == 0:
            self.positions.pop(instrument, None)
            self.average_cost.pop(instrument, None)
        else:
            self.positions[instrument] = new_qty
            self.average_cost[instrument] = new_avg


    # Getters
        
    def get_positions(self):
        """
        Returns:
        {
            instrument: {
                "quantity": int,
                "average_cost": float
            }
        }
        """
        return {
            inst: {
                "quantity": qty,
                "average_cost": self.average_cost[inst]
            }
            for inst, qty in self.positions.items()
        }

    def get_cash_balance(self):
        return self.cash_balance
    
    def get_unrealised_pnl_for_instrument(self, inst):
        if inst not in self.positions:
            print(f"User {self.user_id} does not have a position for instrument {inst}!")
            return None

        ob = self.exchange.order_books.get(inst)
        if ob is None or ob.last_price is None:
            return 0.0

        qty = self.positions[inst]
        avg = self.average_cost[inst]

        return qty * (ob.last_price - avg)
    
    def get_unrealised_pnl(self):
        total = 0.0

        for inst in self.positions:
            total += self.get_unrealised_pnl_for_instrument(inst)

        return total
    
    def get_exposure_for_instrument(self, inst):
        if inst not in self.positions:
            return 0.0

        ob = self.exchange.order_books.get(inst)
        if ob is None or ob.last_price is None:
            return 0.0

        qty = self.positions[inst]
        return abs(qty) * ob.last_price
    
    def get_total_exposure(self):
        total = 0.0

        for inst in self.positions:
            total += self.get_exposure_for_instrument(inst)
        
        return total