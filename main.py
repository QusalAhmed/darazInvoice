import io
import os
import re
import PyPDF2
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A5, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# import from local
from online_parcel import Parcel

# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM csv_data where TRUE')
cursor.execute('DELETE FROM pdf_data where TRUE')
cursor.execute('DELETE FROM outside_delivery where TRUE')

# Register the font
pdfmetrics.registerFont(TTFont('BanglaFont', 'font/Li Alinur Nakkhatra ANSI V2.ttf'))
pdfmetrics.registerFont(TTFont('Roboto', 'font/Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont('HARNGTON', 'HARNGTON.TTF'))

# ANSI escape sequences for colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


def identical(common_sku: str):
    cursor.execute('SELECT identical_sku FROM identical WHERE sku = ?', (common_sku,))
    identical_sku = cursor.fetchone()
    return identical_sku[0].strip() if identical_sku else common_sku.strip()


def sort_factory(order_details: tuple):
    order_number, seller_skus, page_number = order_details
    sort_text = 'Multi: ' + seller_skus if ',' in seller_skus else seller_skus
    # for seller_sku in seller_skus.split(','):
    #     product_tag = identical(seller_sku.split('-')[0].strip().lower())
    #     if seller_sku != '':
    #         color_family = identical(seller_sku.split('-')[1].split('_')[0].strip().lower())
    #     else:
    #         color_family = 'Unlisted'
    #     sort_text += identical(product_tag + '-' + color_family) + ', '
    cursor.execute('UPDATE pdf_data SET identity_sku = ? WHERE order_number = ?',
                   (sort_text.strip(', ').title(), order_number))
    conn.commit()
    cursor.execute('SELECT order_time FROM csv_data WHERE order_number = ?', (order_number,))
    return sort_text.title() + str(cursor.fetchone())


def create_watermark(text: str, overlay_page_size, x=10, y=None, font_size=10, font='Helvetica',
                     border=False, rotation=0, alpha: float = 1.0):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=overlay_page_size)
    can.setFont(font, font_size)
    can.setFillColorRGB(0, 0, 0, alpha=alpha)
    can.saveState()
    if y is None:
        y = int(overlay_page_size[1]) - 20
    can.translate(x, y)
    can.rotate(rotation)
    if border:
        can.setLineWidth(3)
        can.setStrokeAlpha(0.5)
        height = 60
        width = 200
        padding = 10
        can.roundRect(-padding, 2 * padding, width + 2 * padding, -(height + 2 * padding), 5)
    lin_space = 0
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 120:
            for i in range(0, len(line), 120):
                can.drawString(0, -lin_space, line[i:i + 120])
                lin_space += font_size + 5
        else:
            can.drawString(0, -lin_space, line)
            lin_space += font_size + 5
    can.save()
    packet.seek(0)
    return packet


def outside_delivery():
    cursor.execute('SELECT pay_method FROM csv_data WHERE order_number = ?', (order_id,))
    if cursor.fetchone()[0] != 'COD':
        return False
    delivery = 0
    cursor.execute('SELECT shipping_cost FROM csv_data WHERE order_number = ?', (order_id,))
    for single_shipping_fee in cursor.fetchall():
        delivery += single_shipping_fee[0]
    cursor.execute('SELECT shipping_city FROM csv_data WHERE order_number = ?', (order_id,))
    is_dhaka = 'D*h' in cursor.fetchone()
    if (55 >= delivery > 0 and is_dhaka) or delivery >= 110:
        try:
            voucher = float(page_text.split('Voucher:')[1].splitlines()[0].replace('-', ''))
        except IndexError:
            print("Voucher value couldn't extracted, set to 0")
            voucher = 0
        if voucher == 0:
            cursor.execute(
                'INSERT INTO outside_delivery (delivery_charge, is_dhaka, order_number) VALUES ( ?, ?, ?)',
                (delivery, is_dhaka, order_id))
            return True


# Variable
directory = r'D:\Downloads\Daraz Invoice'
merged_pdf = os.path.join(directory, 'merged.pdf')
final_file = os.path.join(directory, 'Final.pdf')
CLEAR = 2

if os.path.exists(merged_pdf):
    os.remove(merged_pdf)
if os.path.exists(final_file):
    os.remove(final_file)

# Create a PDF merger object
pdf_merger = PyPDF2.PdfMerger()

# Get a list of all PDF files in the directory
pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
# Iterate over the PDF files and append them to the merger
for pdf in pdf_files:
    pdf_path = os.path.join(directory, pdf)
    pdf_merger.append(pdf_path)

# Write out the merged PDF
with open(os.path.join(directory, merged_pdf), 'wb') as output_file:
    pdf_merger.write(output_file)

# Working with xlsx file
for file in os.listdir(directory):
    if file.endswith('.xlsx'):
        reader = pd.read_excel(os.path.join(directory, file), sheet_name='sheet1')
        for index, row in reader.iterrows():
            order_id = row['orderNumber']
            if row['status'] != 'ready_to_ship':
                print(RED + 'Ready to ship:', YELLOW, order_id, file, row['status'], index, RESET)
                # raise Exception
            sku = row['sellerSku']
            original_sku = identical(identical(sku.split('-')[0]) + '-' + identical(sku.split('-')[1].split('_')[0]))
            if row['shippingProvider'] == 'BD-RedX-API':
                print('Redex:', order_id, row['trackingCode'])
                original_sku = 'Redex'
            order_time = datetime.strptime(row['createTime'], '%d %b %Y %H:%M')
            shipping_cost = row['shippingFee']
            unit_price = row['unitPrice']
            pay_method = row['payMethod']
            shipping_city = row['shippingCity']
            tracking_code = row['trackingCode']
            lazadaSku = row['lazadaSku']
            seller_note = row['sellerNote']
            cursor.execute('INSERT INTO csv_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (order_id, sku, order_time.timestamp(), shipping_cost, unit_price, pay_method,
                            shipping_city, original_sku.title(), tracking_code, lazadaSku, file, seller_note))
            # Minimal pricing check
            cursor.execute('SELECT price FROM pricing WHERE product_tag = ?', (original_sku.split('-')[0],))
            try:
                min_price = cursor.fetchone()[0] * (1 - CLEAR / 100)
            except TypeError:
                if original_sku != 'Redex':
                    print(BLUE + f'Product tag not found: {original_sku}' + RESET)
                min_price = 0
            if unit_price < min_price:
                print(YELLOW + f'Price is less than expected ({order_id}): {unit_price} ({min_price})' + RESET)
