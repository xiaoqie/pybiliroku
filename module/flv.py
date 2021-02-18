# -*- coding:utf-8 -*-
import time
import os
import contextlib

log = None
file = None
total_size = 0
savepath = None
savepath_ass = None

def on_start(**kargs):
    global file, savepath
    savepath = kargs['savepath'] + '.flv'
    savepath_ass = kargs['savepath'] + '.ass'
    file = open(savepath, 'wb')


def on_chunk(chunk):
    global file, total_size
    file.write(chunk)
    total_size += len(chunk)
    

def on_end():
    global file, total_size
    file.close()

    log.info("downloaded %d" % total_size)

    if total_size == 0:
        os.remove(savepath)
        log.info("removed empty %s" % savepath)
        os.remove(savepath_ass)
        log.info("removed empty %s" % savepath_ass)

