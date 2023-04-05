from __future__ import print_function

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

import io
import os
import sys
import pdb
import ast
import json
import urllib
import zipfile
import argparse
import requests
#sys.path.append('/mnt/fs1/ziyxiang/BabyViewPublic/download_data/')


# write a function to download videos from google drive
# 1. get the video id from the google drive link
# 2. download the video from the video id
# 3. save the video to the video_root
class GoogleDriveDownloader:
    def __init__(self, args):
        self.args = args
        self.babyview_drive_id = '0AJtfZGZvxvfxUk9PVA'
        self.SCOPES = ['https://www.googleapis.com/auth/drive']

    def download_file(self, service, file_id, file_name, file_path):
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))        
    
    def download_videos(self):
        creds = None
        token_path = os.path.join(self.args.cred_folder, 'token.json')
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                cred_path = os.path.join(self.args.cred_folder, 'credentials.json')
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, self.SCOPES)
                creds = flow.run_local_server(port=self.args.port)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('drive', 'v3', credentials=creds)                 
            # Call the Drive v3 API
            results = service.files().list(                
                driveId=self.babyview_drive_id,
                corpora='drive',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True).execute()
            items = results.get('files', [])
            for item in items:
                if 'mp4' in item['mimeType']:
                    try:
                        save_path = os.path.join(self.args.video_root, item['name'])
                        self.download_file(service, item['id'], item['name'], save_path)
                        print(f"saved item {item['name']} to {save_path}")
                    except Exception as err:
                        print(f"An error occured {err}")
        except HttpError as err:
            print(f"An error occured {err}")
            

def main():
    video_root = "/data/ziyxiang/Babyview/raw_videos"
    cred_folder = "/mnt/fs4/ziyxiang/cloud/babyview"
    parser = argparse.ArgumentParser(
        description="Download videos from cloud services")
    parser.add_argument('--video_root', type=str, default=video_root)
    parser.add_argument('--cred_folder', type=str, default=cred_folder)
    parser.add_argument('--port', type=int, default=8080, help='port number needs to forward from local port')
    args = parser.parse_args()
    downloader = GoogleDriveDownloader(args)
    downloader.download_videos()


if __name__ == '__main__':
    main()
