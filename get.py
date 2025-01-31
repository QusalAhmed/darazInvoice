import sqlite3
import winsound
from multiprocessing import Process
from datetime import datetime, timedelta

# import from local
from daraz_api import DarazAPI, identical
from colors import *

# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()


# Get all orders from Daraz between time range
def get_order_status(daraz_api: DarazAPI):
    created_after = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    created_before = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    _, order_info = daraz_api.orders(created_after=created_after, created_before=created_before, status='all')
    for order in order_info:
        if order['order_status'] != 'canceled' and order['order_status'] != 'delivered':
            time_elapsed = datetime.now() - datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S +0800')
            print(f'{order["order_id"]}: {order["order_status"]} {order["created_at"]} {time_elapsed.days} days')


def get_hub_parcels(daraz_api: DarazAPI):
    updated_after = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    _, order_info = daraz_api.orders(update_after=updated_after, status='all')
    for order in order_info:
        if order['order_status'] == 'shipped_back':
            created_at = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S %z')
            time_elapsed = datetime.now(created_at.tzinfo) - created_at
            updated_at = datetime.strptime(order['updated_at'], '%Y-%m-%d %H:%M:%S %z')
            update_time_elapsed = datetime.now(updated_at.tzinfo) - updated_at
            print(f'{order["order_id"]}:{CYAN}', f'Updated before {update_time_elapsed} {BLUE}'
                  f'Created before {time_elapsed.days} days', RESET)


delivered_parcel = 0
total_parcel = 0


def count_order(daraz_api: DarazAPI):
    global delivered_parcel, total_parcel
    created_after = (datetime.now() - timedelta(days=37)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    created_before = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    _, order_info = daraz_api.orders(created_after=created_after, created_before=created_before, status='all')
    for order in order_info:
        if order['order_status'] != 'canceled':
            if order['order_status'] == 'delivered':
                delivered_parcel += 1
            total_parcel += 1


def calculate_profit():
    # Clear table
    cursor.execute('DELETE FROM parcel where TRUE')
    conn.commit()

    created_after = (datetime.now() - timedelta(days=37)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    created_before = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    # Iterate through all the shops
    for row in cursor.execute('SELECT shop_name, access_token FROM open_daraz').fetchall():
        shop_name, access_token = row
        daraz_api = DarazAPI(access_token, shop_name)
        print(YELLOW + f"For {shop_name}" + RESET)
        _, order_info = daraz_api.orders(created_after=created_after, created_before=created_before, status='all')
        for order in order_info:
            order_status = order['order_status']
            if order_status != 'canceled':
                order_id = order['order_id']
                for order_item_info in daraz_api.order_item(order_id):
                    seller_sku = identical(order_item_info['seller_sku'])
                    product_name = order_item_info['product_name']
                    cursor.execute('SELECT cost FROM buying_price WHERE seller_sku = ?',(seller_sku,))
                    try:
                        buy_price, paid_price = cursor.fetchone()
                        print(f'{product_name} ({seller_sku}) Buy price: {buy_price} Paid price: {paid_price}')
                    except TypeError:
                        winsound.Beep(2000, 500)
                        buy_price, paid_price = map(float, input(f'{product_name} ({seller_sku}) Buy price, Paid price: ').split())
                    cursor.execute('INSERT INTO parcel VALUES (?, ?, ?, ?, ?, ?)',
                                   (order_id, product_name, seller_sku, buy_price, paid_price, order_status))
                    conn.commit()

    # Calculate profit
    profit = 0
    cost = 0
    cursor.execute('SELECT order_id, seller_sku, buy_price, status FROM parcel')
    for row in cursor.fetchall():
        order_id, seller_sku, buy_price, status = row
        print(order_id, seller_sku, buy_price, status)

    print(f"Profit: {profit:.2f} BDT Cost: {cost:.2f} BDT")

def get_current_order():
    # Clear table
    cursor.execute('DELETE FROM open_order where TRUE')
    conn.commit()

    for row in cursor.execute('SELECT shop_name, access_token FROM open_daraz').fetchall():
        shop_name, access_token = row
        daraz_api = DarazAPI(access_token, shop_name)
        print(YELLOW + f"For {shop_name}" + RESET)
        # Process(target=daraz_api.review, args=()).start()
        daraz_api.order(shop_name, status='toship')  # to arrange shipment & ready to ship
        daraz_api.order(shop_name, status='topack')
    # Group identical products and get the total quantity
    print(YELLOW + "Order items" + RESET)
    cursor.execute('SELECT identical_sku, COUNT(identical_sku) FROM open_order Group By identical_sku')
    for sku, count in cursor.fetchall():
        print(sku, count)


def generate_access_token():
    for code in cursor.execute('SELECT code FROM open_daraz LIMIT -1 OFFSET 0').fetchall():
        daraz_api = DarazAPI('', '')
        response = daraz_api.generate_access_token(code[0])
        expires_in = response['expires_in']
        access_token = response['access_token']
        refresh_token = response['refresh_token']
        refresh_expires_in = response['refresh_expires_in']
        cursor.execute(
            'UPDATE open_daraz SET access_token = ?, expires_in = ?, refresh_token = ?, refresh_expires_in = ? WHERE code = ?',
            (access_token, expires_in, refresh_token, refresh_expires_in, code[0]))
        conn.commit()


def main():
    # get_current_order()
    # calculate_profit()
    for row in cursor.execute('SELECT shop_name, access_token FROM open_daraz').fetchall():
        shop_name, access_token = row
        daraz_api = DarazAPI(access_token, shop_name)
        print(YELLOW + f"For {shop_name}" + RESET)
        # daraz_api.payout_status()
        # daraz_api.reverse_order()
    #     get_order_status(daraz_api)
    #     get_hub_parcels(daraz_api)
        daraz_api.seller_metrics()

    #     count_order(daraz_api)
    # print(BLUE + f"Delivered: {delivered_parcel} Total: {total_parcel} {delivered_parcel / total_parcel * 100:.2f}%" +
    #       RESET)


if __name__ == "__main__":
    main()
    # generate_access_token()
