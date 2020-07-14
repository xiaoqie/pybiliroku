import sys
import json
import datetime
import urllib.request
from pprint import pprint
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


def upload(video_list, title):
    print(title)
    pprint([video.video_name for video in video_list])
    b = Bilibili(config['bilibili_cookie'])
    #print("login success?", b.login(config['bilibili_username'], config['bilibili_password']))
    with open("concat.list", "w") as l:
        for video in video_list:
            l.write(f"file '{os.getcwd()}/{video.path_without_ext}.mp4'\n")
    cmd = f"ffmpeg -y -f concat -safe 0 -i concat.list -c copy concat.mp4"
    os_system_ensure_success(cmd)
    b.upload(parts=[VideoPart("concat.mp4", title)], title=title, tid=17, tag=["lolo直播录像"], desc='大概每天早上八点更新？b站单p视频有10个小时的限制。如果时长超过十个小时，会拆成两个视频上传。换了个机子，可以带更高码率了？')
    os.remove("concat.list")
    os.remove("concat.mp4")


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
        print(f"{date} encoding isn't finished yet")
    elif date in uploaded_video_date:
        print(f"{date} is uploaded and can be deleted")
        for video in video_list:
            move_to_trash(f"{video.path_without_ext}.mp4")
    elif date <= last_uploaded_video_date:
        print(f"{date} has been uploaded, but is not ready to watch yet")
    else:
        print(f"{date} is ready to upload")
        total_duration = sum(video.duration for video in video_list)
        if total_duration < 36000:
            title = f"【{date.strftime('%Y-%m-%d')}】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in video_list]))])}"
            upload(video_list, title)
        else:
            split_index = next(i for i in range(len(video_list)) if sum(video.duration for video in video_list[0:i+1]) >= 10*3600)
            title = f"【{date.strftime('%Y-%m-%d')}第一部分】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in video_list]))])}"
            upload(video_list[0:split_index], title)
            title = f"【{date.strftime('%Y-%m-%d')}第二部分】{'＋'.join([t.replace('！', '') for t in list(dict.fromkeys([v.title for v in video_list]))])}"
            upload(video_list[split_index:], title)

        config['last_uploaded_video_date'] = date.strftime('%Y-%m-%d')
        json.dump(config, open("config.json", "w"), indent=4)
        print("success")
        sys.exit()  # upload only once a time

print("nothing to do")
