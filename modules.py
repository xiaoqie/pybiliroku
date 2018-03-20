import os
from _logging import verbose, error, log

__all__ = ['on_start', 'on_chunk', 'on_danmaku', 'on_end', 'request_args']

on_starts = []
on_ends = []
ended = False
on_danmakus = []
on_chunks = []
request_args = {}
verbose("Loading modules.")
for module_file in os.listdir("module"):
    filename, ext = os.path.splitext(module_file)
    if filename == "__init__" or ext != ".py":
        continue
    module = __import__("module.%s" % filename)
    try:
        enabled = getattr(module, filename).enabled
        verbose("%s.enabled = %s" %
                (os.path.splitext(module_file)[0], enabled))
        if not enabled:
            continue
    except AttributeError:
        pass
    try:
        req_args = getattr(module, filename).request_args
        verbose("%s request the following args: %s" % (os.path.splitext(module_file)[0], req_args))
        request_args.update(req_args)
    except AttributeError:
        pass
    try:
        on_starts.append(getattr(module, filename).on_start)
        verbose("loaded %s.on_start" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_ends.append(getattr(module, filename).on_end)
        verbose("loaded %s.on_end" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_danmakus.append(getattr(module, filename).on_danmaku)
        verbose("loaded %s.on_danmaku" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
    try:
        on_chunks.append(getattr(module, filename).on_chunk)
        verbose("loaded %s.on_chunk" % os.path.splitext(module_file)[0])
    except AttributeError:
        pass
verbose("Complete loading modules.")


def on_start(**kwargs):
    for on_start in on_starts:
        try:
            on_start(**kwargs)
        except Exception as e:
            error(e)


def on_chunk(chunk):
    for on_chunk in on_chunks:
        try:
            on_chunk(chunk)
        except Exception as e:
            error(e)


def on_danmaku(danmaku):
    for on_danmaku in on_danmakus:
        try:
            on_danmaku(danmaku)
        except Exception as e:
            error(e)


def on_end():
    global ended
    if not ended:
        ended = True
        for on_end in on_ends:
            try:
                on_end()
            except Exception as e:
                error(e)
