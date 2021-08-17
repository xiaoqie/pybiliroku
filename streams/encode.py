# -*- coding:utf-8 -*-
import os
import datetime
from collections import defaultdict
from utils import *


if len(sys.argv) < 2:
    print("room id required")
    sys.exit()
room_id = sys.argv[1]
config = get_config(room_id)

videos = get_videos(int(room_id))
videos = videos_with(videos, _with=[".flv", ".ass"], _without=[".mp4"])
if videos.items():
    video_list = list(videos.values())[0]

    if video_list:
        video = video_list[0]

        resolution = video.resolution
        if min(resolution) >= 1080:
            bitrate = '3000k'
        else:
            bitrate = '2000k'
        if resolution[0] > resolution[1]:
            input_format = 'live_flv'
        else:
            input_format = 'flv'
        cmd = f'{ffmpeg} -analyzeduration 2147483647 -probesize 2147483647 -y -f {input_format} -i "{video.path_without_ext}.flv" -vf "subtitles=\\\'{video.path_without_ext}.ass\\\'" -c:v libx264 -preset superfast -b:v {bitrate} -c:a aac -b:a 128k -r 30 -max_muxing_queue_size 20000 "{video.path_without_ext}.mp4"'
        print(cmd)
        ret_code = os.system(cmd)
        if ret_code != 0:
            move_to_trash(f'{video.path_without_ext}.mp4')
            raise Exception(f"{cmd} returns non-zero status {ret_code}.")
        move_to_trash(f'{video.path_without_ext}.flv')
        move_to_trash(f'{video.path_without_ext}.ass')
        empty_trash()

