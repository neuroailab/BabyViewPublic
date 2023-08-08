import os
import io
import argparse
import pandas as pd

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from moviepy.editor import VideoFileClip

from concurrent.futures import ThreadPoolExecutor
import threading


class GoogleDriveDownloader:
    def __init__(self, args):
        self.args = args
        self.babyview_drive_id = '0AJtfZGZvxvfxUk9PVA'
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.total_video_count = 0
        self.video_durations = {}  # initialize an empty dictionary to keep track of video durations
        self.lock = threading.Lock()  # lock for thread-safety

    def download_file(self, service, file_id, file_path):
        if os.path.exists(file_path):
            return
        print(f"Downloading to: {file_path}")
        # Uncomment the below for actual download
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}% complete.")
        with self.lock:
            self.total_video_count += 1

    def get_video_duration(self, file_path):
        with VideoFileClip(file_path) as clip:
            duration = clip.duration
            with self.lock:
                self.video_durations[file_path] = duration
                print(f"Video duration: {duration} seconds")

    def download_and_get_duration(self, service, file_id, file_path):
        self.download_file(service, file_id, file_path)
        self.get_video_duration(file_path)

    def recursive_search_and_download(self, service, folder_id, local_path):
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        page_token = None
        while True:
            results = service.files().list(
                driveId=self.babyview_drive_id,
                corpora='drive',
                q=f"'{folder_id}' in parents and trashed = false",  # exclude trashed items
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageToken=page_token
            ).execute()

            items = results.get('files', [])

            with ThreadPoolExecutor(max_workers=self.args.max_workers) as executor:
                futures = []
                for item in items:
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        self.recursive_search_and_download(service, item['id'], os.path.join(local_path, item['name']))
                    elif item['name'].endswith('.MP4'):
                        future = executor.submit(self.download_and_get_duration, service, item['id'], os.path.join(local_path, item['name']))
                        futures.append(future)

                for future in futures:
                    future.result()  # This will raise any exceptions encountered

            page_token = results.get('nextPageToken', None)
            if page_token is None:
                break

    def download_videos_from_drive(self):
        creds = None
        token_path = os.path.join(self.args.cred_folder, 'token.json')
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                cred_path = os.path.join(self.args.cred_folder, 'credentials.json')
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, self.SCOPES)
                creds = flow.run_local_server(port=self.args.port)

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)
        self.recursive_search_and_download(service, self.babyview_drive_id, self.args.video_root)

    def save_to_csv(self, csv_path):
        # Convert dictionary to DataFrame
        df = pd.DataFrame(list(self.video_durations.items()), columns=['File Path', 'Duration (s)'])
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
    
    def print_video_stats(self):
        total_duration = sum(self.video_durations.values())
        total_videos = len(self.video_durations)
        
        print(f"Total Number of Videos: {total_videos}")
        print(f"Total Duration of Videos: {total_duration} seconds")

        

def main():
    video_root = "/data/ziyxiang/BabyView/"
    cred_folder = "/ccn2/u/ziyxiang/cloud_credentials/babyview"
    parser = argparse.ArgumentParser(description="Download videos from cloud services")
    parser.add_argument('--video_root', type=str, default=video_root)
    parser.add_argument('--cred_folder', type=str, default=cred_folder)
    parser.add_argument('--max_workers', type=int, default=1)
    args = parser.parse_args()

    downloader = GoogleDriveDownloader(args)
    import time
    start = time.time()
    downloader.download_videos_from_drive()
    end = time.time()
    print(f"Downloaded {downloader.total_video_count} videos in {end - start} seconds")
    breakpoint()
    downloader.save_to_csv("video_durations.csv")
    downloader.print_video_stats()

if __name__ == '__main__':
    main()




# import argparse
# import os
# import io
# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseDownload
# from moviepy.editor import VideoFileClip
# # to makde download faster with multiple threads
# from concurrent.futures import ThreadPoolExecutor



