import sqlite3
from datetime import datetime, timedelta

# import from local
from daraz_api import DarazAPI
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
        if order['order_status'] != 'canceled':
            time_elapsed = datetime.now() - datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S +0800')
            print(f'{order["order_id"]}: {order["order_status"]} {order["created_at"]} {time_elapsed.days} days')


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


def get_current_order():
    # Clear table
    cursor.execute('DELETE FROM open_order where TRUE')
    conn.commit()

    for row in cursor.execute('SELECT shop_name, access_token FROM open_daraz').fetchall():
        shop_name, access_token = row
        daraz_api = DarazAPI(access_token, shop_name)
        print(YELLOW + f"For {shop_name}" + RESET)
        daraz_api.review()
        daraz_api.order(shop_name, status='toship')  # to arrange shipment & ready to ship
        daraz_api.order(shop_name, status='topack')
    # Group identical products and get the total quantity
    print(YELLOW + "Order items" + RESET)
    cursor.execute('SELECT identical_sku, COUNT(identical_sku) FROM open_order Group By identical_sku')
    for sku, count in cursor.fetchall():
        print(sku, count)


def main():
    get_current_order()
    # for row in cursor.execute('SELECT shop_name, access_token FROM open_daraz').fetchall():
    #     shop_name, access_token = row
    #     daraz_api = DarazAPI(access_token, shop_name)
    #     print(YELLOW + f"For {shop_name}" + RESET)
    #     daraz_api.payout_status()
    #     daraz_api.reverse_order()
        # get_order_status(daraz_api)

    #     count_order(daraz_api)
    # print(BLUE + f"Delivered: {delivered_parcel} Total: {total_parcel} {delivered_parcel / total_parcel * 100:.2f}%" +
    #       RESET)


if __name__ == "__main__":
    main()
