import os
import dotenv
import ngrok
import time
import sqlite3
import threading
import winsound
from flask import Flask, request, jsonify
from colors import *
from daraz_api import DarazAPI

dotenv.load_dotenv()


def beep():
    winsound.Beep(1000, 900)

def respond_customer():
    # connect to database
    conn = sqlite3.connect('order_details.db')
    cursor = conn.cursor()
    print(YELLOW + "Responding to customer" + RESET)
    while True:
        for row in cursor.execute('SELECT * FROM unpaid_order').fetchall():
            trade_order_id, status_update_time, order_status, shop_name = row
            if time.time() - status_update_time > 60:
                cursor.execute('SELECT access_token FROM open_daraz WHERE shop_name = ?', (shop_name,))
                access_token = cursor.fetchone()[0]
                daraz_api = DarazAPI(access_token, shop_name)
                session_id = daraz_api.open_session(trade_order_id)
                daraz_api.send_order_message(session_id, trade_order_id)
                daraz_api.send_text_message(session_id, os.getenv("UNPAID_MESSAGE"))
                daraz_api.invite_to_follow_store(session_id)
                cursor.execute('DELETE FROM unpaid_order WHERE order_id = ?', (trade_order_id,))
                conn.commit()
                print(YELLOW + f"Responded to {trade_order_id} {shop_name}" + RESET)
                beep()
        time.sleep(60)


def data_handler(response: dict):
    # connect to database
    conn = sqlite3.connect('order_details.db')
    cursor = conn.cursor()
    seller_id = response['seller_id']
    message_type = response['message_type']
    data = response['data']
    # Get shop_name from the database
    cursor.execute('SELECT shop_name, access_token FROM open_daraz WHERE seller_id = ?', (seller_id,))
    fetched_data = cursor.fetchone()
    if fetched_data:
        shop_name, access_token = fetched_data
    else:
        print(RED + "Seller ID not found" + RESET)
        return
    print(YELLOW + f"Received data from {shop_name}" + RESET)
    if message_type == 1:
        threading.Thread(target=beep).start()
        trade_order_id = data['trade_order_id']
        buyer_id = data['buyer_id']
        # fulfillment_package_id = data['fulfillment_package_id']
        status = data['status']
        status_update_time = data['status_update_time']

        print('Trade Order ID:', trade_order_id, 'Buyer ID:', buyer_id, 'Status:', status,
              'Status Update Time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status_update_time)))

    elif message_type == 2:
        from_account_type = data['from_account_type']
        if from_account_type == 2:
            return
        threading.Thread(target=beep).start()
        session_id = data['session_id']
        message_id = data['message_id']
        send_type = data['type']
        content = data['content']
        send_time = data['send_time']
        to_account_id = data['to_account_id']
        to_account_type = data['to_account_type']
        template_id = data['template_id']
        from_user_id = data['from_user_id']
        status = data['status']

        print(f"From Account Type: {from_account_type}, Content: {content}, Session ID: {session_id},"
              f"Message ID: {message_id}, Type: {send_type}, Send Time: {send_time}, To Account ID: {to_account_id}"
              f"To Account Type: {to_account_type}, Template ID: {template_id}, From User ID: {from_user_id},"
              f"Status: {status}")

    elif message_type == 3:
        print("Message Type 3")
        print(data)

    elif message_type == 4:
        threading.Thread(target=beep).start()
        order_status = data['order_status']
        trade_order_id = data['trade_order_id']
        # trade_order_line_id = data['trade_order_line_id']
        status_update_time = data['status_update_time']
        buyer_id = data['buyer_id']
        print(f"Order Status: {order_status}, Trade Order ID: {trade_order_id}, Buyer ID: {buyer_id}")
        # daraz_api = DarazAPI(access_token, shop_name)
        # for customer_order in daraz_api.get_order(trade_order_id):
        #     seller_sku = customer_order['sku']
        # Respond to unpaid order
        if order_status == 'unpaid':
            cursor.execute('INSERT INTO unpaid_order VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING',
                            (trade_order_id, status_update_time, order_status, shop_name))
            conn.commit()
        elif order_status in ['pending', 'canceled']:
            message_type_dict = {'pending': 'PENDING_MESSAGE', 'canceled': 'CANCELED_MESSAGE'}
            daraz_api = DarazAPI(access_token, shop_name)
            session_id = daraz_api.open_session(trade_order_id)
            daraz_api.send_order_message(session_id, trade_order_id)
            daraz_api.send_text_message(session_id, os.getenv(message_type_dict[order_status]))
            daraz_api.invite_to_follow_store(trade_order_id)
            cursor.execute('DELETE FROM unpaid_order WHERE order_id = ?', (trade_order_id,))
            conn.commit()

    else:
        print(RED, "Invalid message send_type", RESET)


# Initialize Flask app
app = Flask(__name__)


# Route to handle POST request
@app.route("/webhook", methods=['POST'])
def webhook():
    response = request.json
    threading.Thread(target=data_handler, args=(response,)).start()

    # Respond to the POST request
    return jsonify({"status": "success", "data_received": response}), 200


if __name__ == '__main__':
    threading.Thread(target=respond_customer).start()
    ngrok_token = os.getenv("NGROK_AUTH_TOKEN")
    # Step 1: Start a ngrok tunnel programmatically
    ngrok.set_auth_token(ngrok_token)  # Optional, if you need authentication
    public_url = ngrok.connect(5000, hostname="tapir-willing-ultimately.ngrok-free.app")  # This exposes port 5000
    print(f"ngrok tunnel available at: {public_url.url()}")

    # Step 2: Start the Flask app
    app.run(port=5000)
