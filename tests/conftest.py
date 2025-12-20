import pytest
from htf_engine.exchange import Exchange
from htf_engine.order_book import OrderBook
from htf_engine.user.user import User

@pytest.fixture
def ob():
    return OrderBook("NVDA", enable_stp=False)

@pytest.fixture
def exchange():
    e = Exchange(fee=10)
    e.add_order_book("Stock A", OrderBook("Stock A"))
    e.add_order_book("Stock B", OrderBook("Stock B"))
    e.add_order_book("Stock C", OrderBook("Stock C"))
    return e

@pytest.fixture
def u1():
    return User("ceo_of_fumbling", "Zi Shen", 5000)

@pytest.fixture
def u2():
    return User("cheater6767", "Clemen", 5000)

@pytest.fixture
def u3():
    return User("csgod", "Brian", 5000)
