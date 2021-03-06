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

        if os.name == 'posix':
            with open(f'{video.path_without_ext}.ass') as inp:
                with open(f'temp.ass', 'w') as out:
                    out.write(inp.read())
        else:
            with open(f'{video.path_without_ext}.ass', encoding='utf-8') as inp:
                with open(f'temp.ass', 'w', encoding='utf-8') as out:
                    out.write(inp.read())

        resolution = video.resolution
        if min(resolution) > 1080:
            scale = '-1:1080'
            bitrate = '3000k'
        else:
            scale = '-1:720'
            bitrate = '2000k'
        cmd = f'{ffmpeg} -analyzeduration 2147483647 -probesize 2147483647 -y -f live_flv -i "{video.path_without_ext}.flv" -vf "subtitles=temp.ass, scale={scale}" -c:v libx264 -preset superfast -b:v {bitrate} -c:a aac -b:a 128k -r 30 -max_muxing_queue_size 20000 "{video.path_without_ext}.mp4"'
        print(cmd)
        ret_code = os.system(cmd)
        if ret_code != 0:
            move_to_trash(f'{video.path_without_ext}.mp4')
            raise Exception(f"{cmd} returns non-zero status {ret_code}.")
        move_to_trash(f'{video.path_without_ext}.flv')
        move_to_trash(f'{video.path_without_ext}.ass')
        empty_trash()

