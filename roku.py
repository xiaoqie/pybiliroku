# -*- coding:utf-8 -*-
import argparse
import asyncio
import atexit
import datetime
import json
import os
import signal
import sys
import time
import urllib.request
import random

import danmaku
import modules
from _logging import error, log, verbose
from bs4 import BeautifulSoup


CHUNK_SIZE = 16 * 1024


parser = argparse.ArgumentParser()
parser.add_argument("--room-id", action="store",
                    dest="room_id", type=int, required=True)
parser.add_argument("--savepath", action="store",
                    dest="savepath", required=True)
parser.add_argument("--time-format", action="store",
                    dest="time_format", default='%Y-%m-%d_%H-%M-%S')
for name, params in modules.request_args.items():
    parser.add_argument(name, **params)
args = parser.parse_args()
original_room_id = room_id = args.room_id
savepath = args.savepath
start_time = datetime.datetime.now().strftime(args.time_format)


def get_info(uid):
    url = f"https://live.bilibili.com/{uid}"
    req = urllib.request.Request(
       url, 
        data=None, 
        headers={
            'Host': 'live.bilibili.com',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': 1,
            'DNT': 1,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en,zh;q=0.9,ja;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6'
        }
    )
    with urllib.request.urlopen(req) as conn:
        response = conn.read()
        parsed = BeautifulSoup(response, "lxml")
        scripts = parsed.body.find('div', attrs={'class': 'script-requirement'})
        for script in scripts.find_all('script'):
            text = script.text
            if '__NEPTUNE_IS_MY_WAIFU__' in text:
                info_json = text[text.find('{'):]
                break
        else:
            raise RuntimeError("Could not get info.")
        
        info = json.loads(info_json)
        verbose("GET returns %s" % json.dumps(info, indent=4))
        return info


async def download_flv(flv_url):
    total_downloaded = 0
    # FIXME async is not working due to frequent timeout
    with urllib.request.urlopen(flv_url, timeout=5) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                raise RuntimeError("File ended, this ususally is not an error.")

            modules.on_chunk(chunk)
            total_downloaded += CHUNK_SIZE

            await asyncio.sleep(0)


verbose("Starting.")
info = get_info(room_id)

room_id = info['roomInitRes']['data']['room_id']
uid = info['roomInitRes']['data']['uid']

is_living = info['baseInfoRes']['data']['live_status'] == 1
if not is_living:
    verbose("UID:%s, Room ID:%s is not streaming, waiting for 30 seconds and closing." % (
        uid, original_room_id))
    # The sleep logic comes here, not in roku_loop.py
    # Because if it is streaming, this shouldn't wait to restart.
    time.sleep(30)
    quit()

title = info['baseInfoRes']['data']['title']
title = title.replace('/', 'or')
title = title.replace(' ', '_')
log("Title: %s" % title)

flv_url = random.choice(info['playUrlRes']['data']["durl"])["url"]
log("Got flv URL: %s" % flv_url)

start_timestamp = time.time()
savepath = savepath.format(**globals())
os.makedirs(os.path.dirname(savepath), exist_ok=True)
log("Savepath: %s" % savepath)
modules.on_start(**globals())


asyncio.new_event_loop()
loop = asyncio.get_event_loop()

tasks = []
tasks += [asyncio.ensure_future(download_flv(flv_url))]
tasks += danmaku.connect(room_id, loop, modules.on_danmaku)


async def main(tasks, loop):
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        loop.stop()
        raise
    # only hardware malfunctions could achieve this line of code, i guess
    error("while True: ended without exception, WHAAAAT?!")


try:
    loop.run_until_complete(main(tasks, loop))
finally:
    loop.close()
    modules.on_end()
    log("Closed.")
