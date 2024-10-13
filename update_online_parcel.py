import os
import dotenv
import sqlite3

from daraz_sdk.python import lazop

dotenv.load_dotenv()

app_key = os.getenv('OPEN_APP_KEY')
appSecret = os.getenv('OPEN_APP_SECRET')

# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()

for shop_name in cursor.execute('SELECT shop_name FROM open_daraz').fetchall():
    cursor.execute('SELECT access_token FROM open_daraz WHERE shop_name = ?', (shop_name[0],))
    access_token = cursor.fetchall()[0][0]

    client = lazop.LazopClient('https://api.daraz.com.bd/rest', app_key, appSecret)

    # create an api request set GET method
    # default http method is POST
    request = lazop.LazopRequest('/order/get')

    # Fetch order from NEON database
    from online_parcel import Parcel
    for order_number in Parcel().get_order_id(shop_name):
        request.add_api_param('order_id', order_number[0])

        # response = client.execute(request)
        response = client.execute(request,access_token)
        print(order_number[0], end=': ')
        try:
            delivery_status = response.body['data']['statuses'][0]
            if delivery_status == 'shipped_back_success':
                print("\033[31m" + delivery_status + "\033[0m")
            else:
                print(delivery_status)
                Parcel().update_status(order_number[0], delivery_status)
        except KeyError:
            print("\033[31m" + 'No delivery status found ' + shop_name[0] + "\033[0m")
