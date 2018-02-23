# -*- coding:utf-8 -*-
import time

file = None
total_size = 0

def on_start(**kargs):
    global file
    savepath = kargs['savepath'] + '.flv'
    file = open(savepath, 'wb')


def on_chunk(chunk):
    global file, total_size
    file.write(chunk)
    total_size += len(chunk)
    

def on_end():
    global file, total_size
    file.close()

    print("downloaded %d" % total_size)
