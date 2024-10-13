# import requests
#
# # Dropbox app credentials
# app_key = 'oe6qai287ykyhz2'
# app_secret = 'o2h04bmk3dprao2'
# auth_code = 'EbZuB3wSugAAAAAAAAAAalsLNTL7nh_7lf4C_6uKgLA'
# redirect_uri = 'http://localhost'
#
# # Exchange authorization code for tokens
# url = "https://api.dropboxapi.com/oauth2/token"
# data = {
#     'code': auth_code,
#     'grant_type': 'authorization_code',
#     'client_id': app_key,
#     'client_secret': app_secret,
#     'redirect_uri': redirect_uri
# }
#
# response = requests.post(url, data=data)
#
# if response.status_code == 200:
#     tokens = response.json()
#     access_token = tokens['access_token']
#     refresh_token = tokens['refresh_token']
#     print(f"Access Token: {access_token}")
#     print(f"Refresh Token: {refresh_token}")
# else:
#     print(f"Error: {response.text}")

import os
from dotenv import load_dotenv
import dropbox

load_dotenv()
dbx = dropbox.Dropbox(
    oauth2_access_token=os.getenv('DROPBOX_ACCESS_TOKEN'),
    oauth2_refresh_token=os.getenv('DROPBOX_REFRESH_TOKEN'),
    app_key=os.getenv('DROPBOX_APP_KEY'),
    app_secret=os.getenv('DROPBOX_APP_SECRET')
)


def upload_file(file_path, target_path):
    with open(file_path, 'rb') as f:
        dbx.files_upload(f.read(), target_path)


for entry in dbx.files_list_folder('/Invoice').entries:
    print(f"Deleting: {entry.path_lower}")
    dbx.files_delete_v2(entry.path_lower)
# upload_file(r'D:\Downloads\Gaming edition rabbit.png', '/Invoice/20230824_131338_0000.png')

