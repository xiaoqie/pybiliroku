from aiohttp import web
import json
import signal
import psutil
import subprocess
import os
import time
import urllib.parse
import urllib.request
import re
import sys
import shutil


def IndexMiddleware(index='index.html'):
    async def middleware_factory(app, handler):
        async def index_handler(request):
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
terminate = 1800


def report(room_id, downloaded_size, start_timestamp):
    if room_id in status:
        last_download_size = status[room_id]['downloaded_size']
        last_time = status[room_id]['time']
    else:
        last_download_size = 0
        last_time = 0
    status[room_id] = {'downloaded_size': downloaded_size,
                       "time": time.time(), 
                       "start_timestamp": start_timestamp,
                       "download_speed": 1 if int(downloaded_size) > int(last_download_size) else 0}
    return True


def open_room(room_id):
    if room_id not in processes:
        processes[room_id] = subprocess.Popen([
            sys.executable, "roku_loop.py",
            "--room-id", str(room_id),
            "--savepath", get_config()['savepath'],
            "--port", str(port),
            "--terminate", str(terminate)
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
        json_obj['savepath'] = "streams/{original_room_id}/{start_time}-{title}"
    if "load_on_init" not in json_obj:
        json_obj['load_on_init'] = []
    return json_obj


def save_config(json_obj):
    if "savepath" not in json_obj:
        json_obj['savepath'] = "streams/{original_room_id}/{start_time}-{title}"
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
    for room_id, value in status.items():
        if time.time() - value['time'] > 1:
            value['download_speed'] = 0
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


async def do_info(request):
    for room_id, value in status.items():
        if time.time() - value['time'] > 1:
            value['download_speed'] = 0
    return web.Response(text=json.dumps({"time": time.time(), "processes": list(processes.keys()), "status": status}))


async def do_get_config(request):
    return web.Response(text=json.dumps(get_config()))


async def do_get_disk_usage(request):
    total, used, free = shutil.disk_usage("/")
    return web.Response(text=json.dumps({"total": total, "used": used}))


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


user_info_cache = {}
async def do_get_user_info(request):
    original_room_id = request.query["room_id"]
    if original_room_id in user_info_cache:
        return web.Response(text=user_info_cache[original_room_id])

    with urllib.request.urlopen("https://api.live.bilibili.com/room/v1/Room/room_init?id=%s" % original_room_id, timeout=5) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        if result['msg'] != 'ok':
            raise ValueError("Error while requesting room ID:%s" % result['msg'])
        room_id = result['data']['room_id']
    with urllib.request.urlopen("https://api.live.bilibili.com/room/v1/Room/get_info?room_id=%s&from=room" % room_id, timeout=5) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        if result['msg'] != 'ok':
            raise ValueError("Error while requesting room ID:%s" % result['msg'])
        data1 = result['data']
        
    with urllib.request.urlopen("https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room?roomid=%s" % room_id, timeout=5) as conn:
        content = conn.read().decode("utf-8")
        result = json.loads(content)
        if result['msg'] != 'success':
            raise ValueError("Error while requesting room ID:%s" % result['msg'])
        data2 = dict(data1)
        data2.update(result['data'])
    
    user_info_cache[original_room_id] = json.dumps(data2)
    return web.Response(text=user_info_cache[original_room_id])


app = web.Application(middlewares=[IndexMiddleware()])
app.router.add_get('/report', do_report)
app.router.add_get("/status", do_status)
app.router.add_get("/open", do_open)
app.router.add_get("/close", do_close)
app.router.add_get("/processes", do_processes)
app.router.add_get("/info", do_info)
app.router.add_get("/get_config", do_get_config)
app.router.add_get("/save_config", do_save_config)
app.router.add_get("/get_user_info", do_get_user_info)
app.router.add_get("/get_disk_usage", do_get_disk_usage)
app.router.add_static('/', path='static')

load_on_init = get_config()["load_on_init"]
print("Opening initialization tasks.")
for room_id in load_on_init:
    if open_room(str(room_id)):
        print("Opened room_id %d during initialization." % room_id)
    else:
        print("Failed to open room_id %d during initialization." % room_id)

web.run_app(app, host='0.0.0.0', port=port)
