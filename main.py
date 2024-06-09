import io
import os
import PyPDF2
import csv
from reportlab.pdfgen import canvas


def sort_factory(order_details):
    page_no, seller_sku = order_details
    product_tag = seller_sku.split('-')[0].split(' ')[0].lower()
    color_family = seller_sku.split('-')[1].split('_')[0].lower()
    return product_tag + '-' + color_family


def create_watermark(text, overlay_page_size):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=overlay_page_size)
    can.setFont('Helvetica', 10)
    can.setFillColorRGB(0, 0, 00, alpha=1)
    can.saveState()
    can.drawCentredString(100, 5, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    return packet


directory = 'D:\\Downloads\\Daraz Invoice'
output_filename = 'merged.pdf'
if os.path.exists(os.path.join(directory, output_filename)):
    os.remove(os.path.join(directory, output_filename))
if os.path.exists(os.path.join(directory, 'Final.pdf')):
    os.remove(os.path.join(directory, 'Final.pdf'))

# Create a PDF merger object
pdf_merger = PyPDF2.PdfMerger()

# Get a list of all PDF files in the directory
pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
# Iterate over the PDF files and append them to the merger
for pdf in pdf_files:
    pdf_path = os.path.join(directory, pdf)
    pdf_merger.append(pdf_path)

# Write out the merged PDF
with open(os.path.join(directory, output_filename), 'wb') as output_file:
    pdf_merger.write(output_file)

order: list = []
label: list = []
for file in os.listdir(directory):
    if file.endswith('.csv'):
        with open(os.path.join(directory, file), 'r', newline='\n', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader)
            for row in reader:
                order_id = row[0].split(';')[8]
                sku = row[0].split(';')[4]
                order.append((order_id, sku))
                print(order_id, sku)

pw = PyPDF2.PdfWriter()
pdf_path = 'D:\\Downloads\\Daraz Invoice\\merged.pdf'
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page_size = (page.mediabox.width, page.mediabox.height)

        order_id = page.extract_text().split('COD')[1].split('\n')[1]
        quantity = int(page.extract_text().split('Item Quantity:')[1].split(' ')[0])
        for _ in range(quantity):
            for csv_order_id, sku in order:
                # print(csv_order_id, order_id)
                if csv_order_id == order_id:
                    label.append((page_num, sku))
                    print(csv_order_id, sku)
                    order.remove((order_id, sku))
                    break
        # Create a new PDF with the watermark
        watermark_pdf_data = create_watermark(sku, page_size)
        watermark_pdf = PyPDF2.PdfReader(watermark_pdf_data)
        watermark_page = watermark_pdf.pages[0]

        # Merge the watermark PDF with the original page
        page.merge_page(watermark_page)

        # Add the merged page to the PDF writer
        pw.add_page(page)

# Write the final PDF to a file
with open(pdf_path, 'wb') as output_pdf:
    pw.write(output_pdf)

label = sorted(label, key=sort_factory)
print(label)
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    pw = PyPDF2.PdfWriter()
    for page_num, sku in label:
        pw.add_page(reader.pages[page_num])
with open('D:\\Downloads\\Daraz Invoice\\Final.pdf', 'wb') as file:
    pw.write(file)
