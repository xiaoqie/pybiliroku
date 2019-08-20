import os
import argparse
from logger import Logger

__all__ = ['on_start', 'on_chunk', 'on_danmaku', 'on_end', 'request_args']

parser = argparse.ArgumentParser()
parser.add_argument("--room-id", action="store", dest="room_id", type=int, required=True)
args, _ = parser.parse_known_args()
log = Logger(f"{args.room_id} module loader")

on_starts = []
on_ends = []
ended = False
on_danmakus = []
on_chunks = []
request_args = {}
log.verbose("Loading modules.")
for module_file in os.listdir("module"):
    filename, ext = os.path.splitext(module_file)
    if filename == "__init__" or ext != ".py":
        continue
    module = __import__("module.%s" % filename)
    try:
        enabled = getattr(module, filename).enabled
        log.verbose("%s.enabled = %s" %
                (os.path.splitext(module_file)[0], enabled))
        if not enabled:
            continue
    except AttributeError:
        pass
    try:
        getattr(module, filename).log = Logger(f"{args.room_id} {filename} module")
        log.verbose(f"injected log dependency to {filename} module")
    except AttributeError:
        pass
    try:
        req_args = getattr(module, filename).request_args
        log.verbose("%s request the following args: %s" % (os.path.splitext(module_file)[0], req_args))
        request_args.update(req_args)
    except AttributeError:
        pass
    try:
        on_starts.append(getattr(module, filename).on_start)
        log.verbose("loaded %s.on_start" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_ends.append(getattr(module, filename).on_end)
        log.verbose("loaded %s.on_end" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_danmakus.append(getattr(module, filename).on_danmaku)
        log.verbose("loaded %s.on_danmaku" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_chunks.append(getattr(module, filename).on_chunk)
        log.verbose("loaded %s.on_chunk" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
log.verbose("Complete loading modules.")


def on_start(**kwargs):
    for on_start in on_starts:
        try:
            on_start(**kwargs)
        except Exception as e:
            log.error(e)


def on_chunk(chunk):
    for on_chunk in on_chunks:
        try:
            on_chunk(chunk)
        except Exception as e:
            log.error(e)


def on_danmaku(danmaku):
    for on_danmaku in on_danmakus:
        try:
            on_danmaku(danmaku)
        except Exception as e:
            log.error(e)


def on_end():
    global ended
    if not ended:
        ended = True
        for on_end in on_ends:
            try:
                on_end()
            except Exception as e:
                log.error(e)
