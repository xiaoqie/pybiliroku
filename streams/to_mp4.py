# -*- coding:utf-8 -*-
import os
from utils import *

videos = get_videos()
videos = videos_with(videos, _with=[".flv"], _without=[".mp4"])
for video_list in videos.values():
    for video in video_list:
        cmd = f'{ffmpeg} -f live_flv -i "{video.path_without_ext}.flv" -vcodec copy -acodec copy "{video.path_without_ext}.mp4"'
        os_system_ensure_success(cmd)
        move_to_trash(f'{video.path_without_ext}.flv')
