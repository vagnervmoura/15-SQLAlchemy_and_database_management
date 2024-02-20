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


db = SQLAlchemy()
db.init_app(app)

alembic = Alembic()
alembic.init_app(app, db)


class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float(127), nullable=False)


class Warehoue(db.Model):
    # product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, primary_key=True)
    product_price = db.Column(db.Float, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)


@app.route("/")
def index():
    data = manager.load_data()
    balance = load_balance()
    warehouse = db.session.query(Warehoue).all()
    stock = {"idx": [], "product_name": [], "product_price": [], "product_quantity": []}
    idx = 0

    for product in warehouse:
        product_name = warehouse[idx].product_name
        product_price = warehouse[idx].product_price
        product_quantity = warehouse[idx].product_quantity

        stock['idx'].append(idx)
        stock['product_name'].append(product_name)
        stock['product_price'].append(product_price)
        stock['product_quantity'].append(product_quantity)
        idx += 1

    # Get the Username logged on system.
    user = system.getlogin()

    return render_template("index.html", title="Current stock level:", stock=stock, balance=str(balance), user=user) #, actual_balance=actual_balance)


@app.route("/purchase/", methods=["POST", "GET"])
def purchase():
    data = manager.load_data()
    # balance = data["v_balance"]
    balance = load_balance()
    stock = load_stock()
    warehouse = db.session.query(Warehoue).all()
    print(f"WAREHOUSE: {warehouse}")
    user = system.getlogin()
    if request.method == "POST":
        form_values = request.form
        new_purchase = {
            "user": user,
            "v_name": str(form_values["v_name"]),
            "v_quantity": int(form_values["v_quantity"]),
            "v_price": float(form_values["v_price"]),
        }

        user = user
        v_name = new_purchase["v_name"].lower()
        v_quantity = new_purchase["v_quantity"]
        v_price = new_purchase["v_price"]
        total_price = v_price * v_quantity

        if total_price > balance:
            print(f"Sorry, you do not have a balance enough to make this purchase.\n"
                  f"Your actual balance is {balance}.")
            message = f"WARNING: Balance is not enough  enough to make this purchase."
            return render_template("message.html", message=message, balance=str(balance), user=user)
        else:
            print("+" * 300)
            print("+" * 300)
            print(f"NEW_PURCHASE - V_NAME: {new_purchase['v_name']}")
            print(f"STOCK - PRODUCT_NAME: {stock['product_name']}")
            print(f"STOCK: {stock}")
            id = Warehoue.query.get(new_purchase["v_name"])
            print(f"ID: {id}")
            if new_purchase["v_name"] in stock['product_name']:
                idx = stock['product_name'].index(new_purchase["v_name"])
                existing_product = warehouse[idx]
                existing_product.product_quantity += new_purchase["v_quantity"]
                existing_product.product_price = new_purchase["v_price"]
                db.session.commit()

            else:
                print("INTO ELSE")
                new_purchase = (Warehoue(product_name=v_name, product_price=v_price, product_quantity=v_quantity))
                db.session.add(new_purchase)
                db.session.commit()

            new_balance = balance - total_price
            update_balance(1, new_balance)


            # manager.f_purchase(new_purchase)
            # message = f"Purchased '{v_quantity}' '{v_name}'."
            # return render_template("message.html", message=message, balance=str(balance), user=user)

    return render_template("purchase.html", title="PURCHASE", balance=str(balance), user=user)

