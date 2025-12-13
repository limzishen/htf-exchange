from .order_book import OrderBook
from .user import User


class Exchange:
    def __init__(self):
        self.users = {}          # user_id -> User
        self.order_books = {}    # instrument -> OrderBook

    def register_user(self, user: User):
        self.users[user.user_id] = user
        user.exchange = self

    def add_order_book(self, instrument, ob: OrderBook):
        self.order_books[instrument] = ob
        ob.on_trade_callback = lambda trade, ob=ob: self.process_trade(trade, ob.instrument)

    def place_order(self, user: User, instrument, order_type, side, qty, price=None):
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
    
        # --- CASH / MARGIN CHECK ---
        if side == "buy":
            # For limit/market buy orders, check if user has enough cash
            required_cash = price * qty if price is not None else qty * self.order_books[instrument].best_ask() or 0
            if (1.25 if order_type == "market" else 1) * required_cash > user.cash_balance: # 1.25 safety margin for market orders due to slippage
                raise ValueError(f"User {user.user_id} does not have enough cash to buy {qty} shares of {instrument}")
        elif side == "sell": # Note: cannot turn a long (qty > 0) to a short (qty < 0) in a single sell trade
            # Selling long: check holdings
            current_qty = user.positions.get(instrument, 0)
            if current_qty > 0 and qty > current_qty:
                raise ValueError(f"User {user.user_id} cannot sell {qty} shares of {instrument}; only {current_qty} held")
            # Selling short: allow, credit cash immediately
            if current_qty <= 0:
                user.cash_balance += qty * price  # shorting
        
        ob = self.order_books[instrument]
        order_id = ob.add_order(order_type, side, qty, price, user_id=user.user_id)
        return order_id

    def process_trade(self, trade, instrument):
        """Called by order book whenever a trade occurs"""
        buy_user = self.users.get(trade.buy_user_id)
        sell_user = self.users.get(trade.sell_user_id)
        if buy_user:
            buy_user.update_positions(trade, instrument)
        if sell_user:
            sell_user.update_positions(trade, instrument)
