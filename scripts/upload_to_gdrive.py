import os
import json
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_files(folder_id, file_paths):
    """Uploads files to a specific Google Drive folder."""
    creds_json = os.environ.get('GDRIVE_CREDENTIALS_JSON')
    if not creds_json:
        print("Error: GDRIVE_CREDENTIALS_JSON environment variable not set.")
        return

    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    
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
