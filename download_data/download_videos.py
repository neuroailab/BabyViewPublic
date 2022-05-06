import os
import pdb
import ast
import json
import urllib
import zipfile
import argparse
import requests
import goproplus

from tqdm import tqdm
from shutil import move
from bs4 import BeautifulSoup


class GoProDownload:
    def __init__(self, args):
        self.args = args
        self.gp = goproplus.plus(args.email, args.password)
        self.access_token = self.gp.getToken()
        self.headers = {
            'Accept-Charset': 'utf-8',
            'Accept': 'application/vnd.gopro.jk.media+json; version=2.0.0',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.access_token}

    def get_video_ids(self):
        video_ids = []
        url = "%s/media/search" % self.gp.GOPRO_API_ENDPOINT        
        resp = requests.get(url, headers=self.headers)                
        resp.raise_for_status()
        resp = resp.json()
        pages = resp['_pages']['total_pages']
        for page in range(1, pages+1):
            page_url = f"{url}?page={page}"
            page_resp = requests.get(page_url, headers=self.headers).json()
            for id_dict in page_resp['_embedded']['media']:
                video_ids.append(id_dict['id'])
        return video_ids

    def download_videos(self):
        video_ids = self.get_video_ids()
        print(f"Downloading {len(video_ids)} videos")
        for video_id in tqdm(video_ids):
            download_url = f"https://api.gopro.com/media/{video_id}/download"
            try:
                resp = requests.get(download_url, headers=self.headers)
                resp.raise_for_status()
                content = resp.json()
                filename = content['filename']
                existing_videos = [
                    f.split('.')[0] for f in os.listdir(self.args.video_root)
                    if f.endswith('.MP4') or f.endswith('.zip')]
                if filename.split('.')[0] not in existing_videos:
                    video_path = os.path.join(self.args.video_root, filename)
                    video_url = content['_embedded']['files'][0]['url']
                    try:
                        urllib.request.urlretrieve(video_url, video_path)
                    except:
                        os.remove(video_path)
                        print(f'{filename} only has zip, creating new url')
                        filename = filename.replace('MP4', 'zip')
                        zip_path = os.path.join(self.args.video_root, filename)
                        video_url = f"https://api.gopro.com/media/{video_id}/zip/source?access_token={self.access_token}"
                        command = f'wget {video_url} -O {filename}'                    
                        try:
                            os.system(command)
                            move(filename, zip_path)
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(self.args.video_root)
                        except:                            
                            pass
            except:
                pass
                        
def main():
    email = 'email'
    password = 'password'
    video_root = 'root_path'
    parser = argparse.ArgumentParser(
        description="Download GoPro videos")
    parser.add_argument('--email', type=str, default=email)
    parser.add_argument('--password', type=str, default=password)
    parser.add_argument('--video_root', type=str, default=video_root)
    args = parser.parse_args()
    go_pro = GoProDownload(args)
    go_pro.download_videos()
    

if __name__ == '__main__':
    main()
