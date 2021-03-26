# -*- coding:utf-8 -*-
import time
import math
import os
import unicodedata
from types import SimpleNamespace


def toasstime(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d.%02d" % (h, m, s, int(str(int(math.modf(sec)[0] * 1000))[:2]))


def intersect(old, new):
    vel_old = (1280 + old.len * 30) / 10
    pos_old = vel_old * (new.sec - old.sec) - old.len * 30

    vel_new = (1280 + new.len * 30) / 10
    pos_new = 0

    # if old is ahead of new and old is ahead at the end, then no intesect
    if pos_old > pos_new and pos_old + vel_old * (10 - new.sec + old.sec) > vel_new * (10 - new.sec + old.sec):
        return False
    else:
        return True


log = None
start_timestamp = None
file = None
onscreen = {j: [] for j in range(21)}  # 720/35 = 21 columns
danmaku_count = 0
savepath = None


def on_start(**kargs):
    global start_timestamp, file, savepath
    start_timestamp = kargs['start_timestamp']
    savepath = kargs['savepath'] + '.ass'
    file = open(savepath, 'w', encoding='utf-8')
    file.write(u"""\
[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1280
PlayResY: 720
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: testStyle,WenQuanYi Micro Hei,30,&H00ffffff,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0.00,1,2,0,7,0,0,0,0

[Events]
Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text
""")
    file.flush()


def char_len(text):
    length = 0
    for c in text:
        if unicodedata.east_asian_width(c) in ['W', 'F', 'A']:
            length += 1
        else:
            length += 0.5
    return length


def on_danmaku(danmaku):
    global file, onscreen, danmaku_count
    log.info(f"{danmaku.user} sent {danmaku.text} in relative time {danmaku.timestamp - start_timestamp}")

    danmaku_count += 1

    text = danmaku.text
    sec = danmaku.timestamp - start_timestamp  # wait a sec, why does this work?
    onscreen = {j: [data for data in onscreen[j] if sec - data.sec < 10]
                for j in range(21)}  # remove old off screen text
    screen_record = SimpleNamespace(sec=sec, len=char_len(text))
    for j in range(21):  # 720/35 = 21 columns
        for text_on_screen in onscreen[j]:
            if intersect(text_on_screen, screen_record):
                break
        else:  # no intersection found
            column = j
            onscreen[j].append(screen_record)
            break
    else:
        log.warning(f'cannot find a place for danmaku "{text}", ignored')
        return

    y = column * 35
    end_x = -30 * char_len(text)
    file.write(f'Dialogue: 0,{toasstime(sec)},{toasstime(sec + 10)},testStyle,,0000,0000,0000,,{{\move(1280,{y},{end_x},{y})}}{text}\n')
    file.flush()


def on_end():
    global file
    file.close()

