# -*- coding:utf-8 -*-
import time
import urllib
import sys


segment_time = 1790

start_timestamp = 0
enabled = False

def on_start(**kargs):
    global start_timestamp
    start_timestamp = time.time()


def on_chunk(chunk):
    if time.time() - start_timestamp > segment_time:
        sys.exit()


def on_end():
    pass
