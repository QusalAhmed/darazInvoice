import psycopg2
import time


class Parcel:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="ep-empty-block-a56m3gjb.us-east-2.aws.neon.tech",
            database="dinfo",
            user="dinfo_owner",
            password="1kxmVcS0dXZP"
        )
        self.cursor = self.conn.cursor()

    def save(self, order_number, tracking, shop_name, seller_sku, lazada_sku):
        try:
            self.cursor.execute(
                "INSERT INTO daraz_parcel (order_number, trackingcode, shop_name, sellerSKU, lazadaSku) \
                VALUES (%s, %s, %s, %s, %s) \
                ON CONFLICT (order_number) DO UPDATE SET \
                date = %s, trackingcode = EXCLUDED.trackingcode, shop_name = EXCLUDED.shop_name, \
                sellerSKU = EXCLUDED.sellerSKU, lazadaSku = EXCLUDED.lazadaSku",
                (order_number, tracking, shop_name, seller_sku, lazada_sku, time.strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def late_save(self, order_number, created_at, tracking='', shop_name='', seller_sku='', lazada_sku=''):
        try:
            self.cursor.execute(
                "INSERT INTO daraz_parcel (order_number, trackingcode, shop_name, sellerSKU, lazadaSku, date) \
                VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (order_number) DO NOTHING",
                (order_number, tracking, shop_name, seller_sku, lazada_sku, created_at))
            self.conn.commit()
        except Exception as e:
            print(e)

    def get_order_id(self, shop_name):
        self.cursor.execute("SELECT order_number FROM daraz_parcel WHERE shop_name ~* %s AND status != 'Delivered'",
                            (r'\s*'.join(shop_name),))
        return self.cursor.fetchall()

    def update_status(self, order_number, status):
        self.cursor.execute("UPDATE daraz_parcel SET status = %s WHERE order_number = %s",
                            (status, order_number))
        # Check if any row updated
        if self.cursor.rowcount:
            self.conn.commit()
            return True
        return False

    def update_status_by_tracking(self, tracking_code, status):
        self.cursor.execute("UPDATE daraz_parcel SET status = %s WHERE trackingcode = %s",
                            (status, tracking_code))
        # Check if any row updated
        if self.cursor.rowcount:
            self.conn.commit()
            return True
        return False

    def failed_parcel(self, order_number, tracking_code, date, shop_name):
        self.cursor.execute(
            'INSERT INTO failed_parcel (order_number, tracking, date_time, shop_name) VALUES (%s, %s, %s, %s) \
            ON CONFLICT (order_number) DO UPDATE SET tracking = EXCLUDED.tracking, date_time = EXCLUDED.date_time, \
            shop_name = EXCLUDED.shop_name',
            (order_number, tracking_code, date, shop_name))
        self.conn.commit()

    def delivered_parcel(self):
        self.cursor.execute("SELECT shop_name, order_number, sellersku FROM daraz_parcel WHERE status = 'Delivered'")
        for index, (shop_name, order_number, seller_sku) in enumerate(self.cursor.fetchall(), 1):
            print(f"{index}. {shop_name} {order_number} {seller_sku}")

    def update_failed_parcel(self, tracking_code):
        self.cursor.execute("UPDATE failed_parcel SET status = TRUE WHERE tracking = %s",
                            (str(tracking_code),))
        # Check if any row updated
        if self.cursor.rowcount:
            self.conn.commit()
            return True
        return False

    # Email notified parcel needs to be collected from hub
    def get_hub_parcel(self):
        self.cursor.execute('SELECT order_number, tracking, shop_name, date_time FROM failed_parcel WHERE status = FALSE')
        return self.cursor.fetchall()

    def get_failed_parcel_hub(self):
        self.cursor.execute(
            'SELECT order_number, tracking, date_time, shop_name FROM failed_parcel WHERE status = FALSE')
        return self.cursor.fetchall()

    def get_order_number_by_tracking(self, tracking_code):
        self.cursor.execute("SELECT order_number FROM daraz_parcel WHERE trackingcode = %s", (tracking_code,))
        return self.cursor.fetchone()[0]

    def undelivered_parcel(self):
        self.cursor.execute("SELECT * FROM daraz_parcel WHERE \
                            status != 'Delivered' AND status != 'Package Returned' \
                            AND date < NOW() - INTERVAL '45 days' \
                            AND date > NOW() - INTERVAL '60 days' \
                            ORDER BY shop_name")
        for index, *data in enumerate(self.cursor.fetchall(), 1):
            print(f"{index}. {data}")


if __name__ == '__main__':
    online_parcel = Parcel()
    # online_parcel.delivered_parcel()
    # online_parcel.get_hub_parcel()
    online_parcel.undelivered_parcel()
