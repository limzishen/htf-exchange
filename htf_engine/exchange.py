from .order_book import OrderBook
from .user.user import User
from .orders.order import Order
from .trades.trade import Trade


class Exchange:
    def __init__(self, fee=0):
        self.users = {}          # user_id -> User
        self.order_books = {}    # instrument -> OrderBook
        self.fee = fee
        self.balance = 0

    def register_user(self, user: User) -> bool:
        if user.user_id in self.users:
            return False

        self.users[user.user_id] = user
        user.register()
        user.exchange = self
        user.place_order_callback = self.place_order
        user.cancel_order_callback = self.cancel_order
        user.modify_order_callback = self.modify_order
        return True

    def add_order_book(self, instrument: str, ob: OrderBook) -> None:
        self.order_books[instrument] = ob
        ob.on_trade_callback = lambda trade, ob=ob: self.process_trade(trade, ob.instrument)
        ob.cleanup_discarded_order_callback = lambda order, ob=ob: self.cleanup_discarded_order(order, ob.instrument)

    def place_order(self, user_id: str, instrument:str, order_type:str, side:str, qty:int, price=None) -> str:
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
        ob = self.order_books[instrument]
        order_id = ob.add_order(order_type, side, qty, price, user_id=user_id)
        return order_id

    def modify_order(self, user_id: str, instrument: str, order_id: str, new_qty: int, new_price: float) -> bool: 
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
        
        if instrument not in self.order_books: 
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
        ob = self.order_books[instrument]
        if order_id not in ob.order_map:
            print("Order not found in order book!")
            return False

        prev_order = ob.order_map[order_id]
        qty_change = new_qty - prev_order.qty
        ob.modify_order(order_id, new_qty,new_price)
        
        if qty_change > 0:
            self.users[user_id].increase_outstanding_buys(instrument, qty_change)

        if qty_change < 0:
            self.users[user_id].reduce_outstanding_buys(instrument, -qty_change)
        
        return True
    
    def cancel_order(self, user_id: str, instrument: str, order_id: str) -> bool:
        if user_id not in self.users:
            raise ValueError(f"User '{user_id}' is not registered with exchange.")
            
        if instrument not in self.order_books:
            raise ValueError(f"Instrument '{instrument}' does not exist in the exchange.")
        
        ob = self.order_books[instrument]

        if order_id not in ob.order_map:
            print("Order not found in order book!")
            return False
        
        order = ob.order_map[order_id]
        
        # Remove from user's outstanding
        if order.side == "buy":
            self.users[user_id].reduce_outstanding_buys(instrument, order.qty)
        else:
            self.users[user_id].reduce_outstanding_sells(instrument, order.qty)
        
        # Cancel in order book
        return ob.cancel_order(order_id)

    def process_trade(self, trade: Trade, instrument:str) -> None:
        """Called by order book whenever a trade occurs"""
        buy_user = self.users.get(trade.buy_user_id)
        sell_user = self.users.get(trade.sell_user_id)
        if buy_user:
            buy_user.update_positions_and_cash_balance(trade, instrument, self.fee)
            self._earn_fee()
        if sell_user:
            sell_user.update_positions_and_cash_balance(trade, instrument, self.fee)
            self._earn_fee()
    
    def cleanup_discarded_order(self, order: Order, instrument: str) -> None:
        user = self.users.get(order.user_id)

        if order.is_buy_order():
            user.reduce_outstanding_buys(instrument, order.qty)
        else:
            user.reduce_outstanding_sells(instrument, order.qty)

    def _earn_fee(self) -> None:
        self.balance += self.fee
    
    def change_fee(self, new_fee: int) -> None:
        self.fee = new_fee
