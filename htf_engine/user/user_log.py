from datetime import datetime
from typing import List

from htf_engine.user.action_log.user_action import UserAction
from htf_engine.user.action_log.register_user_action  import RegisterUserAction
from htf_engine.user.action_log.cash_in_action import CashInAction
from htf_engine.user.action_log.cash_out_action import CashOutAction
from htf_engine.user.action_log.cancel_order_action import CancelOrderAction
from htf_engine.user.action_log.place_order_action import PlaceOrderAction

class UserLog:
    def __init__(self, user_id, username):
        self._actions: List[UserAction] = []
        self.user_id = user_id 
        self.username = username

    def _get_now(self) -> datetime:
        return datetime.now()

    def record_register_user(self, user_balance: float):
        action = RegisterUserAction(
            timestamp=self._get_now(),
            user_id=self.user_id,
            username=self.username,
            action="REGISTER",
            user_balance=user_balance
        )
        self._actions.append(action)

    def record_place_order(self, instrument_id: str, order_type: str, side: str, quantity: int, price: float):
        action = PlaceOrderAction(
            timestamp=self._get_now(),
            user_id=self.user_id,
            username=self.username,
            action="PLACE ORDER",
            instrument_id=instrument_id,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price
        )
        self._actions.append(action)


    def record_cash_in(self, amount: float, new_balance: float):
        action = CashInAction(
            timestamp=self._get_now(),
            user_id=self.user_id,
            username=self.username,
            action="CASH IN",
            amount_added=amount,
            curr_balance=new_balance
        )
        self._actions.append(action)

    def record_cash_out(self, amount: float, new_balance: float):
        action = CashOutAction(
            timestamp=self._get_now(),
            user_id=self.user_id,
            username=self.username,
            action="CASH OUT",
            amount_removed=amount,
            curr_balance=new_balance
        )
        self._actions.append(action)

    def record_cancel_order(self, order_id: str, instrument_id: str):
        action = CancelOrderAction(
            timestamp=self._get_now(),
            user_id=self.user_id,
            username=self.username,
            action="CANCEL ORDER",
            order_id=order_id,
            instrument_id=instrument_id
        )
        self._actions.append(action)

    def retrieve_log(self) -> tuple:
        return tuple(self._actions)

    def retrieve_simple_log(self) -> tuple:
        return tuple(map(str, self._actions))

    def __str__(self):
        """Prints user actions"""
        return "\n".join(str(action) for action in self._actions)