# -*- coding:utf-8 -*-
import os
import datetime
from collections import defaultdict
import subprocess

if os.name == 'posix':
    ffprobe = '/usr/bin/ffprobe'
    ffmpeg = '/usr/bin/ffmpeg'
    NUL = '/dev/null'
else:
    ffprobe = 'ffprobe'
    ffmpeg = 'ffmpeg'
    NUL = 'NUL'


def get_duration(path):
    # cmd = f'{ffprobe} -i "{path}" -show_entries format=duration -v quiet -of csv=p=0'.split(' ')
    cmd = [ffprobe, '-i', path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
    output = subprocess.check_output(cmd)
    print(output)
    return float(output)


ls = os.listdir("297")
videos = []
for file in ls:
    name, ext = os.path.splitext(file)
    if ext == ".ass" and name + ".mp4" in ls and os.path.getsize("297/" + name + ".mp4") > 50 * 1024*1024:
        videos.append(name)

videos = sorted(videos)

date2videos = defaultdict(lambda: [])
for video in videos:
    datetime_string = '-'.join(video.split('-')[0:5])
    datetime_obj = datetime.datetime.strptime(datetime_string, '%Y-%m-%d_%H-%M-%S')
    date_str = str(datetime_obj - datetime.timedelta(hours=8)).split(' ')[0]
    date2videos[date_str] += [video]

for date_str, videos in date2videos.items():
    print(date_str, videos)
    output_dir = f'297/{date_str}'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    else:
        continue
    p = 0
    for video in videos:
        path = "297/" + video
        if os.name == 'posix':
            with open(f'{path}.ass') as inp:
                with open(f'temp.ass', 'w') as out:
                    out.write(inp.read().replace('黑体', 'WenQuanYi Micro Hei'))
        else:
            with open(f'{path}.ass', encoding='utf-8') as inp:
                with open(f'temp.ass', 'w', encoding='utf-8') as out:
                    out.write(inp.read())


        get_duration(f'{path}.mp4')  # for log purpose

        scale = '1280:720'
        bitrate = '2900k'
        #cmd = (f'{ffmpeg} -y -i "{path}.mp4" -vf "subtitles=temp.ass, scale={scale}" -c:v libx264 -preset veryfast -b:v {bitrate} -c:a aac -b:a 128k -f segment -segment_time 1800 -max_muxing_queue_size 2000 -reset_timestamps 1 -map 0 {output_dir}/T%d.mp4')
        cmd = (f'{ffmpeg} -y -i "{path}.mp4" -vf "subtitles=temp.ass, scale={scale}" -c:v libx264 -preset veryfast -b:v {bitrate} -c:a aac -b:a 128k -r 30 "{output_dir}/T0.mp4"')
        print(cmd)
        os.system(cmd)

        for filename in sorted([f for f in os.listdir(output_dir) if f[0] == 'T' and f.endswith('.mp4')], key=lambda s: int(s[1:-4])):
            p += 1
            os.rename(f'{output_dir}/{filename}', f'{output_dir}/P{p}_{video}.mp4')

        os.makedirs('trash', exist_ok=True)
        os.rename(path + ".mp4", "trash/" + video + ".mp4")
        os.system('rm -rf trash')

        os.remove('temp.ass')
