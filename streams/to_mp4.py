# -*- coding:utf-8 -*-
import os

ffmpeg = '/usr/bin/ffmpeg' if os.name == 'posix' else 'ffmpeg'

# rooms = [d for d in os.listdir('.') if os.path.isdir(d)]
# rooms = [d for d in rooms if d.isdigit()]
rooms = ['297']
lss = [(room, os.listdir(room)) for room in rooms]
for (room, ls) in lss:
    videos = []
    for file in ls:
        name, ext = os.path.splitext(file)
        if ext == '.flv' and os.path.getsize(room + "/" + file) == 0:
            print("removed", room + "/" + file)
            os.makedirs('trash', exist_ok=True)
            os.rename(room + "/" + file, "trash/" + file)
        elif ext == '.ass' and open(room + "/" + file, encoding='utf-8').read() == """
[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1280
PlayResY: 720
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: testStyle,黑体,30,&H40ffffff,&H00000000,&H40000000,&H00000000,-1,0,0,0,100,100,0,0.00,1,2,0,7,0,0,0,0

[Events]
Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text
""":
            print("removed", room + "/" + file)
            os.makedirs('trash', exist_ok=True)
            os.rename(room + "/" + file, "trash/" + file)
        elif ext == ".flv" and name + ".mp4" not in ls:
            videos.append(name)

    for video in videos:
        path = room + "/" + video
        cmd = f"{ffmpeg} -f live_flv -i \"{path}.flv\" -vcodec copy -acodec copy \"{path}.mp4\""
        if os.system(cmd) == 0:
            os.makedirs('trash', exist_ok=True)
            os.rename(path + ".flv", "trash/" + video + ".flv")
            os.system('rm -rf trash')

