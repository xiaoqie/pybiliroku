# -*- coding:utf-8 -*-
import time
import urllib

request_args = {"--port": {
    'action': "store",
    'dest': "port",
    'type': int
}}
port = None

room_id = None
total_size = 0
start_timestamp = 0

has_exception = False


def on_start(**kargs):
    global room_id, start_timestamp, port, has_exception
    room_id = kargs['original_room_id']
    start_timestamp = time.time()
    port = kargs['args'].port

    if port is None:
        has_exception = True
        raise RuntimeError("http_logger: No port specified.")


def on_chunk(chunk):
    global total_size, has_exception
    if has_exception:
        return

    total_size += len(chunk)
    try:
        with urllib.request.urlopen("http://127.0.0.1:2004/report?room_id=%d&downloaded_size=%d&start_timestamp=%d" % (room_id, total_size, start_timestamp)) as conn:
            content = conn.read().decode("utf-8")
            if content != "success":
                has_exception = True
                raise RuntimeError("Failed to log: returned %s" % content)
    except Exception as e:
        has_exception = True
        raise RuntimeError("Failed to log: %s" % e)


def on_end():
    pass
