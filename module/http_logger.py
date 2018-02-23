# -*- coding:utf-8 -*-
import time
import urllib

room_id = None
total_size = 0
start_timestamp = 0


def on_start(**kargs):
    global room_id, start_timestamp
    room_id = kargs['original_room_id']
    start_timestamp = time.time()


def on_chunk(chunk):
    global total_size
    total_size += len(chunk)
    with urllib.request.urlopen("http://127.0.0.1:2004/report?room_id=%d&downloaded_size=%d&start_timestamp=%d" % (room_id, total_size, start_timestamp)) as conn:
        content = conn.read().decode("utf-8")
        if content != "success":
            raise RuntimeError("Cannot report to logger")


def on_end():
    pass
