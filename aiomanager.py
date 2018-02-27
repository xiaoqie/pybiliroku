from aiohttp import web
import json
import signal
import psutil
import subprocess
import os
import time
import urllib.parse


def IndexMiddleware(index='index.html'):
    """Middleware to serve index files (e.g. index.html) when static directories are requested.

    Usage:
    ::

        from aiohttp import web
        from aiohttp_index import IndexMiddleware
        app = web.Application(middlewares=[IndexMiddleware()])
        app.router.add_static('/', 'static')

    ``app`` will now serve ``static/index.html`` when ``/`` is requested.

    :param str index: The name of a directory's index file.
    :returns: The middleware factory.
    :rtype: function

    Borrowed from: http://pythonhosted.org/aiohttp-index/_modules/aiohttp_index/index.html#IndexMiddleware
    License?
    """
    async def middleware_factory(app, handler):
        """Middleware factory method.

        :type app: aiohttp.web.Application
        :type handler: function
        :returns: The retry handler.
        :rtype: function
        """
        async def index_handler(request):
            """Handler to serve index files (index.html) for static directories.

            :type request: aiohttp.web.Request
            :returns: The result of the next handler in the chain.
            :rtype: aiohttp.web.Response
            """
            try:
                filename = request.match_info['filename']
                if not filename:
                    filename = index
                if filename.endswith('/'):
                    filename += index
                request.match_info['filename'] = filename
            except KeyError:
                pass
            return await handler(request)
        return index_handler
    return middleware_factory


def kill_proc_tree(pid, sig=signal.SIGTERM, include_parent=True,
                   timeout=3, on_terminate=None):
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callabck function which is
    called as soon as a child terminates.
    """
    if pid == os.getpid():
        raise RuntimeError("I refuse to kill myself")
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        p.send_signal(sig)
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    return (gone, alive)


status = {}
processes = {}
port = 2004


def report(room_id, downloaded_size, start_timestamp):
    status[room_id] = {'downloaded_size': downloaded_size,
                       "time": time.time(), "start_timestamp": start_timestamp}
    return True


def open_room(room_id):
    if room_id not in processes:
        processes[room_id] = subprocess.Popen([
            "python", "roku_loop.py",
            "--room-id", str(room_id),
            "--savepath", get_config()['savepath'],
            "--port", str(port)
        ])
        return True
    else:
        return False


def close_room(room_id):
    if room_id in processes:
        process = processes.pop(room_id)
        gone, alive = kill_proc_tree(process.pid)
        return True
    else:
        return False


def get_config():
    if os.path.exists("config.json"):
        json_file = open("config.json").read()
    else:
        json_file = "{}"
    json_obj = json.loads(json_file)
    if "savepath" not in json_obj:
        json_obj['savepath'] = "streams/{room_id}/{start_time}-{title}"
    if "load_on_init" not in json_obj:
        json_obj['load_on_init'] = []
    return json_obj


def save_config(json_obj):
    if "savepath" not in json_obj:
        json_obj['savepath'] = "streams/{room_id}/{start_time}-{title}"
    if "load_on_init" not in json_obj:
        json_obj['load_on_init'] = []
    with open("config.json", "w") as config_file:
        config_file.write(json.dumps(json_obj, indent=4))


async def do_report(request):
    if not ("room_id" in request.query and
            "downloaded_size" in request.query and
            "start_timestamp" in request.query):
        return web.Response(text='fail')
    report(request.query["room_id"], request.query["downloaded_size"],
           request.query["start_timestamp"])
    return web.Response(text='success')


async def do_status(request):
    return web.Response(text=json.dumps(status))


async def do_open(request):
    room_id = request.query["room_id"]
    if open_room(room_id):
        return web.Response(text='success')
    else:
        return web.Response(text='duplicate')


async def do_close(request):
    room_id = request.query["room_id"]
    if close_room(room_id):
        return web.Response(text='success')
    else:
        return web.Response(text='no such process')


async def do_processes(request):
    return web.Response(text=json.dumps(list(processes.keys())))


async def do_get_config(request):
    return web.Response(text=json.dumps(get_config()))


async def do_save_config(request):
    if "json" not in request.query:
        return web.Response(text="no argument")
    json_content = urllib.parse.unquote_plus(request.query["json"])
    try:
        json_obj = json.loads(json_content)
    except Exception as e:
        return web.Response(text="invalid json")
    save_config(json_obj)
    return web.Response(text="success")


app = web.Application(middlewares=[IndexMiddleware()])
app.router.add_get('/report', do_report)
app.router.add_get("/status", do_status)
app.router.add_get("/open", do_open)
app.router.add_get("/close", do_close)
app.router.add_get("/processes", do_processes)
app.router.add_get("/get_config", do_get_config)
app.router.add_get("/save_config", do_save_config)
app.router.add_static('/', path='.')

load_on_init = get_config()["load_on_init"]
print("Opening initialization tasks.")
for room_id in load_on_init:
    if open_room(str(room_id)):
        print("Opened room_id %d during initialization." % room_id)
    else:
        print("Failed to open room_id %d during initialization." % room_id)

web.run_app(app, host='0.0.0.0', port=port)
