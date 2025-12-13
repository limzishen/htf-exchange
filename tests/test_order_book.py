from htf_engine.order_book import OrderBook

# ========================================================
#                         TESTS
# ========================================================

print("=== Test 1: Insert non-crossing orders ===")
ob = OrderBook("NVDA")

ob.add_order("limit", "buy", 5, 95)
ob.add_order("limit", "buy", 3, 100)
ob.add_order("limit", "buy", 5, 90)
ob.add_order("limit", "sell", 4, 105)
ob.add_order("limit", "sell", 9, 123)
ob.add_order("limit", "sell", 2, 110)

assert ob.best_bid() == 100
assert ob.best_ask() == 105
print(ob)


print("\n=== Test 2: Add crossing buy order ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 5, 100)
ob.add_order("limit", "buy", 3, 99)
ob.add_order("limit", "sell", 4, 105)
ob.add_order("limit", "sell", 2, 110)
ob.add_order("limit", "buy", 20, 110)  # this crosses all asks

assert ob.best_bid() == 110
assert ob.best_ask() is None
print(ob)


print("\n=== Test 3: FIFO same-price queue ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 5, 100)
ob.add_order("limit", "buy", 50, 100)
ob.add_order("limit", "sell", 10, 105)
ob.add_order("limit", "sell", 20, 105)
ob.add_order("limit", "sell", 50, 110)
ob.add_order("limit", "sell", 250, 115)

print("Before crossing:", ob.get_all_pending_orders())
ob.add_order("limit", "sell", 3, 100)  # hits ID 0 first
print("After 1st cross:", ob.get_all_pending_orders())
ob.add_order("limit", "sell", 42, 100)  # hits ID 1 next
print("After 2nd cross:", ob.get_all_pending_orders())
print(ob)


print("\n=== Test 4: Cancel order ===")
ob = OrderBook("NVDA")
target = ob.add_order("limit", "buy", 5, 100)
ob.add_order("limit", "buy", 50, 100)
print("Before cancel:", ob.get_all_pending_orders())
ob.cancel_order(target)
ob.add_order("limit", "sell", 10, 105)
ob.add_order("limit", "sell", 20, 105)

print(ob)

print("After cancel:", ob.get_all_pending_orders())
print(ob)

print("\n=== Test 4.5: Cancel order ===")
ob = OrderBook("NVDA")
target = ob.add_order("limit", "buy", 5, 100)
print(target)
print(ob.cancel_order(target))
print(ob.best_bid())
print(ob)
print(ob.best_bids)
print(ob.bids)


print("\n=== Test 5: Simple partial match ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 55, 100)
ob.add_order("limit", "sell", 40, 110)
ob.add_order("limit", "sell", 10, 105)
print("Best bid:", ob.best_bid())
print("Best ask:", ob.best_ask())


print("\n=== Test 6: Partial fill on both sides ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "sell", 25, 100)
print(ob.get_all_pending_orders())
print(ob)


print("\n=== Test 7: Sweep through multiple ask levels ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "sell", 5, 101)
ob.add_order("limit", "sell", 5, 102)
ob.add_order("limit", "sell", 5, 103)
ob.add_order("limit", "buy", 20, 200)  # should take 5@101, 5@102, 5@103
print(ob)
print("Last Traded Price:", ob.last_price)


print("\n=== Test 8: Sweep through multiple bid levels ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 5, 99)
ob.add_order("limit", "buy", 5, 97)
ob.add_order("limit", "buy", 5, 98)
ob.add_order("limit", "sell", 20, 90)  # should take 5@99, 5@98, 5@97
print(ob)
print("Last Traded Price:", ob.last_price)


print("\n=== Test 9: Cancel middle of FIFO queue ===")
ob = OrderBook("NVDA")
o1 = ob.add_order("limit", "buy", 5, 100)
o2 = ob.add_order("limit", "buy", 6, 100)
o3 = ob.add_order("limit", "buy", 7, 100)
print("Remaining:", ob.get_all_pending_orders())
print(ob)
ob.cancel_order(o2)
print("Remaining:", ob.get_all_pending_orders())
print(ob)


print("\n=== Test 10: Best bid/ask when book becomes empty ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 5, 100)
ob.add_order("limit", "sell", 5, 100)  # trades and empties book
print("best bid:", ob.best_bid())
print("best ask:", ob.best_ask())


print("\n=== Test 11: Stress FIFO correctness ===")
ob = OrderBook("NVDA")
for _ in range(5):
    ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "sell", 42, 100)  # should eat 4 orders fully, last partially
print([str(x) for x in ob.get_all_pending_orders()])
print(ob)


print("\n=== Test 12: Large imbalance (big ask hits many bids) ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "buy", 10, 99)
ob.add_order("limit", "buy", 10, 98)
ob.add_order("limit", "sell", 100, 95)  # Should clear all bids
print(ob)


print("\n=== Test 13: Add then cancel everything ===")
ob = OrderBook("NVDA")
o1 = ob.add_order("limit", "sell", 10, 105)
o2 = ob.add_order("limit", "sell", 20, 106)
ob.cancel_order(o1)
ob.cancel_order(o2)
print(ob)


print("\n=== Test 14: Cancel non-existent order ===")
ob = OrderBook("NVDA")
o1 = ob.add_order("limit", "sell", 10, 105)
o2 = ob.add_order("limit", "sell", 20, 106)
ob.cancel_order("dummy")  # Order not found!
print(ob)


print("\n=== Test 15: Multiple partials before level removed ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 30, 100)
ob.add_order("limit", "sell", 10, 100)
ob.add_order("limit", "sell", 10, 50)
ob.add_order("limit", "sell", 10, 80)  # last fill empties buy side
print(ob)
print(ob.last_price)


print("\n=== Test 16: Large imbalance with same price ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 100, 100)
print(ob)


print("\n=== Test 16: Large imbalance with same price ===")
ob = OrderBook("NVDA")
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "buy", 10, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 1, 100)
ob.add_order("limit", "sell", 1, 100)
print(ob)
ob.add_order("market", "sell", 100)
print(ob)