# class GoogleDriveDownloader:
#     def __init__(self, args):
#         self.args = args
#         self.babyview_drive_id = '0AJtfZGZvxvfxUk9PVA'
#         self.SCOPES = ['https://www.googleapis.com/auth/drive']
#         self.total_video_count = 0
#         self.video_durations = {}  # initialize an empty dictionary to keep track of video durations

#     def download_file(self, service, file_id, file_path):
#         if os.path.exists(file_path):
#             return
#         print(f"Downloading to: {file_path}")
#         # request = service.files().get_media(fileId=file_id)
#         # fh = io.FileIO(file_path, 'wb')
#         # downloader = MediaIoBaseDownload(fh, request)
#         # done = False
#         # while not done:
#         #     status, done = downloader.next_chunk()
#         #     print(f"Download {int(status.progress() * 100)}% complete.")
#         self.total_video_count += 1
#         # After successfully downloading the file, get its duration
#         with VideoFileClip(file_path) as clip:
#             duration = clip.duration  # duration in seconds
#             self.video_durations[file_path] = duration
#             print(f"Video duration: {duration} seconds")

#     def download_and_get_duration(self, service, file_id, file_path):
#         self.download_file(service, file_id, file_path)
#         self.get_video_duration(file_path)

#     def get_video_duration(self, file_path):
#         with VideoFileClip(file_path) as clip:
#             duration = clip.duration
#             with threading.Lock():
#                 self.video_durations[file_path] = duration
#                 print(f"Video duration: {duration} seconds")

#     def recursive_search_and_download(self, service, folder_id, local_path):
#         # Create the folder locally
#         if not os.path.exists(local_path):
#             os.makedirs(local_path)

#         page_token = None
#         while True:
#             results = service.files().list(
#                 driveId=self.babyview_drive_id,
#                 corpora='drive',
#                 q=f"'{folder_id}' in parents and trashed = false",     # exclude trashed
#                 pageSize=1000,
#                 fields="nextPageToken, files(id, name, mimeType)",
#                 includeItemsFromAllDrives=True,
#                 supportsAllDrives=True,
#                 #trashed=False,
#                 pageToken=page_token
#             ).execute()

#             items = results.get('files', [])

#             for item in items:
#                 # If item is a folder
#                 if item['mimeType'] == 'application/vnd.google-apps.folder':
#                     self.recursive_search_and_download(service, item['id'], os.path.join(local_path, item['name']))
#                 # If item is an .MP4 file
#                 elif item['name'].endswith('.MP4'):
#                     self.download_file(service, item['id'], os.path.join(local_path, item['name']))

#             # Update the page_token for the next iteration
#             page_token = results.get('nextPageToken', None)
#             if page_token is None:
#                 break

#     def download_videos_from_drive(self):
#         creds = None
#         token_path = os.path.join(self.args.cred_folder, 'token.json')
#         if os.path.exists(token_path):
#             creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 cred_path = os.path.join(self.args.cred_folder, 'credentials.json')
#                 flow = InstalledAppFlow.from_client_secrets_file(cred_path, self.SCOPES)
#                 creds = flow.run_local_server(port=self.args.port)

#             with open(token_path, 'w') as token:
#                 token.write(creds.to_json())

#         service = build('drive', 'v3', credentials=creds)
#         self.recursive_search_and_download(service, self.babyview_drive_id, self.args.video_root)


# def main():
#     video_root = "/data/ziyxiang/BabyView/"
#     cred_folder = "/ccn2/u/ziyxiang/cloud_credentials/babyview"
#     parser = argparse.ArgumentParser(description="Download videos from cloud services")
#     parser.add_argument('--video_root', type=str, default=video_root)
#     parser.add_argument('--cred_folder', type=str, default=cred_folder)
#     parser.add_argument('--port', type=int, default=8080, help='port number needs to forward from local port')
#     args = parser.parse_args()
    
#     downloader = GoogleDriveDownloader(args)
#     import time
#     start = time.time()
#     downloader.download_videos_from_drive()
#     end = time.time()
#     print(f"download {downloader.total_video_count} videos took {end - start} seconds")
#     # no thread time: 


# if __name__ == '__main__':
#     main()