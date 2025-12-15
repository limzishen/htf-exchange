from collections import defaultdict

class User:
    def __init__(self, user_id, username, cash_balance=0.0):
        self.user_id = user_id
        self.username = username
        self.cash_balance = cash_balance            # TODO... can ignore for now
        self.realised_pnl = 0.0

        self.positions = {}                         # instrument -> quantity
        self.average_cost = {}                      # instrument -> avg cost
        self.outstanding_buy = defaultdict(int)     # instrument -> qty
        self.outstanding_sell = defaultdict(int)    # instrument -> qty
        
        self.exchange = None  # injected later

    def cash_in(self, amount):
        self.cash_balance += amount

    def cash_out(self, amount):
        if amount > self.cash_balance:
            raise ValueError("Insufficient balance")
        self.cash_balance -= amount
    
    def can_place_order(self, instrument, side, qty):
        limit = 100     # TODO: change limit to be configurable

        current = self.positions.get(instrument, 0)
        outstanding_buy = self.outstanding_buy.get(instrument, 0)
        outstanding_sell = self.outstanding_sell.get(instrument, 0)

        if side == "buy":
            return qty <= limit - current - outstanding_buy
        else:  # sell
            return qty <= limit + current - outstanding_sell


    def place_order(self, exchange, instrument, order_type, side, qty, price=None):
        """Place order via exchange; exchange returns order id."""
        
        # --- CHECK LIMIT ---
        if not self.can_place_order(instrument, side, qty):
            raise ValueError(f"User {self.user_id} cannot place order: would exceed position limit")
        
        # --- UPDATE OUTSTANDING ---
        if side == "buy":
            self.outstanding_buy[instrument] += qty
        else:
            self.outstanding_sell[instrument] += qty

        # Place order through exchange
        order_id = exchange.place_order(self, instrument, order_type, side, qty, price)
        return order_id

    def cancel_order(self, order_id, instrument=None):
        if self.exchange is None:
            raise ValueError("User is not registered with any exchange.")
        
        if instrument:
            return self.exchange.cancel_order(self, instrument, order_id)
        
        # If instrument not provided, search all order books
        for inst, ob in self.exchange.order_books.items():
            if order_id in ob.order_map:
                return self.exchange.cancel_order(self, inst, order_id)
        
        print("Order ID not found!")
        return False

    def update_positions(self, trade, instrument):
        qty = trade.qty
        price = trade.price

        old_qty = self.positions.get(instrument, 0)
        old_avg = self.average_cost.get(instrument, 0.0)

        # BUY
        if trade.buy_user_id == self.user_id:
            self.outstanding_buy[instrument] -= qty

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
            self.outstanding_sell[instrument] -= qty

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
    
    def get_realised_pnl(self):
        return self.realised_pnl
    
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