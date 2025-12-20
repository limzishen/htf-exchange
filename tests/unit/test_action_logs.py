def test_record_register_user(exchange, u1):
    exchange.register_user(u1)
    assert len(u1.user_log._actions) == 1
    assert u1.user_log._actions[0].user_id == u1.user_id
    assert u1.user_log._actions[0].username == u1.username
    assert u1.user_log._actions[0].action == "REGISTER"
    assert u1.user_log._actions[0].user_balance == u1.cash_balance

def test_record_place_order(exchange, u1): 
    exchange.register_user(u1)
    u1.place_order(exchange, "Stock A", "limit", "buy", 10, 10)
    assert u1.user_log._actions[0].action == "REGISTER"
    assert u1.user_log._actions[1].action == "PLACE ORDER"
    assert u1.user_log._actions[1].username == u1.username
    assert u1.user_log._actions[1].user_id == u1.user_id
    assert u1.user_log._actions[1].order_type == "limit"
    assert u1.user_log._actions[1].side == "buy"
    assert u1.user_log._actions[1].quantity == 10
    assert u1.user_log._actions[1].price == 10
    assert u1.user_log._actions[1].instrument_id == "Stock A"


def test_record_cash_in(u1): 
    u1.cash_in(100)
    assert u1.user_log._actions[0].action == "CASH IN"
    assert u1.user_log._actions[0].username == u1.username
    assert u1.user_log._actions[0].user_id == u1.user_id
    assert u1.user_log._actions[0].amount_added == 100
    assert u1.user_log._actions[0].curr_balance == u1.cash_balance

def test_record_cash_out(u1): 
    u1.cash_out(100)
    assert u1.user_log._actions[0].action == "CASH OUT"  
    assert u1.user_log._actions[0].username == u1.username
    assert u1.user_log._actions[0].user_id == u1.user_id
    assert u1.user_log._actions[0].amount_removed == 100
    assert u1.user_log._actions[0].curr_balance == u1.cash_balance

def test_record_cancel_order(exchange, u1): 
    exchange.register_user(u1)
    oid = u1.place_order(exchange, "Stock A", "limit", "buy", 10, 10)
    u1.cancel_order(oid, "Stock A")
    print(u1.user_log)

    assert u1.user_log._actions[0].action == "REGISTER"
    assert u1.user_log._actions[1].action == "PLACE ORDER"
    assert u1.user_log._actions[2].action == "CANCEL ORDER"
    assert u1.user_log._actions[2].username == u1.username
    assert u1.user_log._actions[2].user_id == u1.user_id
    assert u1.user_log._actions[2].order_id == oid
    assert u1.user_log._actions[2].instrument_id == "Stock A" 







