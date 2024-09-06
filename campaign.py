import pandas as pd
import sqlite3
import math
import re


def identical(common_sku):
    cursor.execute('SELECT identical_sku FROM identical WHERE sku = ?', (common_sku,))
    db_sku = cursor.fetchone()
    return db_sku[0] if db_sku else common_sku


# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM campaign_data where TRUE')

# Variable
min_stock = 20

# Read the .xls file
df = pd.read_excel('D:/Downloads/fs.xlsx', header=0, skiprows=[1])

for index, row in df.iterrows():
    price = math.floor(float(''.join(re.findall(r'\d+\.?\d*', row['Recommended Price']))))
    if price < 50:
        df.drop(index, inplace=True)
        continue
    seller_sku = row['Seller SKU'].lower()
    product_tag, variation = [identical(i.strip()) for i in seller_sku.split('-', 1)]
    if 'multi' in variation or variation == 'f' or variation == 'fs':
        df.loc[index, 'Campaign Price（Mandatory）'] = price
        print(f'{product_tag} ({variation}) = {price}')
    else:
        df.drop(index, inplace=True)
        continue
    # Set stock
    if 'Campaign stock' in df.columns:
        stock = int(row['Stock'])
        if stock >= min_stock:
            df.loc[index, 'Campaign stock'] = min_stock
        else:
            df.loc[index, 'Campaign stock'] = stock
            print('Low Stock at', stock, 'of', seller_sku)
file_path = 'D:/Downloads/fs out.xlsx'
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    worksheet = writer.sheets['Sheet1']
    # Set the column width
    worksheet.column_dimensions['A'].width = 40
    worksheet.column_dimensions['G'].width = 20
    worksheet.column_dimensions['I'].width = 20
