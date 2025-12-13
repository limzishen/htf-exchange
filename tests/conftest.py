import pytest
from htf_engine.order_book import OrderBook

@pytest.fixture
def ob():
    return OrderBook()