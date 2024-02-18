# flask run --debug
"""
{% extends "base.html" %}

{% block content %}

{% endblock %}
"""

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_alembic import Alembic
from manager import Manager
from config import Config
from datetime import datetime
import os as system


# db = Manager
warehouse = Manager(name="warehouse_file")

config_obj = Config()
config_obj.create_files()
manager = Manager(config_obj)

data = manager.load_data()

new_data = {}

app = Flask(__name__)
app.config["SECRET_KEY"] = "mySecretKey"


# CREATING NEW DBs:
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"

# class Base(DeclarativeBase):
#   pass
#
# db_balance = SQLAlchemy(app, model_class=Base)
#db.init_app(app)


db = SQLAlchemy()
db.init_app(app)


alembic = Alembic()
alembic.init_app(app, db)


class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float(127), nullable=False)


class Warehoue(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)


@app.route("/")
def index():
    data = manager.load_data()
    balance = db.session.query(Balance).all()
    products = db.session.query(Warehoue).all()
    stock = {"idx": [], "product_name": [], "product_price": [], "product_quantity": []}
    idx = 0

    for product in products:
        product_name = products[idx].product_name
        product_price = products[idx].product_price
        product_quantity = products[idx].product_quantity

        stock['idx'].append(idx)
        stock['product_name'].append(product_name)
        stock['product_price'].append(product_price)
        stock['product_quantity'].append(product_quantity)
        idx += 1


    # with app.app_context():
    #     balance = db_balance.create_all()
    #
    # db_balance.session.add(DB_Balance(v_balance=1))
    # db.session.commit()

    # actual_balance = db_balance.session.execute(db_balance.select(DB_Balance)).scalars()
    # print(f"++++++++++++++++++++++BALANCE: {DB_Balance.query}")

    # Get the Username logged on system.
    user = system.getlogin()

    return render_template("index.html", title="Current stock level:", stock=stock, balance=balance, user=user) #, actual_balance=actual_balance)


@app.route("/purchase/", methods=["POST", "GET"])
def purchase():
    data = manager.load_data()
    balance = data["v_balance"]
    user = system.getlogin()
    if request.method == "POST":
        form_values = request.form
        new_data = {
            "user": user,
            "v_name": str(form_values["v_name"]),
            "v_quantity": int(form_values["v_quantity"]),
            "v_price": float(form_values["v_price"]),
        }

        user = user
        v_name = new_data["v_name"]
        v_quantity = new_data["v_quantity"]
        v_price = new_data["v_price"]
        total_price = v_price * v_quantity

        if total_price > balance:
            print(f"Sorry, you do not have a balance enough to make this purchase.\n"
                  f"Your actual balance is {balance}.")
            message = f"WARNING: Balance is not enough  enough to make this purchase."
            return render_template("message.html", message=message, balance=balance, user=user)
        else:
            manager.f_purchase(new_data)
            message = f"Purchased '{v_quantity}' '{v_name}'."
            return render_template("message.html", message=message, balance=balance, user=user)

    return render_template("purchase.html", title="PURCHASE", balance=balance, user=user)

@app.route("/sale/", methods=["POST", "GET"])
def sale():
    user = system.getlogin()
    success = False
    data = manager.load_data()
    balance = data["v_balance"]
    stock = data["v_warehouse"]
    if request.method == "POST":
        if request.form.get("s_name"):
            new_sale = {
                "user": user,
                "s_name": request.form["s_name"],
                "s_quantity": request.form["s_quantity"]
            }
            if int(new_sale["s_quantity"]) > stock[new_sale["s_name"]]["v_quantity"]:
                print(f"WARNING: Not enough {new_sale['s_name']} to sell.\n")
                message = f"WARNING: Not enough '{new_sale['s_name']}' to sell.\n"
                return render_template("message.html", message=message, balance=balance, user=user)
            else:
                success = manager.f_sale(new_sale)

            if not success:
                # flash(f"Sorry no more '{new_sale['s_name']}' available!")
                message = f"WARNING: No more '{new_sale['s_name']}' available!"
                return render_template("message.html", message=message, balance=balance, user=user)

            else:
                # flash(f"Successfully sold '{new_sale['s_quantity']}' items of '{new_sale['s_name']}'")
                message = f"Successfully sold '{new_sale['s_quantity']}' items of '{new_sale['s_name']}'"
                return render_template("message.html", message=message, balance=balance, user=user)

        return redirect(url_for("index"))


@app.route("/balance/", methods=["POST", "GET"])
def balance():
    user = system.getlogin()
    data = manager.load_data()
    balance = data["v_balance"]
    if request.method == "POST":
        form_values = request.form
        new_balance = {
            "user": user,
            "v_value": float(form_values["v_value"]),
            "v_action": int(form_values["v_action"]),
        }

        if new_balance["v_action"] == 2 and new_balance["v_value"] > balance:
            message = f"WARNING: Your balance is too low. Maximum amount you can withdraw is: {balance}."
            return render_template("message.html", message=message, balance=balance, user=user)
        else:
            manager.f_balance(new_balance)
            if new_balance["v_action"] == 2:
                msg = "Withdraw"
            else:
                msg = "Added"
            message = f"{msg} '{new_balance['v_value']}' successfully."
            return render_template("message.html", message=message, balance=balance, user=user)

    return render_template("balance.html", title="BALANCE", balance=balance, user=user)


@app.route("/history/", defaults={"line_from": None, "line_to": None})
@app.route("/history/", methods=["POST", "GET"])
def history():
    user = system.getlogin()
    data = manager.load_data()
    history = data.get("v_review", [])
    balance = data.get("v_balance", 0)

    new_history = {"date_transaction": [], "user": [], "transaction": [], "v_value": []}

    if request.method == "POST":
        form_values = request.form
        filtered_history = []
        new_data = {
            "line_from": str(form_values["line_from"]),
            "line_to": str(form_values["line_to"]),
        }
        line_from = new_data["line_from"].replace('-','/')

        if new_data["line_to"] is "":
            line_to = datetime.today()
            line_to = line_to.strftime("%Y/%m/%d")

        else:
            line_to = new_data["line_to"].replace('-','/')
        line_to = line_to + ' 23:59:59'

        new_history = manager.f_review(history)

        if line_from is "" and line_to is "":
            filtered_history = new_history

        else:
            index = 0

            filtered_data = {'date_transaction': [], 'user': [], 'transaction': [], 'v_value': []}
            for valor in new_history['date_transaction']:
                index += 1
                if line_from <= valor <= line_to:
                    if valor in new_history['date_transaction']:
                        index = new_history['date_transaction'].index(valor)
                        filtered_data['date_transaction'].append(new_history['date_transaction'][index])
                        filtered_data['user'].append(new_history['user'][index])
                        filtered_data['transaction'].append(new_history['transaction'][index])
                        filtered_data['v_value'].append(new_history['v_value'][index])

        new_history=filtered_data

    return render_template("history.html", title="HISTORY", history=history, balance=balance, new_history=new_history, user=user)
