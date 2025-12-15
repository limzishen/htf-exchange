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
        
        ob = self.order_books[instrument]
        order_id = ob.add_order(order_type, side, qty, price, user_id=user.user_id)
        return order_id

    def cancel_order(self, user: User, instrument: str, order_id: str):
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist.")
        
        ob = self.order_books[instrument]
        
        if order_id not in ob.order_map:
            print("Order not found in order book!")
            return False
        
        order = ob.order_map[order_id]
        
        # Remove from user's outstanding
        if order.side == "buy":
            user.outstanding_buy[instrument] -= order.qty
        else:
            user.outstanding_sell[instrument] -= order.qty
        
        # Cancel in order book
        return ob.cancel_order(order_id)

    def process_trade(self, trade, instrument):
        """Called by order book whenever a trade occurs"""
        buy_user = self.users.get(trade.buy_user_id)
        sell_user = self.users.get(trade.sell_user_id)
        if buy_user:
            buy_user.update_positions(trade, instrument)
        if sell_user:
            sell_user.update_positions(trade, instrument)
