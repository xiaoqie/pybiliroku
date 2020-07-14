# -*- coding:utf-8 -*-
import time
import urllib
import sys


request_args = {"--terminate": {
    'action': "store",
    'dest': "terminate",
    'type': int,
    'default': 0
}}

segment_time = 1800
start_timestamp = 0

def on_start(**kargs):
    global start_timestamp, segment_time
    start_timestamp = time.time()
    segment_time = kargs['args'].terminate


def on_chunk(chunk):
    if time.time() - start_timestamp > segment_time and segment_time > 0:
        sys.exit()


def on_end():
    pass
