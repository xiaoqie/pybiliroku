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


def get_ids(room_id):
    with urllib.request.urlopen("https://api.live.bilibili.com/room/v1/Room/room_init?id=%d" % room_id, timeout=5) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        verbose("room_init returns %s" % result)
        if result['msg'] != 'ok':
            raise ValueError(
                "Error while requesting room ID:%s" % result['msg'])
        return (result['data']['room_id'], result['data']['uid'])


def get_flv_url(room_id):
    with urllib.request.urlopen("https://api.live.bilibili.com/api/playurl?cid=%d&otype=json&quality=0&platform=web" % room_id, timeout=5) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        verbose("playurl returns %s" % result)
        return random.choice(result["durl"])["url"]  # we don't know which url is valid, so random choose one


def get_info(uid):
    with urllib.request.urlopen("https://api.live.bilibili.com/room/v1/Room/get_info?room_id=%d&from=room" % uid, timeout=5) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        verbose("isliving returns %s" % result)
        return result["data"]


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
(room_id, uid) = get_ids(room_id)
verbose("Got room ID: %s, UID: %s" % (room_id, uid))
flv_url = get_flv_url(room_id)
verbose("Got flv URL: %s" % flv_url)
info = get_info(room_id)
title = info['title']
log(info)
if info['live_status'] == 1:
    title = title.replace('/', 'or')
    title = title.replace(' ', '_')
    log("Title: %s" % title)
else:
    verbose("UID:%s, Room ID:%s is not streaming, waiting for 30 seconds and closing." % (
        uid, original_room_id))
    # The sleep logic comes here, not in roku_loop.py
    # Because if it is streaming, this shouldn't wait to restart.
    time.sleep(30)
    quit()

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