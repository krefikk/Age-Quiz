from googleapiclient.discovery import build
from google.oauth2 import service_account
from Google import Create_Service
import os
import json

CLIENT_SECRET_JSON = os.environ.get("CLIENT_SECRET_JSON")
if CLIENT_SECRET_JSON:
    credentials_data = json.loads(CLIENT_SECRET_JSON)
    with open("age_quiz_client_secret.json", "w") as json_file:
        json.dump(credentials_data, json_file)
    CLIENT_SECRET_FILE = "age_quiz_client_secret.json"
else:
    raise Exception("CLIENT_SECRET_JSON environment variable is missing!")

API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

FOLDER_ID = "1eGPQqlYmDnSSig4RzOWCm6eFE1w6YmUi"

def list_drive_photos(folder_id):
    query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
    page_token = None
    photo_links = []
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageToken=page_token
        ).execute()
        
        for file in response.get('files', []):
            file_id = file['id']
            photo_url = f"https://lh3.googleusercontent.com/d/{file_id}=s800"
            photo_links.append((file['name'], photo_url))
        
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    return photo_links
