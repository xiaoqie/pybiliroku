exit()
import sys
import json
import datetime
import urllib.request
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

videos = get_videos()
unfinished_videos = videos_with(videos, _with=[".flv"])
videos = videos_with(videos, _with=[".mp4"])

if not videos:
    print("nothing to do")
    sys.exit()
    
last_uploaded_video_date = datetime.datetime.strptime(config['last_uploaded_video_date'], '%Y-%m-%d').date()
uploaded_video_info = get_json_from(f"https://api.bilibili.com/x/space/arc/search?mid={config['bilibili_mid']}&ps=30&tid=0&pn=1&keyword=&order=pubdate&jsonp=jsonp")
uploaded_video_date = [datetime.datetime.strptime(v['title'][1:len('1970-01-01') + 1], '%Y-%m-%d').date() for v in uploaded_video_info['data']['list']['vlist']]

for date, video_list in videos.items():
    if datetime.datetime.now() <= datetime.datetime.combine(date, datetime.time()) + datetime.timedelta(days=1, hours=6) or date in unfinished_videos:
        print(f"{date} encoding isn't finished yet")
    elif date in uploaded_video_date:
        print(f"{date} is uploaded and can be deleted")
        for video in video_list:
            move_to_trash(f"{video.path_without_ext}.mp4")
        empty_trash()
    elif date <= last_uploaded_video_date:
        print(f"{date} has been uploaded, but is not ready to watch yet")
    else:
        print(f"{date} is ready to upload")
        title = f"【{date.strftime('%Y-%m-%d')}】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in video_list]))])}"
        upload(video_list, title)

        config['last_uploaded_video_date'] = date.strftime('%Y-%m-%d')
        json.dump(config, open("config.json", "w"), indent=4)
        print("success")
        sys.exit()  # upload only once a time

print("nothing to do")
