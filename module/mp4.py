# -*- coding:utf-8 -*-
"""import time
import subprocess

savepath = None


def on_start(**kargs):
    global savepath
    savepath = kargs['savepath']


def on_chunk(chunk):
    pass


def on_end():
    if savepath is not None:
        subprocess.Popen(["ffmpeg", "-i", "%s.flv" % savepath, "-vcodec", "copy", "-c:a", "aac", "-b:a", "128k", "%s.mp4" % savepath])
        print("Saving mp4.")
"""