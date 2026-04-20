import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes needed for the script
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_tokens():
    """
    Instructions for the user:
    1. Go to https://console.cloud.google.com/
    2. Create/select a project.
    3. Enable "Google Drive API".
    4. Go to "Credentials" -> "Create Credentials" -> "OAuth client ID".
    5. Select "Desktop app", name it, and click "Create".
    6. Download the JSON (it will be named something like client_secret_XXXX.json).
    7. Rename it to 'client_secrets.json' and place it in the same directory as this script.
    8. Run this script: python scripts/get_gdrive_tokens.py
    """
    client_secrets_path = 'client_secrets.json'
    
    if not os.path.exists(client_secrets_path):
        print(f"Error: {client_secrets_path} not found.")
        print("Please follow the instructions in the script's docstring.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\nSuccessfully authenticated!")
    print("-" * 20)
    print(f"CLIENT_ID: {creds.client_id}")
    print(f"CLIENT_SECRET: {creds.client_secret}")
    print(f"REFRESH_TOKEN: {creds.refresh_token}")
    print("-" * 20)
    print("\nCopy these values to your GitHub Repository Secrets.")

if __name__ == '__main__':
    get_tokens()
