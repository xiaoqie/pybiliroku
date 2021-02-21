import sys
import json
import datetime
import urllib.request
from pathlib import Path
from pprint import pprint
from bilibiliuploader import BilibiliUploader, VideoPart
from utils import *


def get_json_from(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as conn:
        response = conn.read()
        text = response.decode("utf-8") 
        info = json.loads(text) 
        return info


def upload(video_list, title):
    print(title)
    pprint([video.video_name for video in video_list])

    uploader = BilibiliUploader()
    uploader.login_by_access_token_file("bilibili_token.json")
    video_parts = [VideoPart(path=f"{video.path_without_ext}.mp4", title=f"{video.video_name}") for video in video_list]
    uploader.upload(parts=video_parts, title=title, tid=17, tag="lolo直播录像", desc='https://live.bilibili.com/297', copyright=1, thread_pool_workers=5, max_retry=10)


config = json.load(open("config.json"))
today = datetime.date.today() - datetime.timedelta(days=1)

videos = get_videos()
unfinished_videos = videos_with(videos, _with=[".flv"])
videos = videos_with(videos, _with=[".mp4"])
videos = sum(videos.values(), [])

uploaded_video_info = get_json_from(f"https://api.bilibili.com/x/space/arc/search?mid={config['bilibili_mid']}&ps=30&tid=0&pn=1&keyword=&order=pubdate&jsonp=jsonp")
uploaded_video_date = [datetime.datetime.strptime(v['title'][1:len('1970-01-01') + 1], '%Y-%m-%d').date() for v in uploaded_video_info['data']['list']['vlist']]
for date in uploaded_video_date:
    folder = Path("297") / date.strftime('%Y-%m-%d')
    if folder.exists() and folder.is_dir():
        print(f"remove {folder}")
        shutil.rmtree(folder)

if unfinished_videos:
    print("some videos have not finished encoding")
    sys.exit()
    
last_uploaded_video_date = datetime.datetime.strptime(config['last_uploaded_video_date'], '%Y-%m-%d').date()
if last_uploaded_video_date >= today:
    print("today has already been uploaded")
    sys.exit()

print(f"{today} is ready to upload")
title = f"【{today.strftime('%Y-%m-%d')}】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in videos]))])}"
upload(videos, title)

config['last_uploaded_video_date'] = today.strftime('%Y-%m-%d')
json.dump(config, open("config.json", "w"), indent=4)

uploaded_folder = Path("297") / today.strftime('%Y-%m-%d')
uploaded_folder.mkdir()
for video in videos:
    videopath = Path(f"{video.path_without_ext}.mp4")
    videopath.rename(uploaded_folder / videopath.name)

print("success")

