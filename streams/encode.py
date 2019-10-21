# -*- coding:utf-8 -*-
import os
import datetime
from collections import defaultdict
from utils import *

videos = get_videos()
videos = videos_with(videos, _with=[".mp4", ".ass"])

for date, video_list in videos.items():
    output_dir = f'297/{str(date)}'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    else:
        continue

    p = 0
    for video in video_list:
        # if os.path.getsize(f"{video.path_without_ext}.mp4") < 30 * 1024*1024:  # 30 MiB
        #     continue

        if os.name == 'posix':
            with open(f'{video.path_without_ext}.ass') as inp:
                with open(f'temp.ass', 'w') as out:
                    out.write(inp.read().replace('黑体', 'WenQuanYi Micro Hei'))
        else:
            with open(f'{video.path_without_ext}.ass', encoding='utf-8') as inp:
                with open(f'temp.ass', 'w', encoding='utf-8') as out:
                    out.write(inp.read())

        print(f'{video.video_name}:', get_duration(f'{video.path_without_ext}.mp4'), "seconds")

        p += 1
        scale = '1280:720'
        bitrate = '2900k'
        #scale = '852:480'
        #bitrate = '1200k'
        #scale = '1920:1080'
        #bitrate = '5900k'
        cmd = (f'{ffmpeg} -analyzeduration 2147483647 -probesize 2147483647 -y -i "{video.path_without_ext}.mp4" -vf "subtitles=temp.ass, scale={scale}" -c:v libx264 -preset veryfast -b:v {bitrate} -c:a aac -b:a 128k -r 30 -max_muxing_queue_size 2000 "{output_dir}/P{p}_{video.title}_{video.time.strftime("%H-%M-%S")}.mp4"')
        os_system_ensure_success(cmd)
        move_to_trash(f'{video.path_without_ext}.mp4')
