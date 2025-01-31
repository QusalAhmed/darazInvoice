import os
import json
import dotenv
import requests
import sqlite3

# Load environment variables from .env file
dotenv.load_dotenv()

# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()


class Order:
    # Placeholder class for demonstration
    # Replace with actual ORM or database query methods
    def __init__(self, invoice_id, address, due_amount, note):
        self.invoice_id = invoice_id
        self.address = address
        self.due_amount = due_amount
        self.note = note


class Address:
    # Placeholder class for demonstration
    def __init__(self, name, address, phone):
        self.name = name
        self.address = address
        self.phone = phone


class Steadfast:
    def __init__(self):
        self.base_url = 'https://portal.packzy.com/api/v1'
        self.api_key = os.getenv('STEADFAST_API_KEY')
        self.secret_key = os.getenv('STEADFAST_SECRET_KEY')

    def create_order(self, data):
        headers = {
            'Api-Key': self.api_key,
            'Secret-Key': self.secret_key,
            'Content-Type': 'application/json',
        }
        response = requests.post(
            f"{self.base_url}/create_order",
            headers=headers,
            json=data
        )
        return response.json()

    def bulk_create(self, data):
        headers = {
            'Api-Key': self.api_key,
            'Secret-Key': self.secret_key,
            'Content-Type': 'application/json',
        }
        response = requests.post(
            f"{self.base_url}/create_order/bulk-order",
            headers=headers,
            data=json.dumps(data)
        )
        return response.json()

    def get_balance(self):
        headers = {
            'Api-Key': self.api_key,
            'Secret-Key': self.secret_key,
            'Content-Type': 'application/json',
        }
        response = requests.get(
            f"{self.base_url}/get_balance",
            headers=headers,
        )
        return response.json()


def bulk_create():
    # Simulated function to retrieve orders; replace with actual query logic
    orders = []
    cursor.execute('SELECT order_id, customer_name, address, phone_number, cod_amount, note, skus \
                    FROM outside_delivery WHERE proceed = 1')
    for row in cursor.fetchall():
        order_id, customer_name, address, phone_number, cod_amount, note, skus = row
        orders.append(Order(order_id, Address(customer_name, address, phone_number), cod_amount, f'{note}|{skus}'))

    data = []

    for order in orders:
        item = {
            'invoice': order.invoice_id,
            'recipient_name': order.address.name if order.address else 'N/A',
            'recipient_address': order.address.address,
            'recipient_phone': order.address.phone,
            'cod_amount': order.due_amount,
            'note': order.note,
        }
        data.append(item)

    steadfast = Steadfast()
    result = steadfast.bulk_create(data)
    print(result)
    return result


def create_order():
    order = Order('668084365860265', Address("Qusal", "123 Elm Street", "01771056096"),
                  100, "Urgent delivery")
    data = {
        'invoice': order.invoice_id,
        'recipient_name': order.address.name if order.address else 'N/A',
        'recipient_address': order.address.address,
        'recipient_phone': order.address.phone,
        'cod_amount': order.due_amount,
        'note': order.note,
    }

    steadfast = Steadfast()
    result = steadfast.create_order(data)
    print(result)
    return result


def get_balance():
    steadfast = Steadfast()
    balance = steadfast.get_balance()
    print(balance)


# Example usage
if __name__ == "__main__":
    # create_order()
    # bulk_create()
    get_balance()
