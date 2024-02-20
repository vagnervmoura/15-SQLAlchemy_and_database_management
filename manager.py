import os
import json
import ast  # For literal_eval
from datetime import datetime

import app
from config import Config
#from app import Balance
#from app import db
from sqlalchemy import update
#from app import purchase
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from flask_alembic import Alembic

db = SQLAlchemy()
#balance = db.session.query(Balance).all()


class Manager:
    def __init__(self, name, config_obj=None):
        if config_obj is not None:
            self.balance_file = config_obj.balance_file
            self.warehouse_file = config_obj.warehouse_file
            self.review_file = config_obj.review_file
        else:
            # Set default file paths if config_obj is not provided
            self.balance_file = "db_balance.sqlite"
            self.warehouse_file = "warehouse.txt"
            self.review_file = "review.txt"


    ##########################################  START OF DECORATORs  ##########################################
    def add_to_review(self, transaction):
        data = self.load_data()
        v_review = data.get("v_review", [])
        v_review.append(transaction)
        data["v_review"] = v_review
        self.save_data(data)

        ## log_transaction:
        ### This decorator logs the details of the transaction (timestamp, type, and value) to the review file.
        ### It uses the function name as the transaction description.
        def log_transaction(func):
            def wrapper(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                date_transaction = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                transaction_desc = func.__name__.capitalize()  # Using the function name as the transaction description
                value = kwargs.get("value", 0)
                self.add_to_review(f"{date_transaction};{transaction_desc};{value}")
                return result

            return wrapper

        ## validate_quantity:
        ### This decorator ensures that the quantity provided in the quantity keyword argument is non-negative.
        ### If a negative quantity is detected, it prints an error message and skips the execution of the decorated function.
        def validate_quantity(func):
            def wrapper(self, *args, **kwargs):
                quantity = kwargs.get("quantity", 0)
                if quantity < 0:
                    print("Invalid quantity. Please enter a non-negative quantity.")
                    return
                return func(self, *args, **kwargs)

            return wrapper

        def validate_price(func):
            def wrapper(self, *args, **kwargs):
                price = kwargs.get("price", 0)
                if price < 0:
                    print("Invalid price. Please enter a non-negative price.")
                    return
                return func(self, *args, **kwargs)

            return wrapper

    ##########################################  END OF DECORATORs  ##########################################


    def load_data(self):
        Config.create_files(self)

        def load_file(file_path, default_value):
            try:
                with open(file_path, "r") as file:
                    return ast.literal_eval(file.read().strip())
            except (FileNotFoundError, ValueError, SyntaxError):
                print(f"Error loading {file_path}. Initializing to {default_value}.")
                return default_value

        v_balance = load_file(self.balance_file, 0)
        v_warehouse = load_file(self.warehouse_file, {})
        v_review = load_file(self.review_file, [])
        return {"v_balance": v_balance, "v_warehouse": v_warehouse, "v_review": v_review}

    def save_data(self, data):
        def save_file(file_path, content):
            try:
                with open(file_path, "w") as file:
                    file.write(str(content))
            except Exception as e:
                print(f"Error saving data to {file_path}: {e}")

        save_file(self.balance_file, data["v_balance"])
        save_file(self.warehouse_file, data["v_warehouse"])
        save_file(self.review_file, data["v_review"])

    def add_transaction(self, user, data, transaction_type, value, balance, product_name="", quantity=0):
        user = user
        review = data.get("v_review", [])
        date_transaction = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        if transaction_type == "balance":
            # balance += str(value)
            transaction_desc = f"Added to account"

        elif transaction_type == "withdraw":
            # balance -= str(value)
            transaction_desc = f"Withdraw from account"

        elif transaction_type == "sale":
            total_price = (value * 1.5) * quantity
            data["v_balance"] += total_price
            data["v_warehouse"].setdefault(product_name, {"v_price": value, "v_quantity": quantity})
            data["v_warehouse"][product_name]["v_quantity"] -= quantity
            transaction_desc = f"Sold '{quantity}' units of '{product_name}': unit price '{value}'"
            if data["v_warehouse"][product_name]["v_quantity"] == 0:
                print(f"Last {data['v_warehouse'][product_name]} sold, deleting from Warehouse.")
                del data["v_warehouse"][product_name]
            print(transaction_desc)
            value = total_price

        elif transaction_type == "purchase":
            total_price = value * quantity
            data["v_balance"] -= total_price
            data["v_warehouse"].setdefault(product_name, {"v_price": value, "v_quantity": 0})
            data["v_warehouse"][product_name]["v_quantity"] += quantity
            transaction_desc = f"Purchase '{quantity}' units of '{product_name}': unit price '{value}'"
            print(transaction_desc)
            value = total_price

        # print(f"DATA VALUE in DB: {data['v_balance']}")
        # for new_balance in db.session:
        #     #db.session.delete()
        #     db.session.add(data['v_balance'])
        #     db.session.commit()
        review.append(f"{date_transaction};{user};{transaction_desc};{value}")
        data["v_review"] = review

        print(f"ADD_TRANSACTION BEFORE SEND TO F_BALANCE: {balance}")
        Manager.save_data(self, data)
        return data # , balance


#    @log_transaction
    def f_balance(self, new_balance, *args, **kwargs):
        config_obj = Config()
        config_obj.create_files()
        manager = Manager(config_obj)
        data = Manager.load_data(self)
        balance = new_balance["balance"] #data.get("v_balance", 0)
        action = new_balance["action"]
        value = new_balance["value"]
        user = new_balance["user"]
        print(f"MANAGER - NEW BALANCE: {balance}")
        try:
            #v_action = int(input("Press '1' to Add or press '2' to Subtract: "))
            if action not in {1, 2}:
                print(f"Sorry {action} is not a valid option.\n")
            else:
                #v_value = float(input("Insert the amount to your balance: "))
                transaction_type = "balance" if action == 1 else "withdraw"
                print(f"F_BALANCE BEFORE SEND ADD_TRANSACTION: {balance}")
                print(f"F_BALANCE BEFORE SEND ADD_TRANSACTION: {value}")
                balance = float(balance)
                balance = balance + value
                data = self.add_transaction(user, data, transaction_type, value, balance)
                print(f"F_BALANCE AFTER SEND ADD_TRANSACTION: {balance}")

        except ValueError:
            print("Sorry, you did not input a valid value.\n")
        print(f"BALANCE in f_BALANCE BEFORE SEND TO APP: {balance}")
        return data #, balance


#    @log_transaction
#    @validate_quantity
    def f_sale(self, new_sale, *args, **kwargs):
        success = False
        config_obj = Config()
        config_obj.create_files()
        manager = Manager(config_obj)
        data = Manager.load_data(self)
        user = new_sale["user"]
        actual_balance = data.get("v_balance", 0)
        v_warehouse = data.get("v_warehouse", {})

        if not v_warehouse:
            print("\nYour warehouse is empty, and you cannot make any sales.")
            success = False
            return data

        try:
            s_name = str(new_sale["s_name"])
            if s_name not in v_warehouse:
                print(f"Sorry, {s_name} not available in the warehouse.\n")
                success = False
                return data

            v_quantity = int(new_sale["s_quantity"])
            if v_quantity > v_warehouse[s_name]["v_quantity"]:
                print(f"Sorry, you do not have enough {s_name} to sell.\n")
                success = False
                return data
            v_price = v_warehouse[s_name]["v_price"]
            total_price = v_price * v_quantity
            data = self.add_transaction(user, data, "sale", v_price, s_name, v_quantity)
            success = True
        except ValueError:
            print("Sorry, you did not input a valid value.\n")
        return data


#    @log_transaction
#    @validate_quantity
#    @validate_price
    def f_purchase(self, new_purchase, *args, **kwargs):
        config_obj = Config()
        config_obj.create_files()
        manager = Manager(config_obj)
        data = Manager.load_data(self)
        actual_balance = data.get("v_balance", 0)
        user = new_purchase["user"]
        #if actual_balance <= 0:
        #    print("\nYour account is empty, and you cannot make any purchases.")
        #    return data
        #
        #app.purchase()
        data = self.add_transaction(user, data, "purchase", new_purchase["v_price"], new_purchase["v_name"], new_purchase["v_quantity"])
        #except ValueError:
        #    print("Sorry, you did not input a valid value.\n")
        print(data)
        return data

    def f_account(self, data):
        actual_balance = data.get("v_balance", 0)

        if actual_balance <= 0:
            print("\nYour account is empty.\n")
        else:
            print(f"Your current balance is: {actual_balance}\n")

        return data

    def f_list(self, data):
        v_warehouse = data.get("v_warehouse", {})

        if not v_warehouse:
            print("\nWarehouse is empty.")
        else:
            print("\nThe list of products in the Warehouse is:")
            for v_name, details in v_warehouse.items():
                print(f"{v_name}: {details['v_quantity']} items - Price: {details['v_price']}")

        return data

    def f_warehouse(self, data):
        v_warehouse = data.get("v_warehouse", {})

        if not v_warehouse:
            print("\nWarehouse is empty.")
            return data

        s_name = input("Insert the name of the product: ")

        if s_name not in v_warehouse:
            print(f"Sorry, {s_name} not available in Warehouse.\n")
        else:
            print(f"\nThe {s_name} is available in Warehouse.")
            print(f"Have {v_warehouse[s_name]['v_quantity']} items in Warehouse.")
            print(f"And its price is {v_warehouse[s_name]['v_price']}\n")

        return data

    def f_review(self, history):
        new_history = {"date_transaction": [], "user": [], "transaction": [], "v_value": []}

        if history:
            for entry in history:
                parts = entry.split(';')
                date_transaction = parts[0]
                user = parts[1]
                transaction_description = parts[2]
                v_value = (parts[3])

                new_history["date_transaction"].append(date_transaction)
                new_history["user"].append(user)
                new_history["transaction"].append(transaction_description)
                new_history["v_value"].append(v_value)

        return new_history



        # if not v_review:
        #     print("\nReview file is empty.\n")
        # else:
        #
        #     for entry in history:
        #         date_transaction, transaction, v_value = entry.strip().split(";")
        #
        #         #print(f"========================= DATE: {idx}")
        #         print(f"========================= DATE: {date_transaction}")
        #         print(f"================== TRANSACTION: {transaction}")
        #         print(f"======================== VALUE: {v_value}")
        #
        #         #new_history.append(new_history)
        #         new_history["date_transaction"].append(str(date_transaction))
        #         new_history["transaction"].append(str(transaction))
        #         new_history["v_value"].append(str(v_value))
        # print(f"+++++++++++++++++++++++++HISTORY IN REVIEW: {new_history}")

        #return new_history


    def all(self):
        return self.load_data()

    def assign(self, option, data):
        """
        Assign tasks to the appropriate operations in the accounting system.

        Parameters:
        - task_type: A string representing the type of task to be assigned.
        - kwargs: Additional keyword arguments specific to the task type.

        Returns:
        - Updated data dictionary.
        """
        # Check if the task type is in the mapping dictionary
        if option == 1:
            data = self.f_balance(data)
            print(f"Your new balance is: {data['v_balance']}")
        elif option == 2:
            data = self.f_sale(data)
        elif option == 3:
            data = self.f_purchase(data)
        elif option == 4:
            data = self.f_account(data)
        elif option == 5:
            data = self.f_list(data)
        elif option == 6:
            data = self.f_warehouse(data)
        elif option == 7:
            data = self.f_review(data)