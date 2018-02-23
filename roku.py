# -*- coding:utf-8 -*-
import asyncio
import atexit
import json
import sys
import urllib.request
import time
import os
import argparse
import datetime

import danmaku
from _logging import log, verbose, error


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--room-id", action="store", dest="room_id", type=int, required=True)
parser.add_argument("-s", "--savepath", action="store", dest="savepath", required=True)
parser.add_argument("--time-format", action="store", dest="time_format", default='%Y-%m-%d_%H-%M-%S')
args = parser.parse_args()
original_room_id = room_id = args.room_id
savepath = args.savepath
start_time = datetime.datetime.now().strftime(args.time_format)


on_starts = []
on_ends = []
on_danmakus = []
on_chunks = []
log("Loading modules.")
for module_file in os.listdir("module"):
    filename, ext = os.path.splitext(module_file)
    if filename == "__init__" or ext != ".py":
        continue
    module = __import__("module.%s" % filename)
    try:
        on_starts.append(getattr(module, filename).on_start)
        log("loaded %s.on_start" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_ends.append(getattr(module, filename).on_end)
        log("loaded %s.on_end" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_danmakus.append(getattr(module, filename).on_danmaku)
        log("loaded %s.on_danmaku" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_chunks.append(getattr(module, filename).on_chunk)
        log("loaded %s.on_chunk" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
log("Complete loading modules.")


CHUNK_SIZE = 16 * 1024


def get_ids(room_id):
    """
    TODO: Add exception handling
    """
    with urllib.request.urlopen("https://api.live.bilibili.com/room/v1/Room/room_init?id=%d" % room_id) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        verbose("room_init returns %s" % result)
        if result['msg'] != 'ok':
            raise ValueError(
                "Error while requesting room ID:%s" % result['msg'])
        return (result['data']['room_id'], result['data']['uid'])


def get_flv_url(room_id):
    with urllib.request.urlopen("https://api.live.bilibili.com/api/playurl?cid=%d&otype=json&quality=0&platform=web" % room_id) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        verbose("playurl returns %s" % result)
        return result["durl"][0]["url"]


def is_living(uid):
    with urllib.request.urlopen("http://live.bilibili.com/bili/isliving/%d" % uid) as conn:
        content = conn.read().decode("utf-8")[1:-2]
        result = json.loads(content)
        verbose("isliving returns %s" % result)
        return result["data"]


async def download_flv(flv_url):
    total_downloaded = 0
    response = urllib.request.urlopen(flv_url)  # FIXME async is not working due to frequent timeout
    while True:
        chunk = response.read(CHUNK_SIZE)
        if not chunk:
            raise RuntimeError("File ended, this ususally is not an error.")

        for on_chunk in on_chunks:
            try:
                on_chunk(chunk)
            except Exception as e:
                error(e)
        total_downloaded += CHUNK_SIZE

        await asyncio.sleep(0)


log("Starting.")
(room_id, uid) = get_ids(room_id)
verbose("Got room ID: %s, UID: %s" % (room_id, uid))
flv_url = get_flv_url(room_id)
verbose("Got flv URL: %s" % flv_url)
is_living_resp = is_living(uid)
title = None
if is_living_resp:
    title = is_living_resp['title']
    log("Title: %s" % title)
else:
    log("UID:%s is not streaming, waiting for 30 seconds and closing." % uid)
    # The sleep logic comes here rather than in roku_loop.py
    # Because if it is streaming, this shouldn't wait to restart.
    time.sleep(30)
    quit()

start_timestamp = time.time()
savepath = savepath.format(**globals())
os.makedirs(os.path.dirname(savepath), exist_ok=True)
log("Savepath: %s" % savepath)
for on_start in on_starts:
    try:
        on_start(**globals())
    except Exception as e:
        error(e)

asyncio.new_event_loop()
loop = asyncio.get_event_loop()

tasks = []
tasks += [asyncio.ensure_future(download_flv(flv_url))]
tasks += danmaku.connect(room_id, loop, on_danmakus)


async def main(tasks, loop):
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        loop.stop()
        raise
    error("while True: ended without exception, WHAAAAT?!")  # only hardware malfunctions could achieve this line of code, i guess


try:
    loop.run_until_complete(main(tasks, loop))
finally:
    loop.close()
    for on_end in on_ends:
        try:
            on_end()
        except Exception as e:
            error(e)
    log("Closed.")
