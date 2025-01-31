# import pandas as pd
# import sqlite3
# import math
# import re
#
# # Local import
# from colors import *
#
#
# def is_multi(variation):
#     return 'multi' in variation or variation == 'f' or variation == 'fs'
#
#
# def get_identical(common_sku):
#     cursor.execute('SELECT identical_sku FROM identical WHERE sku = ?', (common_sku,))
#     db_sku = cursor.fetchone()
#     return db_sku[0].title() if db_sku else common_sku
#
#
# def identical(common_sku):
#     # Check if common sku is full sku
#     if '-' in common_sku:
#         product_tag, variation = [i.strip() for i in common_sku.split('-', 1)]
#         return f'{get_identical(product_tag)}-{get_identical(variation)}'
#     return get_identical(common_sku)
#
#
# # connect to database
# conn = sqlite3.connect('order_details.db')
# cursor = conn.cursor()
# cursor.execute('DELETE FROM campaign_data where TRUE')
#
# # Variable
# CLEAR = 2
# min_stock = 200
# delivery_cost = 0
#
#
# def main():
#     # Read the .xls file
#     df = pd.read_excel('D:/Downloads/fs.xlsx', header=0, skiprows=[1])
#
#     for index, row in df.iterrows():
#         serial = index.__hash__() + 2
#         price = math.floor(float(''.join(re.findall(r'\d+\.?\d*', row['Recommended Price']))))
#         seller_sku = row['Seller SKU'].lower()
#         sku_id = row['Sku ID']
#         product_name = row['Product Name']
#         identical_sku = identical(seller_sku)
#         product_tag, variation = seller_sku.split('-', 1)
#         identical_product_tag, identical_variation = identical_sku.split('-', 1)
#         cursor.execute('INSERT INTO campaign_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
#                        (serial, product_tag, variation, price, 0, False, seller_sku, sku_id, product_name))
#         cursor.execute('SELECT price, max_price FROM pricing WHERE product_tag = ?', (identical_sku,))
#         db_fetched = cursor.fetchone()
#         if cursor.fetchone() is not None:
#             min_price, max_price = db_fetched
#         else:
#             cursor.execute('SELECT price, max_price FROM pricing WHERE product_tag = ?',
#                            (identical_product_tag,))
#             db_fetched = cursor.fetchone()
#             if db_fetched is not None:
#                 min_price, max_price = db_fetched
#             else:
#                 print(BLUE, 'No pricing found for', seller_sku, RESET)
#                 if not is_multi(seller_sku.lower()):
#                     df.drop(index, inplace=True)
#                     continue
#                 min_price = price
#                 max_price = None
#         if max_price is None:
#             max_price = min_price
#         if price < min_price * (1 - CLEAR / 100) or price < 40:
#             df.drop(index, inplace=True)
#             print(RED, f'{serial}. {row['Seller SKU']} is dropped Price: {price}({min_price})', RESET)
#             continue
#         # Set price
#         evaluated_price = min(max_price, price)
#         df.loc[index, 'Campaign Price（Mandatory）'] = evaluated_price
#         cursor.execute('UPDATE campaign_data SET campaign_price = ? WHERE serial = ?',
#                        (evaluated_price, serial,))
#         # Set stock
#         if 'Campaign stock' in df.columns:
#             stock = int(row['Stock'])
#             if stock >= min_stock:
#                 df.loc[index, 'Campaign stock'] = min_stock
#             else:
#                 df.loc[index, 'Campaign stock'] = stock
#                 print(RED, f'Low stock({stock}) for {seller_sku}', RESET)
#
#         # Update status of eligible products
#         cursor.execute('UPDATE campaign_data SET status = TRUE WHERE serial = ?', (serial,))
#     conn.commit()
#
#     print(YELLOW, f' Permanently removed SKU '.center(50, '━'), RESET)
#     # Eliminated product check
#     cursor.execute('SELECT DISTINCT product_tag FROM campaign_data WHERE status = FALSE')
#     for product_tag in cursor.fetchall():
#         cursor.execute('SELECT * FROM campaign_data WHERE (product_tag, status) = (?, ?)',
#                        (product_tag[0], True))
#         if not cursor.fetchall():
#             cursor.execute('SELECT recommended_price, variation, sku_id, product_name FROM campaign_data WHERE product_tag = ?',
#                            (product_tag[0],))
#             # if 'rabbit' in product_tag[0].lower():
#             print(CYAN, product_tag[0].title(), RED, 'Permanently removed at', cursor.fetchall(), RESET)
#
#     print(YELLOW, f' Total row: {df.shape[0]} '.center(50, '━'), RESET)
#     file_path = 'D:/Downloads/fs out.xlsx'
#     with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
#         df.to_excel(writer, index=False, sheet_name='Sheet1')
#         worksheet = writer.sheets['Sheet1']
#
#         # Set the column width
#         worksheet.column_dimensions['A'].width = 40
#         worksheet.column_dimensions['G'].width = 20
#
#     # Show campaign price
#     cursor.execute('SELECT DISTINCT identical_sku FROM campaign_data WHERE campaign_price != 0')
#     for sku in cursor.fetchall():
#         cursor.execute('SELECT campaign_price FROM campaign_data WHERE identical_sku = ? '
#                        'AND campaign_price != 0 ORDER BY campaign_price', (sku[0],))
#         price_list = cursor.fetchall()
#         print(f'{sku[0].title()} ({price_list[0][0]} - {price_list[-1][0]}): {price_list}')
#
#
# if __name__ == "__main__":
#     main()
