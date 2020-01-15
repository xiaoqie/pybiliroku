import sys
import json
import datetime
import urllib.request
import logging
logging.basicConfig(level=logging.INFO)
from bilibiliupload import *
from utils import *


def get_json_from(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as conn:
        response = conn.read()
        text = response.decode("utf-8") 
        info = json.loads(text) 
        return info

config = json.load(open("config.json"))

last_uploaded_video_date = datetime.datetime.strptime(config['last_uploaded_video_date'], '%Y-%m-%d').date()
uploaded_video_info = get_json_from(f"https://api.kaaass.net/biliapi/user/contribute?id={config['bilibili_mid']}")
uploaded_video_date = [datetime.datetime.strptime(v['title'][1:len('1970-01-01') + 1], '%Y-%m-%d').date() for v in uploaded_video_info['data']]

videos = get_videos()
videos = videos_with(videos, _with=[".mp4"])
unfinished_videos = videos_with(videos, _with=[".flv"])
for date, video_list in videos.items():
    if date in unfinished_videos:
        print(f"{date} is yet to finish encoding")
    elif date in uploaded_video_date:
        print(f"{date} is uploaded and can be deleted")
        for video in video_list:
            move_to_trash(f"{video.path_without_ext}.mp4")
    elif date <= last_uploaded_video_date:
        print(f"{date} has been uploaded, but is yet to be verified")
    else:
        print(f"{date} is ready to upload")
        title = f"【{date.strftime('%Y-%m-%d')}】{'，'.join(list(dict.fromkeys([v.title for v in video_list])))}"
        print(title)
        b = Bilibili()
        print("login success?", b.login(config['bilibili_username'], config['bilibili_password']))
        video_parts = [VideoPart(f"{video.path_without_ext}.mp4", f"{video.video_name}") for video in video_list]
        b.upload(parts=video_parts, title=title, tid=17, tag=["lolo直播录像"], desc='更新喽')
        config['last_uploaded_video_date'] = date.strftime('%Y-%m-%d')
        json.dump(config, open("config.json", "w"))
        print("success")
        sys.exit()  # upload only once a time


