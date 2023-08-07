from __future__ import print_function

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

import io
import os
import argparse


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
    
    def count_videos(self):
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

        # start counting videos
        video_count = 0
        page_token = None
        all_mp4_files = []
        while True:
            try:
                service = build('drive', 'v3', credentials=creds)
                # Call the Drive v3 API                
                response = service.files().list(
                    driveId=self.babyview_drive_id,
                    corpora='drive',
                    pageSize=100,
                    pageToken=page_token,
                    orderBy='name',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    ).execute()
                items = response.get('files', [])                
                for item in items:
                    if 'MP4' in item['name']:                        
                        #print(f"video name: {item['name']}")
                        video_count += 1
                        all_mp4_files.append(item['name'])
                # Check for the nextPageToken
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break            
            except HttpError as err:
                print(f"An error occured {err}")
            
            print(f"Current number of videos: {video_count}")
        
        print(all_mp4_files)
        print(f"Total number of videos: {video_count}")

            

def main():
    video_root = "/data/ziyxiang/BabyView/"
    cred_folder = "/ccn2/u/ziyxiang/cloud_credentials/babyview"
    parser = argparse.ArgumentParser(
        description="Download videos from cloud services")
    parser.add_argument('--video_root', type=str, default=video_root)
    parser.add_argument('--cred_folder', type=str, default=cred_folder)
    parser.add_argument('--port', type=int, default=8080, help='port number needs to forward from local port')
    args = parser.parse_args()
    downloader = GoogleDriveDownloader(args)
    downloader.count_videos()


if __name__ == '__main__':
    main()
