import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Local import
from online_parcel import Parcel

parcel = Parcel()

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Add the path to the downloaded JSON key file
creds = ServiceAccountCredentials.from_json_keyfile_name('credential/credentials.json', scope)

# Authorize the client
client = gspread.authorize(creds)

# Open the Google Sheet
spreadsheet = client.open('Daraz Parcel')

# Update the failed delivery
sheet = spreadsheet.worksheet('Failed Delivery')
for row in sheet.get_all_records(head=1):
    tracking_number = row['Tracking']
    print(tracking_number)
    if parcel.update_failed_parcel(tracking_number):
        if not parcel.update_status_by_tracking(tracking_number, 'Package Returned'):
            order_number = parcel.get_order_number_by_tracking(tracking_number)
            if not parcel.update_status(order_number, 'Package Returned'):
                print(f"Could not update to main order database {order_number}")
        sheet.delete_rows(sheet.find(row['Tracking']).row)
    else:
        print(f"Could not update to failed parcel database {tracking_number}")

# Update customer return parcel
sheet = spreadsheet.worksheet('Return')
for row in sheet.get_all_records(head=1):
    order_number = row['Order ID']
    print(order_number, end=' ')
    if parcel.update_status(order_number, 'Package Returned(Customer)'):
        print('Updated')
        sheet.delete_rows(sheet.find(row['Tracking']).row)
    else:
        print(f"Could not update to failed parcel database {order_number}")