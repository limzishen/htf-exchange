from .order_book import OrderBook
from .orders.order import Order
from .trades.trade import Trade
from .user import User


class Exchange:
    def __init__(self):
        self.users = {}          # user_id -> User
        self.order_books = {}    # instrument -> OrderBook

    def register_user(self, user: User) -> None:
        self.users[user.user_id] = user
        user.exchange = self

    def add_order_book(self, instrument: str, ob: OrderBook) -> None:
        self.order_books[instrument] = ob
        ob.on_trade_callback = lambda trade, ob=ob: self.process_trade(trade, ob.instrument)
        ob.cleanup_discarded_order_callback = lambda order, ob=ob: self.cleanup_discarded_order(order, ob.instrument)

    def place_order(self, user: User, instrument:str, order_type:str, side:str, qty:int, price=None) -> str:
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
        ob = self.order_books[instrument]
        order_id = ob.add_order(order_type, side, qty, price, user_id=user.user_id)
        return order_id

    def cancel_order(self, user: User, instrument: str, order_id: str) -> bool:
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist.")
        
        ob = self.order_books[instrument]

        if order_id not in ob.order_map:
            print("Order not found in order book!")
            return False
        
        order = ob.order_map[order_id]
        
        # Remove from user's outstanding
        if order.side == "buy":
            user.outstanding_buys[instrument] -= order.qty
        else:
            user.outstanding_sells[instrument] -= order.qty
        
        # Cancel in order book
        return ob.cancel_order(order_id)

    def process_trade(self, trade: Trade, instrument:str) -> None:
        """Called by order book whenever a trade occurs"""
        buy_user = self.users.get(trade.buy_user_id)
        sell_user = self.users.get(trade.sell_user_id)
        if buy_user:
            buy_user.update_positions(trade, instrument)
        if sell_user:
            sell_user.update_positions(trade, instrument)
    
    def cleanup_discarded_order(self, order: Order, instrument:str) -> None:
        user = self.users.get(order.user_id)
        if order.is_buy_order():
            outstanding_buys = user.get_outstanding_buys()
            outstanding_buys[instrument] -= order.qty
            if outstanding_buys[instrument] == 0:
                outstanding_buys.pop(instrument)
        else:
            outstanding_sells = user.get_outstanding_sells()
            outstanding_sells[instrument] -= order.qty
            if outstanding_sells[instrument] == 0:
                outstanding_sells.pop(instrument)

