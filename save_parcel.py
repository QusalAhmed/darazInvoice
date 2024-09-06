import psycopg2
import time

conn = psycopg2.connect(
    host="ep-empty-block-a56m3gjb.us-east-2.aws.neon.tech",
    database="dinfo",
    user="dinfo_owner",
    password="1kxmVcS0dXZP"
)
cursor = conn.cursor()


class SaveParcel:
    def __init__(self, order_number, tracking, shop_name, seller_sku, lazada_sku):
        self.order_number = order_number
        self.tracking = tracking
        self.shop_name = shop_name
        self.product_name = seller_sku
        self.lazada_sku = lazada_sku

    def save(self):
        cursor.execute(
            "INSERT INTO daraz_parcel (order_number, trackingcode, shop_name, sellerSKU, lazadaSku) \
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (order_number) DO UPDATE SET date = %s",
            (self.order_number, self.tracking, self.shop_name, self.product_name, self.lazada_sku,
             time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return True
