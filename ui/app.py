import os
import sys

# allow importing htf-engine
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from htf_engine.exchange import Exchange
from htf_engine.user.user import User
from htf_engine.order_book import OrderBook

app = Flask(__name__)
CORS(app)

# ------------------------
# BOOTSTRAP ENGINE
# ------------------------

exchange = Exchange()

INSTRUMENT = "AAPL"

order_book = OrderBook(instrument=INSTRUMENT)
exchange.add_order_book(INSTRUMENT, order_book)

# Create user instances with name, display name, and initial balance
brian = User("brian", "Brian", 1_000_000)
clemen = User("clemen", "Clemen", 1_000_000)
charles = User("charles", "Charles", 1_000_000)
nuowen = User("nuowen", "Nuowen", 1_000_000)
zishen = User("zishen", "Zishen", 1_000_000)

# Register users with exchange
exchange.register_user(brian)
exchange.register_user(clemen)
exchange.register_user(charles)
exchange.register_user(nuowen)
exchange.register_user(zishen)

# Dictionary of users for easy access
USERS = {
    "brian": brian,
    "clemen": clemen,
    "charles": charles,
    "nuowen": nuowen,
    "zishen": zishen
}

# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/place_order", methods=["POST"])
def place_order():
    data = request.json

    user_id = data["user_id"]
    instrument = data["instrument"]
    order_type = data["order_type"]
    side = data["side"]               # buy / sell
    qty = int(data["qty"])
    price = data.get("price")

    if price != "":
        price = float(price)

    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "Unknown user"}), 400

    try:
        order_id = user.place_order(
            instrument=instrument,
            order_type=order_type,
            side=side,
            qty=qty,
            price=(price if order_type != "market" else None)
        )

        return jsonify({
            "status": "ok",
            "order_id": order_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/positions/<user_id>")
def positions(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "Unknown user"}), 400

    return jsonify({
        "positions": user.get_positions(),
        "outstanding_buys": dict(user.get_outstanding_buys()),
        "outstanding_sells": dict(user.get_outstanding_sells()),
        "realised_pnl": user.get_realised_pnl(),
        "unrealised_pnl": user.get_unrealised_pnl()
    })


@app.route("/book")
def book():
    return jsonify(order_book.snapshot())


if __name__ == "__main__":
    app.run(debug=True)
