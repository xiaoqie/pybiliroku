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

videos = get_videos()
unfinished_videos = videos_with(videos, _with=[".flv"])
videos = videos_with(videos, _with=[".mp4"])

if not videos:
    print("nothing to do")
    sys.exit()
    
last_uploaded_video_date = datetime.datetime.strptime(config['last_uploaded_video_date'], '%Y-%m-%d').date()
uploaded_video_info = get_json_from(f"http://space.bilibili.com/ajax/member/getSubmitVideos?mid={config['bilibili_mid']}")
uploaded_video_date = [datetime.datetime.strptime(v['title'][1:len('1970-01-01') + 1], '%Y-%m-%d').date() for v in uploaded_video_info['data']['vlist']]

for date, video_list in videos.items():
    if date in unfinished_videos or datetime.datetime.now() <= datetime.datetime.combine(date, datetime.time()) + datetime.timedelta(days=1, hours=6):
        print(f"{date} is yet to finish encoding")
    elif date in uploaded_video_date:
        print(f"{date} is uploaded and can be deleted")
        for video in video_list:
            move_to_trash(f"{video.path_without_ext}.mp4")
    elif date <= last_uploaded_video_date:
        print(f"{date} has been uploaded, but is yet to be verified")
    else:
        print(f"{date} is ready to upload")
        title = f"【{date.strftime('%Y-%m-%d')}】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in video_list]))])}"
        print(title)
        print(config['bilibili_cookie'])
        b = Bilibili(config['bilibili_cookie'])
        #print("login success?", b.login(config['bilibili_username'], config['bilibili_password']))
        with open("concat.list", "w") as l:
            for video in video_list:
                l.write(f"file '{os.getcwd()}/{video.path_without_ext}.mp4'\n")
        cmd = f"ffmpeg -y -f concat -safe 0 -i concat.list -c copy concat.mp4"
        os_system_ensure_success(cmd)
        # video_parts = [VideoPart(f"{video.path_without_ext}.mp4", f"{video.video_name}") for video in video_list]
        b.upload(parts=[VideoPart("concat.mp4", title)], title=title, tid=17, tag=["lolo直播录像"], desc='等了4个月，网页分P投稿功能还是没有回归。现在把视频合在一起上传，观看体验肯定不如分P')
        config['last_uploaded_video_date'] = date.strftime('%Y-%m-%d')
        json.dump(config, open("config.json", "w"))

        os.remove("concat.list")
        os.remove("concat.mp4")

        print("success")
        sys.exit()  # upload only once a time

print("nothing to do")