conn.commit()

# Insert to pdf_data database
# cursor.execute("""INSERT INTO pdf_info (order_number, identity_sku, quantity)
#                SELECT order_number, GROUP_CONCAT(identical_sku), COUNT(identical_sku)
#                FROM csv_data GROUP BY order_number""")
# conn.commit()

# Working with pdf file
pw = PyPDF2.PdfWriter()
with open(merged_pdf, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page_size = (page.mediabox.width, page.mediabox.height)
        page_text = page.extract_text()
        try:
            order_id = page_text.split('KG')[0].split('\n')[-2].strip()
        except IndexError:
            if page.extract_text() != '':
                print(f'Page no {page_num} Skipped =>', "Can't find order number")
            else:
                print(f'Page no {page_num} Skipped')
            order_id = re.findall(r'6\d{14}', page_text)[-1]
        cursor.execute('SELECT sku FROM override_sku WHERE order_number = ?', (order_id,))
        sku = cursor.fetchall()
        if not sku:
            cursor.execute('SELECT identical_sku FROM csv_data WHERE order_number = ?', (order_id,))
            sku = cursor.fetchall()
        try:
            quantity = int(page_text.split('Item Qty:')[1].splitlines()[0])  #Item Qty:.*\d+
        except IndexError:
            quantity_text = re.findall(r'Item Qty:.*\d+', page_text)
            if quantity_text:
                quantity = int(quantity_text[0].split('Item Qty:').strip())
            else:
                print("Can't find quantity")
                sku_str = 'Error quantity: ' + ','.join(x[0] for x in sku)
        else:
            if len(sku) != quantity and len(sku) != 0:
                print(f'Item Quantity is {quantity} but found {len(sku)}')
                sku_str = 'Error quantity: ' + ','.join(x[0] for x in sku)
            else:
                sku_str = ','.join(x[0] for x in sku)
        try:
            phone = page_text.split('Phone: ')[1].splitlines()[0]  #Phone: \d{13}
        except IndexError:
            print("Can't find phone number")
            sku_str = 'Error phone: ' + ','.join(x[0] for x in sku)
            phone = order_id
        try:
            shop_name = page_text.split('Shipper Name:')[1].splitlines()[0]
        except IndexError:
            print("Can't find shop name")
            shop_name = ''
        cursor.execute('INSERT INTO pdf_data (order_number, seller_sku, page_number, phone) VALUES (?, ?, ?, ?)',
                       (order_id, sku_str, page_num, phone))
        cursor.execute('SELECT tracking_code FROM csv_data WHERE order_number = ?', (order_id,))
        tracking_code = ','.join(x[0] for x in cursor.fetchall())
        cursor.execute('SELECT lazadaSku FROM csv_data WHERE order_number = ?', (order_id,))
        lazada_sku = ','.join(x[0] for x in cursor.fetchall())
        if not Parcel().save(order_id, tracking_code, shop_name, ','.join(x[0] for x in sku), lazada_sku):
            print('Failed to save parcel', order_id, tracking_code, shop_name, ','.join(x[0] for x in sku),
                  lazada_sku)
        print(order_id, sku_str)
        # Outside delivery
        try:
            outside_delivery()
        except Exception as e:
            print("Can't check for outside delivery", order_id, e.__context__)

        # Seller note
        # cursor.execute('SELECT seller_note FROM csv_data WHERE order_number = ?', (order_id,))
        # seller_note = cursor.fetchone()[0]
        # if seller_note:
        #     watermark_pdf_data = create_watermark(seller_note, page_size, page_size[0] - 50, 180,
        #                                           font_size=16, rotation=90, alpha=0.5, font='HARNGTON')
        #     watermark_pdf = PyPDF2.PdfReader(watermark_pdf_data)
        #     watermark_page = watermark_pdf.pages[0]
        #     page.merge_page(watermark_page)

        # Create a new PDF with the watermark
        watermark_pdf_data = create_watermark(sku_str, page_size)
        watermark_pdf = PyPDF2.PdfReader(watermark_pdf_data)
        watermark_page = watermark_pdf.pages[0]

        # Merge the watermark PDF with the original page
        page.merge_page(watermark_page)

        # Add the merged page to the PDF writer
        pw.add_page(page)
    conn.commit()

# Write the final PDF to a file
with open(merged_pdf, 'wb') as output_pdf:
    pw.write(output_pdf)

# Duplicate order
for row in cursor.execute('SELECT COUNT(*), phone FROM pdf_data GROUP BY phone').fetchall():
    if row[0] > 1:
        cursor.execute('SELECT order_number FROM pdf_data WHERE phone = ?', (row[1],))
        print(YELLOW + f'Duplicate order({row[1]}): ' + ','.join(x[0] for x in cursor.fetchall()) + RESET)

cursor.execute('SELECT order_number, seller_sku, page_number FROM pdf_data')
label = sorted(cursor.fetchall(), key=sort_factory)

# Print order details on first page
pw = PyPDF2.PdfWriter()
cursor.execute('SELECT COUNT(*) FROM csv_data')
brief_heading = f'\tOrder Brief (Total: {cursor.fetchone()[0]})'
brief_heading_page = PyPDF2.PdfReader(create_watermark(brief_heading, landscape(A5), x=30, font_size=12))
count = 0
cursor.execute('SELECT identity_sku, COUNT(identity_sku) AS count FROM pdf_data GROUP BY identity_sku')
brief = ''
for row in cursor.fetchall():
    brief += f'{row[0]} : {str(row[1])} ({count + 1} - {row[1] + count})' + '\n'
    count += row[1]
index_page = PyPDF2.PdfReader(create_watermark(brief, landscape(A5), 30, y=landscape(A5)[1] - 40))
index_page.pages[0].merge_page(brief_heading_page.pages[0])
pw.add_page(index_page.pages[0])
current_date = datetime.now().strftime('%d %B %Y')
print('Sorting page', end='')  # Progress bar initialization
outside_delivery = ''
safety_text = "            mveavb!!\n  wfZ‡i Kv‡Pi wRwbm Av‡Q\nZvB e· †P‡c †QvU Ki‡eb bv"
with open(merged_pdf, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for index, (order_id, _, page_num) in enumerate(label):
        # Outside delivery
        cursor.execute('SELECT * FROM outside_delivery WHERE order_number = ?', (order_id,))
        if cursor.fetchall():
            cursor.execute('UPDATE outside_delivery SET page_number = ? WHERE order_number = ?',
                           (index + 2, order_id))
        print(' *', end='')  # Progress bar
        page = reader.pages[page_num]
        # Print date, page number and safety text
        page_size = (page.mediabox.width, page.mediabox.height)
        page.merge_page(PyPDF2.PdfReader(create_watermark(str(current_date), page_size, y=20)).pages[0])
        page.merge_page(PyPDF2.PdfReader(create_watermark(
            str(index + 1), page_size, page_size[0] - 30, 20, 12)).pages[0])
        safety_page = PyPDF2.PdfReader(create_watermark(safety_text, page_size, page_size[0] / 2 + 60, y=70,
                                                        font_size=20, font='BanglaFont', border=True,
                                                        rotation=15)).pages[0]
        # safety_page.add_transformation(Transformation().rotate(15))
        # safety_page.add_transformation(Transformation().translate(30, -10))
        page.merge_page(safety_page)
        pw.add_page(page)
conn.commit()
with open(final_file, 'wb') as file:
    pw.write(file)

# Upload file to dropbox
if input('\nUpload file to dropbox? '):
    from dropbox_connection import upload_file

    upload_file(final_file, '/Invoice/' + 'Final ' + datetime.now().strftime('%d %b %Y') + '.pdf')
    print('File uploaded to dropbox. Can be accessed from https://tinyurl.com/darazinvoice')
