# -*- coding:utf-8 -*-
import time
import json
import os

enabled = False

class Danmaku:
    def __init__(self, json_obj):
        self.is_danmaku = json_obj['cmd'] == "DANMU_MSG"

        if self.is_danmaku:
            self.text = json_obj["info"][1]
            self.user = json_obj["info"][2][1]
            self.timestamp = json_obj["info"][0][4]


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


def on_danmaku(json_obj):
    global ndanmaku, file
    danmaku = Danmaku(json_obj)
    if danmaku.is_danmaku:
        infos = {'user': danmaku.user, 'text': danmaku.text, 'relative_timestamp': danmaku.timestamp - start_timestamp}
        print("received danmaku: {user} sent {text} in relative time {relative_timestamp}".format(**infos))
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
        print("removed empty %s" % savepath)