@app.route("/sale/", methods=["POST", "GET"])
def sale():
    user = system.getlogin()
    success = False
    data = manager.load_data()
    # balance = data["v_balance"]
    balance = load_balance()
    stock = load_stock()
    warehouse = db.session.query(Warehoue).all()
    print(f"WAREHOUSE: {warehouse}")
    # stock = data["v_warehouse"]

    if request.method == "POST":
        print(request.form["s_name"])

        if request.form.get("s_name"):
            print("INTO IF")
            new_sale = {
                "user": user,
                "product_name": request.form["s_name"],
                "product_quantity": request.form["s_quantity"]
            }
            print(new_sale["product_name"])


            if new_sale["product_name"] in stock['product_name']:
                idx = stock['product_name'].index(new_sale["product_name"])
                stock_quantity = warehouse[idx].product_quantity
                print(f"EXISTING PRODUCT: {stock_quantity}")
                if int(new_sale["product_quantity"]) > int(stock_quantity):
                    print(f"Sorry, you do not have enough {new_sale['product_name']} to sell.\n")
                    success = False
                    message = f"WARNING: you do not have enough {new_sale['product_name']} to sell."
                    return render_template("message.html", message=message, balance=str(balance), user=user)
                else:
                    print("SELLING")
                    existing_product = warehouse[idx]
                    existing_product.product_quantity = int(stock_quantity) - int(new_sale["product_quantity"])
                    existing_product.product_price = existing_product.product_price
                    total_price = (existing_product.product_price * int(new_sale["product_quantity"])) * 1.5
                    if int(stock_quantity) == int(new_sale["product_quantity"]):
                        db.session.delete(warehouse[idx])
                    print(f"IDX: {idx}")
                    db.session.commit()
                    new_balance = balance + total_price
                    update_balance(1, new_balance)
                    success = True
                    message = f"Successfully sold '{new_sale['product_quantity']}' items of '{new_sale['product_name']}'"
                    return render_template("message.html", message=message, balance=str(balance), user=user)

            else:
                product_quantity = int(new_sale["product_quantity"])
                if product_quantity > warehouse["product_name"]["product_quantity"]:
                    print(f"Sorry, you do not have enough {new_sale['product_name']} to sell.\n")
                    success = False
                    return data
                v_price = warehouse["product_name"]["product_price"]
                total_price = v_price * product_quantity
                success = True

                success = manager.f_sale(new_sale)

            if not success:
                message = f"WARNING: No more '{new_sale['product_name']}' available!"
                return render_template("message.html", message=message, balance=str(balance), user=user)

            else:
                message = f"Successfully sold '{new_sale['product_quantity']}' items of '{new_sale['product_name']}'"
                return render_template("message.html", message=message, balance=str(balance), user=user)

        return redirect(url_for("index"))


@app.route("/balance/", methods=["POST", "GET"])
def balance():
    user = system.getlogin()
    data = manager.load_data()
    balance = load_balance()

    if request.method == "POST":
        form_values = request.form
        new_balance = {
            "user": user,
            "value": float(form_values["value"]),
            "action": int(form_values["action"]),
            "balance": balance,
        }

        if new_balance["action"] == 2 and new_balance["value"] > new_balance["balance"]:
            message = f"WARNING: Your balance is too low. Maximum amount you can withdraw is: {balance}."
            return render_template("message.html", message=message, balance=str(balance), user=user)
        else:
            if new_balance["action"] == 2:
                new_balance["value"] -= new_balance["value"]*2

            balance = float(balance) + float(new_balance['value'])
            manager.f_balance(new_balance)
            if new_balance["action"] == 2:
                msg = "Withdraw"
            else:
                msg = "Added"
            message = f"{msg} '{new_balance['value']}' successfully."

            balance = update_balance("1", balance)

            return render_template("message.html", message=message, balance=str(balance), user=user)
        return redirect(url_for("index"))
    return render_template("balance.html", title="BALANCE", balance=str(balance), user=user)


@app.route("/history/", defaults={"line_from": None, "line_to": None})
@app.route("/history/", methods=["POST", "GET"])
def history():
    user = system.getlogin()
    data = manager.load_data()
    history = data.get("v_review", [])
    # balance = data.get("v_balance", 0)
    balance = load_balance()

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

    return render_template("history.html", title="HISTORY", history=history, balance=str(balance), new_history=new_history, user=user)


def load_balance():
    if not db.session.query(Balance).first():
        update_balance(1, 0)

    balance = db.session.query(Balance.balance).first()
    balance = balance.balance
    return balance

def update_balance(id, balance):
    try:
        # Try to retrieve the balance entry from the database
        balance_ID = Balance.query.get(id)
        print(f"ID: {id}")
        print(f"BALANCE: {balance}")
        print(f"BALANCE_ENTRY: {balance_ID}")

        if balance_ID:
            # If the entry exists, update its balance
            print(f"INTO IF - BALANCE ID: {balance_ID}")
            balance_ID.balance = balance
        else:
            # If the entry does not exist, create a new one
            print(f"INTO ELSE - BALANCE ID: {balance_ID}")
            balance_ID = Balance(id=id, balance=balance)
            db.session.add(balance_ID)

        # Commit changes to the database
        db.session.commit()
    except Exception as e:
        # Handle exceptions
        print(f"Error updating balance: {str(e)}")
        db.session.rollback()  # Rollback changes in case of an error


def load_stock():
    warehouse = db.session.query(Warehoue).all()
    idx = 0
    stock = {"idx": [], "product_name": [], "product_price": [], "product_quantity": []}
    for product in warehouse:
        product_name = warehouse[idx].product_name
        product_price = warehouse[idx].product_price
        product_quantity = warehouse[idx].product_quantity

        stock['idx'].append(idx)
        stock['product_name'].append(product_name)
        stock['product_price'].append(product_price)
        stock['product_quantity'].append(product_quantity)
        idx += 1
    return stock