import os
import subprocess
import datetime
import sys
from typing import *
from collections import defaultdict
import shutil

if os.name == 'posix':
    ffprobe = '/usr/bin/ffprobe'
    ffmpeg = '/usr/bin/ffmpeg'
    NUL = '/dev/null'
else:
    ffprobe = 'ffprobe'
    ffmpeg = 'ffmpeg'
    NUL = 'NUL'


class BlockPrint:
    def __init__(self):
        self.total_line = 0
    
    def print(self, *args):
        print(*args)
        self.total_line += 1
    
    def clear(self):
        for i in range(self.total_line):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            sys.stdout.flush()
        self.total_line = 0


class Video:
    video_name: str
    available_exts: List[str]
    path_without_ext: str
    title: str
    date: datetime.date
    time: datetime.time
    datetime: datetime.datetime
    streamer: str

    def __str__(self):
        return f"""Video(video_name: {self.video_name}, available_exts: {self.available_exts}, path_without_ext: {self.path_without_ext}, datetime:{self.datetime}, title: {self.title}, date: {self.date}, time: {self.time}, streamer: {self.streamer})"""

    def __repr__(self):
        return str(self)

    def __init__(self):
        self.video_name = None
        self.available_exts = []
        self.path_without_ext = None
        self.title = None
        self.date = None
        self.streamer = None

    @staticmethod
    def from_filename(filename: str):
        """
        filename: filename with extension.
        returns None if the file is created in 30 mins
        """
        (video, ext) = os.path.splitext(filename)

        ret = Video()
        ret.video_name = video
        ret.available_exts = [ext]

        datetime_string = '-'.join(video.split('-')[0:5])
        datetime_obj = datetime.datetime.strptime(datetime_string, '%Y-%m-%d_%H-%M-%S')
        if (datetime.datetime.now() - datetime_obj).total_seconds() < 1800:
            return None

        ret.date = (datetime_obj - datetime.timedelta(hours=6)).date()
        ret.time = datetime_obj.time()
        ret.datetime = datetime_obj
        full_title = video[len('0000-00-00_00-00-00-'):]
        closing_bracket = full_title.find('】')
        if closing_bracket != -1:
            ret.streamer = full_title[1:closing_bracket]
            ret.title = full_title[closing_bracket + 1:]
        else:
            ret.streamer = "lolo"
            ret.title = full_title

        return ret

def get_videos() -> Dict[datetime.date, List[Video]]:
    def combine_videos(videos: List[Video]):
        """
        combine videos with the same name but with different exts
        """
        name_to_video: Dict[str, Video] = dict()
        for video in videos:
            if video.video_name in name_to_video:
                name_to_video[video.video_name].available_exts += video.available_exts
            else:
                name_to_video[video.video_name] = video
        return list(name_to_video.values())

    date_to_videos: Dict[datetime.date, List[Video]] = defaultdict(list)
    for filename in sorted(os.listdir("297")):
        filepath = "297/" + filename
        if os.path.isdir(filepath):
            continue
        video = Video.from_filename(filename)
        if video is None:
            continue
        (video.path_without_ext, _) = os.path.splitext(filepath)
        date_to_videos[video.date] += [video]

    date_to_videos = {k: combine_videos(v) for k, v in date_to_videos.items()}
    return date_to_videos

def move_to_trash(filepath):
    os.makedirs('trash', exist_ok=True)
    shutil.move(filepath, "trash/" + os.path.basename(filepath))

def empty_trash():
    shutil.rmtree("trash")

def os_system_ensure_success(cmd):
    print(cmd)
    ret_code = os.system(cmd)
    if ret_code != 0:
        raise Exception(f"{cmd} returns non-zero status {ret_code}.")

def videos_with(videos: Union[Dict[datetime.date, List[Video]], List[Video]], *, _with: str, _without: str = []):
    if isinstance(videos, dict):
        return {k: videos_with(v, _with=_with, _without=_without) for k, v in videos.items() if videos_with(v, _with=_with, _without=_without)}
    elif isinstance(videos, list):
        return [v for v in videos 
                if all(ext in v.available_exts for ext in _with)
                and not any(ext in v.available_exts for ext in _without)]
    else:
        raise Exception("Invalid argument `videos`")

def get_duration(path):
    cmd = [ffprobe, '-i', path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
    output = subprocess.check_output(cmd)
    return float(output)
