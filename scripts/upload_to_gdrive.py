import os
import argparse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

def get_credentials():
    """Gets credentials from environment variables."""
    client_id = os.environ.get('GDRIVE_CLIENT_ID')
    client_secret = os.environ.get('GDRIVE_CLIENT_SECRET')
    refresh_token = os.environ.get('GDRIVE_REFRESH_TOKEN')

    if all([client_id, client_secret, refresh_token]):
        creds = Credentials(
            token=None,  # Will be refreshed
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        # Refresh the token if needed
        creds.refresh(Request())
        return creds
    
    # Fallback for Service Account (Old method, might still fail with 403 quota)
    creds_json = os.environ.get('GDRIVE_CREDENTIALS_JSON')
    if creds_json:
        import json
        from google.oauth2 import service_account
        creds_dict = json.loads(creds_json)
        return service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive.file']
        )

    print("Error: Missing Google Drive credentials environment variables.")
    return None

def upload_files(folder_id, file_paths):
    """Uploads files to a specific Google Drive folder."""
    creds = get_credentials()
    if not creds:
        return

    service = build('drive', 'v3', credentials=creds)

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        
        try:
            file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
            print(f"Uploaded {file_name} (ID: {file.get('id')})")
        except Exception as e:
            print(f"Failed to upload {file_name}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload files to Google Drive')
    parser.add_argument('--folder', required=True, help='Google Drive Folder ID')
    parser.add_argument('files', nargs='+', help='Files to upload')
    
    args = parser.parse_args()
    upload_files(args.folder, args.files)
