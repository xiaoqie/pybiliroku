# -*- coding:utf-8 -*-
import time
import json
import os

enabled = False

log = None
start_timestamp = None
file = None
ndanmaku = 0
savepath = None


def on_start(**kargs):
    global start_timestamp, file, savepath
    start_timestamp = kargs['start_timestamp']
    savepath = kargs['savepath'] + '.json'
    file = open(savepath, 'w', encoding='utf-8')
    file.write('[')
    file.flush()


def on_danmaku(danmaku):
    global ndanmaku, file
    infos = {'user': danmaku.user, 'text': danmaku.text, 'relative_timestamp': danmaku.timestamp - start_timestamp}
    log.info("{user} sent {text} in relative time {relative_timestamp}".format(**infos))
    if ndanmaku != 0:
        file.write(", \n")
    file.write(json.dumps(infos))
    file.flush()
    ndanmaku += 1
    

def on_end():
    global file
    file.write("]")
    file.flush()
    file.close()

    if ndanmaku == 0:
        os.remove(savepath)
        log.info("removed empty %s" % savepath)
