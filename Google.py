import pickle
import os
import datetime
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import base64

def decode_token():
    # Path to the encoded secret file in Render
    encoded_file_path = '/etc/secrets/encoded_token.txt'
    pickle_file_path = 'token_drive_v3.pickle'

    if os.path.exists(encoded_file_path):
        # Read the encoded Base64 token from the secret file
        with open(encoded_file_path, 'r') as encoded_file:
            encoded_token = encoded_file.read()

        # Decode the Base64 string
        decoded_token = base64.b64decode(encoded_token)

        # Write the decoded data to the pickle file
        with open(pickle_file_path, 'wb') as token_file:
            token_file.write(decoded_token)

        print(f"Decoded token saved to {pickle_file_path}")
    else:
        print("Encoded token file not found!")

# Call this function at the start of your script
decode_token()

# Then proceed with the usual flow to use the pickle file
def Create_Service(client_secret_file, api_name, api_version, scopes):
    cred = None
    pickle_file = f'token_{api_name}_{api_version}.pickle'

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
            cred = flow.run_local_server(port=8080, open_browser=False)

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(api_name, api_version, credentials=cred)
        print(f'{api_name} service created successfully')
        return service
    except Exception as e:
        print(f'Failed to create {api_name} service: {e}')
        return None

def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt