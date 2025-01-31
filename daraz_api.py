import os
import dotenv
import time
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from daraz_sdk.python import lazop
from colors import *

dotenv.load_dotenv()
# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()

app_key = os.getenv('OPEN_APP_KEY')
appSecret = os.getenv('OPEN_APP_SECRET')


def get_identical(common_sku):
    cursor.execute('SELECT identical_sku FROM identical WHERE sku = ?', (common_sku,))
    db_sku = cursor.fetchone()
    return db_sku[0].title() if db_sku else common_sku


def identical(common_sku):
    # Check if common sku is full sku
    if '-' in common_sku:
        product_tag, variation = [i.split('_')[0].strip() for i in common_sku.split('-', 1)]
        return f'{get_identical(product_tag)} - {get_identical(variation)}'
    return get_identical(common_sku)


class DarazAPI:
    def __init__(self, access_token, shop_name):
        self.client = lazop.LazopClient('https://api.daraz.com.bd/rest', app_key, appSecret)
        self.access_token = access_token
        self.shop_name = shop_name

    def get_products(self, offset=0):
        request = lazop.LazopRequest('/products/get', 'GET')
        request.add_api_param('limit', '35')
        request.add_api_param('filter', 'live')
        request.add_api_param('create_after', '2010-01-01T00:00:00+0800')
        request.add_api_param('offset', offset)
        response = self.client.execute(request, self.access_token)
        return response

    def item_ids(self):
        item_ids = []
        offset = 0
        while True:
            response = self.get_products(offset)
            if not response.body['data']:
                break
            for product in response.body['data']['products']:
                item_id = product['item_id']
                product_name = product['attributes']['name_en']
                item_ids.append(
                    {
                        'item_id': item_id,
                        'product_name': product_name
                    }
                )
            offset += 35
        return item_ids

    def review_ids(self):
        item_ids = self.item_ids()
        review_ids = []
        request = lazop.LazopRequest('/review/seller/history/list', 'GET')
        for item_id_dict in item_ids:
            item_id = item_id_dict['item_id']
            product_name = item_id_dict['product_name']
            request.add_api_param('item_id', item_id)
            current_time_utc_plus_8 = int(datetime.now(timezone(timedelta(hours=8))).timestamp() * 1000)
            time_range = 2 * 24 * 60 * 60 * 1000
            start_time = current_time_utc_plus_8 - time_range
            end_time = current_time_utc_plus_8
            request.add_api_param('start_time', start_time)
            request.add_api_param('end_time', end_time)
            request.add_api_param('current', '1')
            response = self.client.execute(request, self.access_token)
            if 'total' in response.body['data']:
                review_id_list = response.body['data']['id_list']
                review_ids.append(
                    {
                        'item_id': item_id,
                        'product_name': product_name,
                        'review_id': review_id_list
                    }
                )
        return review_ids

    def review(self):
        review_id_list = self.review_ids()
        if not review_id_list:
            print(YELLOW + self.shop_name + RESET, 'No reviews found')
        request = lazop.LazopRequest('/review/seller/list/v2', 'GET')
        for review_id_dict in review_id_list:
            product_name = review_id_dict['product_name']
            review_id = review_id_dict['review_id']
            request.add_api_param('id_list', f'{review_id}')
            response = self.client.execute(request, self.access_token)
            for review in response.body['data']['review_list']:
                can_reply = review['can_reply']
                create_time = review['create_time']
                create_date = time.strftime('%d %b %Y', time.localtime(create_time / 1000))
                review_id = review['id']
                product_rating = review['ratings']['product_rating']
                review_content = review.get('review_content', '')
                review_dict = {
                    'review_content': review_content,
                    'product_name': product_name,
                    'review_id': review_id,
                    'can_reply': can_reply,
                    'create_date': create_date,
                    'product_rating': product_rating,
                }

                print(YELLOW + self.shop_name + RESET, review_dict)

    def orders(self, status=None, created_after='2018-02-10T16:00:00+08:00', created_before=None,
               update_after=None, update_before=None):
        request = lazop.LazopRequest('/orders/get', 'GET')
        params = {
            'created_after': created_after,
            'created_before': created_before,
            'update_after': update_after,
            'update_before': update_before,
            'status': status
        }
        for key, value in params.items():
            if value:
                request.add_api_param(key, value)
        request.add_api_param('limt', '100')
        order_info = []
        order_ids = []

        # Set parameter
        offset = 0

        while True:  # Iterate until total order fetched
            request.add_api_param('offset', offset)
            response = self.client.execute(request, self.access_token)
            total_count = response.body['data']['countTotal']
            for order in response.body['data']['orders']:
                order_ids.append(order['order_id'])
                order_info.append(
                    {
                        'voucher_platform': order['voucher_platform'],
                        'voucher': order['voucher'],
                        'voucher_seller': order['voucher_seller'],
                        'voucher_code': order['voucher_code'],
                        'order_id': order['order_id'],
                        'order_number': order['order_number'],
                        'created_at': order['created_at'],
                        'updated_at': order['updated_at'],
                        'customer_name': (order['customer_first_name'] + ' ' + order['customer_last_name']).strip(),
                        'shipping_address': order['address_shipping'],
                        'billing_address': order['address_billing'],
                        'customer_phone': order['address_shipping']['phone'],
                        'shipping_fee': order['shipping_fee'],
                        'price': order['price'],
                        'shipping_fee_original': order['shipping_fee_original'],
                        'payment_method': order['payment_method'],
                        'shipping_fee_discount_seller': order['shipping_fee_discount_seller'],
                        'shipping_fee_discount_platform': order['shipping_fee_discount_platform'],
                        'items_count': order['items_count'],
                        'order_status': order['statuses'][0],
                        'extra_attributes': order['extra_attributes'],
                        'remarks': order['remarks'],
                        'total_price': float(order['price']) + float(order['shipping_fee']) -
                                       float(order['voucher']) - float(order['voucher_seller']),
                    }
                )
            # Break when all orders are fetched
            if total_count > offset:
                offset += 100
            else:
                break
        return order_ids, order_info

    def order(self, shop_name, status):
        order_ids, order_info = self.orders(status, created_after='2018-02-10T16:00:00+08:00')
        for order in order_info:
            order_id = order['order_id']
            print(order_id, end=' ')
            for order_details in self.order_item(order_id):
                sku = order_details['seller_sku']
                order_item_id = order_details['order_item_id']
                package_id = order_details['package_id']
                print(sku, end=' ')
                product_tag, variation = [i.split('_')[0].strip() for i in sku.split('-', 1)]
                identical_sku = f'{identical(product_tag)}-{identical(variation)}'
                cursor.execute('INSERT INTO open_order VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                               (shop_name, order_id, sku, identical_sku, status, True, order_item_id,
                                package_id))
            print()
        conn.commit()

    def order_item(self, order_id) -> list[dict[str, str]]:
        request = lazop.LazopRequest('/order/items/get', 'GET')
        request.add_api_param('order_id', order_id)
        response = self.client.execute(request, self.access_token)
        order_items = []  # Beside sku, other oder details are here
        for order_item in response.body['data']:
            order_items.append(
                {
                    'seller_sku': order_item['sku'],
                    'buyer_id': order_item['buyer_id'],
                    'order_item_id': order_item['order_item_id'],
                    'package_id': order_item['package_id'],
                    'product_name': order_item['name'],
                    'paid_price': order_item['paid_price'],
                    'item_price': order_item['item_price'],
                    'mail_address': order_item['digital_delivery_info'],
                    'tracking_code': order_item['tracking_code'],
                    'shop_sku': order_item['shop_sku'],
                    'sla_time_stamp': order_item['sla_time_stamp'],
                }
            )
        return order_items

    def package_id(self, status):
        package_ids = []
        request = lazop.LazopRequest('/order/items/get', 'GET')
        order_ids, _ = self.orders(status)
        for order_id in order_ids:
            request.add_api_param('order_id', order_id)
            response = self.client.execute(request, self.access_token)
            for order_item in response.body['data']:
                package_id = order_item['package_id']
                package_ids.append(package_id)
        return package_ids

    def seller_metrics(self):
        request = lazop.LazopRequest('/seller/metrics/get', 'GET')
        response = self.client.execute(request, self.access_token)
        print(YELLOW + self.shop_name + RESET, response.body)
        return response.body

    def print_awb(self, package_ids: list[str]):
        request = lazop.LazopRequest('/order/package/document/get')
        document_req = {
            'doc_type': 'PDF',
            'packages': [],
            'print_item_list': 'true'
        }
        for package_id in package_ids:
            document_req['packages'].append({
                'package_id': package_id
            })
        request.add_api_param('getDocumentReq', json.dumps(document_req))
        while True:
            try:
                response = self.client.execute(request, self.access_token)
                break
            except Exception as e:
                print(e)
        pdf_url = response.body['result']['data']['pdf_url']
        print(pdf_url)
        # Download PDF
        import requests
        response = requests.get(pdf_url)
        return response.content

    def pack(self):
        request = lazop.LazopRequest('/order/fulfill/pack')
        cursor.execute('SELECT order_id, GROUP_CONCAT(order_item_id) AS items FROM open_order \
                        WHERE proceed = TRUE AND status = ? AND shop_name = ? GROUP BY order_id',
                       ('topack', self.shop_name,))
        for order_id, items in cursor.fetchall():
            pack_req = {
                "pack_order_list": [{
                    "order_item_list": [],
                    "order_id": order_id
                }],
                "delivery_type": "dropship",
                "shipment_provider_code": "FM50",
                "shipping_allocate_type": "TFS"
            }
            for item in items.split(','):
                pack_req['pack_order_list'][0]['order_item_list'].append(item)
            request.add_api_param('packReq', json.dumps(pack_req))
            response = self.client.execute(request, self.access_token)
            for topack_response in response.body['result']['data']['pack_order_list']:
                order_item_id = topack_response['order_item_list'][0]['order_item_id']
                msg = topack_response['order_item_list'][0]['msg']
                if msg == 'success':
                    print(GREEN + 'Pack success', str(order_item_id) + RESET)
                else:
                    print(RED + 'Pack failed', response.body + RESET)

    def rts(self, package_ids: list):
        request = lazop.LazopRequest('/order/package/rts')
        for start in range(0, len(package_ids), 20):
            ready_to_ship_req = {
                "packages": []
            }
            for package_id in package_ids[start:start + 20]:
                ready_to_ship_req['packages'].append({
                    'package_id': package_id
                })
            request.add_api_param('readyToShipReq', json.dumps(ready_to_ship_req))
            response = self.client.execute(request, self.access_token)
            for rts_response in response.body['result']['data']['packages']:
                msg = rts_response['msg']
                if msg == 'success':
                    print(GREEN + 'RTS success', rts_response['package_id'] + RESET)
                else:
                    print(RED + 'RTS failed', response.body + RESET)
            print(response.body)

    def create_product(self, payload):
        request = lazop.LazopRequest('/product/create')
        request.add_api_param('payload', payload)
        response = self.client.execute(request, self.access_token)
        return response.body

    def find_product(self, seller_sku_list: list[str]):
        request = lazop.LazopRequest('/products/get')
        request.add_api_param('sku_seller_list', seller_sku_list)
        request.add_api_param('filter', 'live')
        response = self.client.execute(request, self.access_token)
        return response.body

    def upload_image(self, image):
        request = lazop.LazopRequest('/image/upload')
        request.add_file_param('image', image)
        response = self.client.execute(request, self.access_token)
        return response.body

    def category_attributes(self, category_id):
        request = lazop.LazopRequest('/category/attributes/get', 'GET')
        request.add_api_param('primary_category_id', category_id)
        request.add_api_param('language_code', 'en_US')
        response = self.client.execute(request)
        return response.body

    def reverse_order(self):
        request = lazop.LazopRequest('/reverse/getreverseordersforseller')
        request.add_api_param('page_size', '10')
        request.add_api_param('page_no', '1')
        request.add_api_param('return_to_type', 'RTW')
        response = self.client.execute(request, self.access_token)
        for order in response.body['result']['items']:
            reverse_order_id = order['reverse_order_id']
            self.reverse_order_detail(reverse_order_id)

    def reverse_order_detail(self, reverse_order_id):
        request = lazop.LazopRequest('/order/reverse/return/detail/list', 'GET')
        request.add_api_param('reverse_order_id', reverse_order_id)
        response = self.client.execute(request, self.access_token)
        trade_order_gmt_create = response.body['data']['reverseOrderLineDTOList'][0]['trade_order_gmt_create']
        trade_order_date = time.strftime('%d %b %Y', time.localtime(trade_order_gmt_create))
        return_order_line_gmt_create = response.body['data']['reverseOrderLineDTOList'][0][
            'return_order_line_gmt_create']
        # Check if trade_order_date is between 45 and 60 days from now
        if (datetime.now() - timedelta(days=60)).date() <= datetime.strptime(trade_order_date,
                                                                             '%d %b %Y').date() <= (
                datetime.now() - timedelta(days=0)).date():
            trade_order_id = response.body['data']['trade_order_id']
            ofc_status = response.body['data']['reverseOrderLineDTOList'][0]['ofc_status']
            user_id = response.body['data']['reverseOrderLineDTOList'][0]['buyer']['user_id']
            print(self.shop_name, trade_order_date, trade_order_id, ofc_status, user_id,
                  return_order_line_gmt_create)

    def payout_status(self):
        request = lazop.LazopRequest('/finance/payout/status/get', 'GET')
        request.add_api_param('created_after', '2024-10-12')
        response = self.client.execute(request, self.access_token)
        total = 0
        for statement in response.body['data']:
            payout = statement['payout']
            paid_status = statement['paid']
            created_at = statement['created_at']
            total += float(payout.split('BDT')[0].strip())
            print(created_at, payout, paid_status)
        print(CYAN, 'Total:', total, RESET)

    def get_order(self, order_id):
        request = lazop.LazopRequest('/order/get', 'GET')
        request.add_api_param('order_id', order_id)
        response = self.client.execute(request, self.access_token)
        return response.body

    def generate_access_token(self, code):
        request = lazop.LazopRequest('/auth/token/create', 'GET')
        request.add_api_param('code', code)
        response = self.client.execute(request)
        print(response.body)
        return response.body

    def open_session(self, order_id) -> str:
        request = lazop.LazopRequest('/im/session/open', 'GET')
        request.add_api_param('order_id', order_id)
        response = self.client.execute(request, self.access_token)
        return response.body['session_id']

    def send_text_message(self, session_id: str, message):
        request = lazop.LazopRequest('/im/message/send', 'POST')
        request.add_api_param("session_id", session_id)
        request.add_api_param("template_id", "1")
        request.add_api_param("txt", message)
        response = self.client.execute(request, self.access_token)
        return response.body


    def send_order_message(self, session_id: str, order_id: str):
        request = lazop.LazopRequest('/im/message/send', 'POST')
        request.add_api_param("session_id", session_id)
        request.add_api_param("template_id", "10007")
        request.add_api_param("order_id", order_id)
        response = self.client.execute(request, self.access_token)
        return response.body


    def invite_to_follow_store(self, session_id: str):
        request = lazop.LazopRequest('/im/message/send', 'POST')
        request.add_api_param("session_id", session_id)
        request.add_api_param("template_id", "10010")
        response = self.client.execute(request, self.access_token)
        return response.body

    def transaction_details(self, order_id):
        request = lazop.LazopRequest('/finance/transaction/details/get', 'GET')
        request.add_api_param('trade_order_id', order_id)
        response = self.client.execute(request, self.access_token)
        return response.body
