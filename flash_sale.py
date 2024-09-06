import pandas as pd
import sqlite3
import math
import re


def is_multi():
    return 'multi' in variation or variation == 'f' or variation == 'fs'


def identical(common_sku):
    cursor.execute('SELECT identical_sku FROM identical WHERE sku = ?', (common_sku,))
    db_sku = cursor.fetchone()
    return db_sku[0] if db_sku else common_sku


# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM campaign_data where TRUE')

# Variable
CLEAR = 2
min_stock = 20
delivery_cost = 0

# Read the .xls file
df = pd.read_excel('D:/Downloads/fs.xlsx', header=0, skiprows=[1])

for index, row in df.iterrows():
    serial = index.__hash__() + 2
    price = math.floor(float(''.join(re.findall(r'\d+\.?\d*', row['Recommended Price']))))
    seller_sku = row['Seller SKU'].lower()
    product_tag, variation = [i.strip() for i in seller_sku.split('-', 1)]
    # Load the .xls file to database
    identical_product_tag = identical(product_tag)
    if is_multi():
        identical_sku = 'Multi ' + identical_product_tag
    else:
        identical_sku = identical_product_tag
    cursor.execute('INSERT INTO campaign_data VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (serial, product_tag.title(), variation.title(), price, 0, False, identical_sku))
    cursor.execute('SELECT price, max_price FROM pricing WHERE product_tag = ?',
                   (identical_product_tag + '-' + identical(variation),))
    try:
        min_price, max_price = cursor.fetchone()
    except TypeError:
        cursor.execute('SELECT price, max_price FROM pricing WHERE product_tag = ?',
                       (identical_product_tag,))
        try:
            min_price, max_price = cursor.fetchone()
        except TypeError:
            print('No pricing found for', product_tag)
            continue
    if max_price is None:
        max_price = min_price
    if price < min_price * (1 - CLEAR / 100):
        df.drop(index, inplace=True)
        print(f'{serial}. {row['Seller SKU']} is dropped Price: {price}({min_price})')
        continue
    elif is_multi() and price < min_price + delivery_cost:
        df.drop(index, inplace=True)
        print(f'{serial}. {row['Seller SKU']} is dropped Price: {price}({min_price + delivery_cost})')
        continue
    # Set price
    if is_multi():
        df.loc[index, 'Campaign Price（Mandatory）'] = price
        cursor.execute('UPDATE campaign_data SET campaign_price = ? WHERE serial = ?',
                       (price, serial,))
    else:
        df.loc[index, 'Campaign Price（Mandatory）'] = min(max_price, price)
        cursor.execute('UPDATE campaign_data SET campaign_price = ? WHERE serial = ?',
                       (min(max_price, price), serial,))
    # Set stock
    if 'Campaign stock' in df.columns:
        stock = int(row['Stock'])
        if stock >= min_stock:
            df.loc[index, 'Campaign stock'] = min_stock
        else:
            df.loc[index, 'Campaign stock'] = stock
            print('Low Stock at', stock, 'of', seller_sku)

    # Update status of eligible products
    cursor.execute('UPDATE campaign_data SET status = TRUE WHERE serial = ?', (serial,))
conn.commit()

# Eliminated product check
cursor.execute('SELECT DISTINCT product_tag FROM campaign_data WHERE status = FALSE')
for product_tag in cursor.fetchall():
    cursor.execute('SELECT * FROM campaign_data WHERE (product_tag, status) = (?, ?)',
                   (product_tag[0], True))
    if not cursor.fetchall():
        cursor.execute('SELECT recommended_price, variation FROM campaign_data WHERE product_tag = ?',
                       (product_tag[0],))
        print(product_tag, 'Permanently removed at', cursor.fetchall())

print(f' Total row: {df.shape[0]} '.center(40, '━'))
file_path = 'D:/Downloads/fs out.xlsx'
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    worksheet = writer.sheets['Sheet1']

    # Set the column width
    worksheet.column_dimensions['A'].width = 40
    worksheet.column_dimensions['G'].width = 20

# Show campaign price
cursor.execute('SELECT DISTINCT identical_sku FROM campaign_data WHERE campaign_price != 0')
for sku in cursor.fetchall():
    cursor.execute('SELECT campaign_price FROM campaign_data WHERE identical_sku = ? '
                   'AND campaign_price != 0 ORDER BY campaign_price', (sku[0],))
    price_list = cursor.fetchall()
    print(f'{sku[0].title()} ({price_list[0][0]} - {price_list[-1][0]}): {price_list}')
