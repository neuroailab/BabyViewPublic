import os
import tarfile
import argparse

import meta_extract.get_device_id as device
import download_data.download_videos as downloader
from meta_extract.get_highlight_flags import examine_mp4, sec2dtime
from shutil import move

ALL_METAS = [
    'ACCL', 'GYRO', 'SHUT', 'WBAL', 'WRGB',
    'ISOE', 'UNIF', 'FACE', 'CORI', 'MSKP',
    'IORI', 'GRAV', 'WNDM', 'MWET', 'AALP',
    'LSKP']


def extract_meta(video_folder, output_folder):
    videos = [f for f in os.listdir(video_folder) if f.endswith('.MP4')]
    for video in videos:
        video_path = os.path.join(video_folder, video)
        output_path = os.path.join(output_folder, video.split('.')[0])
        try:
            os.mkdir(output_path)
        except:
            print(f'{output_folder} already exists')
            pass
    
        for meta in ALL_METAS:            
            meta_path = os.path.join(
                output_path, f'{meta}_meta.txt')
            print(video_path, meta_path)
            cmd = f'../gpmf-parser/gpmf-parser {video_path} -f{meta} -a | tee {meta_path}'
            os.system(cmd)
    
        get_highlight_and_device_id(video_path, output_path)

        
def compress_vid(video_path, output_folder):
    output_path = os.path.join(output_folder, os.path.basename(video_path))
    cmd = f"ffmpeg -i {video_path} -c:v libx265 -vtag hvc1 -strict -2 {output_path} -speed 1200"
    os.system(cmd)
    
    
def get_highlight_and_device_id(video_path, output_folder):
    def save_info(all_info, output_path, info_type):
        assert info_type in ['highlights', 'device_id'], \
            'info_type needs to be either device_id or highlights'
        str2insert = ""        
        str2insert += fname + "\n"
        if info_type == 'highlights':
            for i, highl in enumerate(all_info):
                str2insert += "(" + str(i+1) + "): "
                str2insert += sec2dtime(highl) + "\n"
        elif info_type == 'device_id':
            str2insert += all_info
        str2insert += "\n"
        with open(output_path, "w") as f:
            f.write(str2insert)

    fname = os.path.basename(video_path).split('.')[0]
    # highlights = examine_mp4(video_path)
    # highlights.sort()    
    # highlight_path = os.path.join(output_folder, f'GP-Highlights_{fname}.txt')
    # print(video_path)
    # print(highlight_path)
    # save_info(highlights, highlight_path, 'highlights')
    # device_id = device.examine_mp4(video_path)    
    # device_id_path = os.path.join(output_folder, f'GP-Device_name_{fname}.txt')
    # save_info(device_id, device_id_path, 'device_id')
    # print(device_id_path) 
    compress_vid(video_path, output_folder)    

    
import json
import boto3
from zipfile import ZipFile
from botocore.exceptions import NoCredentialsError
#def aws_upload(output_folder, aws_access_key, aws_secret_key):
def aws_upload(output_folder, aws_key_path):
    aws_keys = json.load(open(aws_key_path, 'r'))
    aws_access_key = aws_keys['aws_access_key']
    aws_secret_key = aws_keys['aws_secret_key']    
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key,
                      aws_secret_access_key=aws_secret_key)
    bucket = 'babyview01'
    current_folder = os.getcwd()
    
    for vid_folder in os.listdir(output_folder):
        vid_folder = os.path.join(output_folder, vid_folder)
        if os.path.isdir(vid_folder):
            os.chdir(vid_folder)
            tar_file = f'{vid_folder}.tar'
            with tarfile.open(tar_file, "w") as tar_handle:
                for f in os.listdir(vid_folder):
                    tar_handle.add(f)
                    
            s3_file = os.path.basename(tar_file)
            try:
                s3.upload_file(tar_file, bucket, s3_file)
                print(f'{s3_file} Upload successful!')
            except FileNotFoundError:
                print("The file was not found")
            except NoCredentialsError:
                print("Credentials not available")
                
            os.chdir(current_folder)
            s3.download_file(bucket, s3_file, f'./{s3_file}')

    
def main():
    parser = argparse.ArgumentParser(description="Data management pipeline for GoPro videos")
    # downloader args
    parser.add_argument(
        '--video_root', type=str,
        default='/data/ziyxiang/BabyView/raw',
        help='folder for downloaded videos'
        )
    parser.add_argument(
        '--cred_folder', type=str,
        default='/ccn2/u/ziyxiang/cloud_credentials/babyview',
        help='Google Drive API credentials'
        )
    # metadata extraction args
    parser.add_argument(
        '--output_folder', type=str,
        default='/data/ziyxiang/BabyView/processed',
        help='Save folder for processed videos'
        )
    # upload args
    parser.add_argument(
        '--aws_key_path', type=str,
        default='/ccn2/u/ziyxiang/cloud_credentials/babyview/aws_keys.json',
        help='JSON file path with AWS access key and secret key'
    )
    args = parser.parse_args()
    #gdrive_downloader = downloader.GoogleDriveDownloader(args)
    #gdrive_downloader.download_videos()
    extract_meta(args.video_root, args.output_folder)
    aws_upload(
        args.output_folder, args.aws_key_path)
    
    
if __name__ == '__main__':
    main()
