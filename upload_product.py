# import re
# import time
# import gspread
# import sqlite3
# import requests
# import random
# from PIL import Image
# from io import BytesIO
# import pandas as pd
# from datetime import datetime
# from bs4 import BeautifulSoup
# from openpyxl import load_workbook
# from openpyxl.styles import Alignment
# from oauth2client.service_account import ServiceAccountCredentials
#
# # connect to database
# conn = sqlite3.connect('order_details.db')
# cursor = conn.cursor()
#
# # Help image link
# for serial, shop_name in cursor.execute('SELECT serial, shop_name FROM unique_image').fetchall():
#     print(f'{serial}. {shop_name}')
# cursor.execute('SELECT url FROM unique_image WHERE serial = ?', (int(input('Enter serial: ')),))
# help_image = cursor.fetchone()[0]
#
#
# def column(header_name):
#     return df.columns.get_loc(header_name) + 1
#
#
# def cdn_link(link: str):
#     full_link = link.split('_')[0].strip()
#     if 'https://img.drz.lazcdn' in full_link:
#         link = full_link
#     else:
#         try:
#             link = 'https://img.drz.lazcdn.com/static/bd/p/' + full_link.split('/p/')[1]
#         except IndexError:
#             link = full_link
#     return link + f'?q={str(time.time()).replace(".", "")}'
#
#
# def image_dimensions(url):
#     response = requests.get(url)
#     img = Image.open(BytesIO(response.content))
#     return img.size  # returns (width, height)
#
#
# def add_image_element():
#     (image_width, image_height) = image_dimensions(image_url)
#     if image_width < 928:
#         image_width = 928
#         image_height = image_height / image_width * 928
#     image_element = soup.new_tag('img')
#     image_element['style'] = f"width:{image_width}px;height:{image_height}px;display:inline;vertical-align:middle"
#     image_element['src'] = image_url
#     paragraph.append(image_element)
#
#
# # Define the scope
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#
# # Add the path to the downloaded JSON key file
# creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
#
# # Authorize the client
# client = gspread.authorize(creds)
#
# # Open the Google Sheet
# spreadsheet = client.open('Daraz Product')
#
# # Variable
# file_path = r'D:\Downloads\product.xlsx'
# excel = load_workbook(file_path, rich_text=True)
# for sheet in excel.worksheets:
#     if cursor.execute('SELECT * FROM daraz_product WHERE category = ?', (sheet.title,)).fetchone():
#         sheet.delete_rows(3, sheet.max_row)
# excel.save(file_path)
#
# print('Updating', end='')
# cursor.execute('SELECT * FROM daraz_product LIMIT -1')
# for google_sheet_name, sheet_name, _ in cursor.fetchall():
#     df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
#     excel_sheet = excel[sheet_name]
#     # Select sheet
#     sheet = spreadsheet.worksheet(google_sheet_name)
#     main_image_series = list(range(1, 8))
#     random.shuffle(main_image_series)
#     sel_row = df.shape[0] + 3
#     # Update records
#     for index, row in enumerate(sheet.get_all_records()):
#         # Product name
#         excel_sheet.cell(row=sel_row, column=column('Group No'), value=google_sheet_name)
#         product_name_eng = row['Product name (English)'].title() + ' QR:' + time.strftime('%y%m%d%H%M%S')
#         excel_sheet.cell(row=sel_row, column=column('*Product Name(English)'), value=product_name_eng)
#         product_name_bn = row['Product name (Bangla)'] + ' QR:' + time.strftime('%y%m%d%H%M%S')
#         excel_sheet.cell(row=sel_row, column=column('Product Name(Bengali) look function'), value=product_name_bn)
#         print(' *', end='')
#         # Image, Description, SKU
#         soup = BeautifulSoup('', 'html.parser')
#         html = soup.new_tag('article')
#         html['style'] = "white-space:break-spaces"
#         html['class'] = "lzd-article"
#         soup.append(html)
#         paragraph = soup.new_tag('p')
#         paragraph['style'] = ("line-height:1.7;text-align:center;text-indent:0;margin-left:0;margin-top:0;margin"
#                               "-bottom:0")
#         html.append(paragraph)
#         text_element = soup.new_tag('span')
#         text_element['style'] = ("font-weight:bold;color:rgb(64, 64, 64);"
#                                  "background-color:rgb(255, 217, 102);font-size:12pt")
#         text_element.string = row['Main Description']
#         paragraph.append(text_element)
#
#         image_url = cdn_link(row[f'Product Images1'])
#         excel_sheet.cell(row=sel_row, column=column('*Product Images1')).hyperlink = image_url
#         # excel_sheet.cell(row=sel_row, column=column('*Product Images1')).style = 'Hyperlink'
#         excel_sheet.cell(row=sel_row, column=column('White Background Image')).hyperlink =image_url
#         # excel_sheet.cell(row=sel_row, column=column('White Background Image')).style = 'Hyperlink'
#         # SKU, Price
#         color_family = row['Color Family'].title()
#         try:
#             excel_sheet.cell(row=sel_row, column=column('*Color Family'), value=color_family)
#         except KeyError:
#             excel_sheet.cell(row=sel_row, column=column('Color Family'), value=color_family)
#         seller_sku = row['Seller SKU'].title()
#         excel_sheet.cell(row=sel_row, column=column('SellerSKU'), value=seller_sku + '-' + color_family)
#         sku_image = row['SKU Image']
#         excel_sheet.cell(row=sel_row, column=column('Images1')).hyperlink = cdn_link(sku_image)
#         # excel_sheet.cell(row=sel_row, column=column('Images1')).style = 'Hyperlink'
#         excel_sheet.cell(row=sel_row, column=column('*Quantity'), value='1000')
#         price = int(row['Price'])
#         excel_sheet.cell(row=sel_row, column=column('*Price'), value=str(max(round((price * 1.5) / 50) * 50, 120)))
#         excel_sheet.cell(row=sel_row, column=column('SpecialPrice'), value=str(price))
#         excel_sheet.cell(row=sel_row, column=column('SpecialPrice Start'),
#                          value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
#         excel_sheet.cell(row=sel_row, column=column('SpecialPrice End'), value='2099-08-05 00:00:00')
#
#         for serial, image_series in enumerate(main_image_series):
#             if image_series == 7:
#                 image_url = help_image
#             else:
#                 image_url = row[f'Product Images{image_series + 1}']
#             if image_url == '':
#                 continue
#             image_url = cdn_link(image_url)
#             excel_sheet.cell(row=sel_row, column=column(f'Product Images{serial + 2}')).hyperlink = image_url
#             # excel_sheet.cell(row=sel_row, column=column(f'Product Images{serial + 2}')).style = 'Hyperlink'
#             add_image_element()
#             print(' *', end='')
#         if row['Main Description Link'] != '':
#             for image_url in re.split(r'[ ,\n]+', row['Main Description Link'].strip()):
#                 image_url = cdn_link(image_url)
#                 add_image_element()
#         excel_sheet.cell(row=sel_row, column=column('Main Description'), value=str(soup))
#         # Additional
#         excel_sheet.cell(row=sel_row, column=column('*Brand'), value='No Brand')
#         excel_sheet.cell(row=sel_row, column=column('Warranty'), value='N/A')
#         excel_sheet.cell(row=sel_row, column=column('Warranty Type'), value='No Warranty')
#         # Measurement, weight
#         weight = row['Weight']
#         excel_sheet.cell(row=sel_row, column=column('*Package Weight (kg)'), value=weight)
#         length, width, height = row['Dimension (cm)'].split('x')
#         excel_sheet.cell(row=sel_row, column=column('*Package Length(cm) * Width(cm) * Height(cm)-Length (cm)'),
#                          value=length)
#         excel_sheet.cell(row=sel_row, column=column('*Package Length(cm) * Width(cm) * Height(cm)-Width (cm)'),
#                          value=width)
#         excel_sheet.cell(row=sel_row, column=column('*Package Length(cm) * Width(cm) * Height(cm)-Height (cm)'),
#                          value=height)
#         excel_sheet.cell(row=sel_row, column=column('Dangerous Goods'), value='None')
#         excel_sheet.cell(row=sel_row, column=column('What\'s in the box'), value='1 X ' + product_name_eng)
#         # Attribute
#         attributes = row['Attributes']
#         if attributes != '':
#             attributes = eval(attributes)
#             for attribute in attributes:
#                 excel_sheet.cell(row=sel_row, column=column(attribute), value=attributes[attribute])
#         # Highlights
#         soup = BeautifulSoup('', 'html.parser')
#         html = soup.new_tag('article')
#         html['style'] = "white-space:break-spaces"
#         html['class'] = "lzd-article"
#         soup.append(html)
#         unordered = soup.new_tag('ul')
#         html.append(unordered)
#         for highlight in row['Highlights'].split('\n'):
#             unordered_list = soup.new_tag('li')
#             unordered.append(unordered_list)
#             line = soup.new_tag('div')
#             line['style'] = "line-height:1.7;text-align:left;text-indent:0"
#             unordered_list.append(line)
#             line_str = soup.new_tag('span')
#             line_str.string = highlight.replace('●', '').replace('•', ' ').strip()
#             line.append(line_str)
#         excel_sheet.cell(row=sel_row, column=df.columns.get_loc('Highlights') + 1, value=str(soup))
#         # format row as wrap text
#         for cell in excel_sheet[f'{sel_row}:{sel_row}']:
#             cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
#         sel_row += 1
#     print('')
#     excel.save(file_path)
