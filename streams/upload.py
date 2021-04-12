import sys
import json
import datetime
import urllib.request
from pathlib import Path
from pprint import pprint
from bilibiliuploader import BilibiliUploader, VideoPart
from utils import *


if len(sys.argv) < 2:
    print("room id required")
    sys.exit()
room_id = sys.argv[1]
config = get_config(room_id)
if config['night']:
    today = datetime.date.today() - datetime.timedelta(days=1)
else:
    today = datetime.date.today()


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
    uploader.login_by_access_token_file(config["token_file"])
    uploader.do_token_refresh()
    uploader.save_login_data(file_name=config["token_file"])
    video_parts = [VideoPart(path=f"{video.path_without_ext}.mp4", title=f"{video.video_name}") for video in video_list]
    uploader.upload(parts=video_parts, 
            title=title, 
            tid=17, 
            tag=config['tag'], 
            desc='lolo直播间：https://live.bilibili.com/297\n爱莉直播间：https://live.bilibili.com/8054378', 
            copyright=1, 
            thread_pool_workers=5)


videos = get_videos(int(room_id))
videos = videos_with(videos, _with=[".mp4"])
videos = sum(videos.values(), [])

uploaded_video_info = get_json_from(f"https://api.bilibili.com/x/space/arc/search?mid={config['bilibili_mid']}&ps=30&tid=0&pn=1&keyword=&order=pubdate&jsonp=jsonp")
uploaded_video_titles = [v['title'].replace("/", "|").replace(" ", "_") for v in uploaded_video_info['data']['list']['vlist']]
for t in uploaded_video_titles:
    folder = Path(room_id) / t
    if folder.exists() and folder.is_dir():
        print(f"remove {folder}")
        shutil.rmtree(folder)

if list(Path(room_id).glob("*.flv")):
    print("some videos have not finished encoding")
    sys.exit()
    
last_uploaded_video_date = datetime.datetime.strptime(config['last_uploaded_video_date'], '%Y-%m-%d').date()
if last_uploaded_video_date >= today:
    print("today has already been uploaded")
    sys.exit()

print(f"{today} is ready to upload")
title = f"【{today.strftime('%Y-%m-%d')} {config['name']}】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in videos]))])}"
upload(videos, title)

config['last_uploaded_video_date'] = today.strftime('%Y-%m-%d')
save_config(room_id, config)

uploaded_folder = Path(room_id) / title.replace("/", "|").replace(" ", "_")
uploaded_folder.mkdir()
for video in videos:
    videopath = Path(f"{video.path_without_ext}.mp4")
    videopath.rename(uploaded_folder / videopath.name)

print("success")

