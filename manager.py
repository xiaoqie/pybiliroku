"""
/report?room_id=XXX&downloaded_size=XXX
/status
/open?room_id=XXX
/close?room_id=XXX
/processes
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib
import time
import json
import subprocess
import os
import signal
import psutil
import urllib.parse
import subprocess


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
kill = kill_proc_tree


def open_room(room_id):
    if room_id not in MyHandler.processes:
        MyHandler.processes[room_id] = subprocess.Popen(
            "python roku_loop.py --room-id %s --savepath %s" % (room_id, get_config()['savepath']))
        return True
    else:
        return False

def close(room_id):
    if room_id in MyHandler.processes:
        process = MyHandler.processes.pop(room_id)
        kill(process.pid)
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



class MyHandler(SimpleHTTPRequestHandler):
    status = {}
    processes = {}

    def process_processes(self):
        """
        remove inactive processes
        """
        for k, v in MyHandler.processes.items():  # remove inactive processes
            if not psutil.pid_exists(v.pid):
                MyHandler.processes.pop(k)

    def report(self, room_id, downloaded_size, start_timestamp):
        MyHandler.status[room_id] = {'downloaded_size': downloaded_size, "time": time.time(), "start_timestamp": start_timestamp}
        return True

    def do_GET(self):
        self.process_processes()

        parsed_url = urllib.parse.urlparse(self.path)
        parsed_qs = urllib.parse.parse_qs(parsed_url.query)
        path = parsed_url.path

        if path in ["/report", "/status", "/open", "/close", "/processes", "/get_config", "/save_config"]:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        if path == "/report":
            if not ("room_id" in parsed_qs and "downloaded_size" in parsed_qs and "start_timestamp" in parsed_qs):
                self.wfile.write("fail".encode())
                return
            room_id = parsed_qs["room_id"][0]
            downloaded_size = parsed_qs["downloaded_size"][0]
            start_timestamp = parsed_qs["start_timestamp"][0]
            self.report(room_id, downloaded_size, start_timestamp)
            self.wfile.write("success".encode())
            return
        if path == "/status":
            # MyHandler.status = {k: v for k, v in MyHandler.status.items() if time.time() - v['time'] < 10}
            self.wfile.write(json.dumps(MyHandler.status).encode())
            return
        if path == "/open":
            room_id = parsed_qs["room_id"][0]
            if open_room(room_id):
                self.wfile.write("success".encode())
            else:
                self.wfile.write("duplicate".encode())
            return
        if path == "/close":
            room_id = parsed_qs["room_id"][0]
            if close(room_id):
                self.wfile.write("success".encode())
            else:
                self.wfile.write("no such process".encode())
            return
        if path == "/processes":
            self.wfile.write(json.dumps(list(MyHandler.processes.keys())).encode())
            return
        if path == "/get_config":
            self.wfile.write(json.dumps(get_config()).encode())
            return
        if path == "/save_config":
            if "json" not in parsed_qs:
                self.wfile.write("no argument".encode())
                return
            json_content = urllib.parse.unquote_plus(parsed_qs["json"][0])
            try:
                json_obj = json.loads(json_content)
            except Exception as e:
                self.wfile.write("invalid json".encode())
            save_config(json_obj)
            self.wfile.write("success".encode())
            return

        super(MyHandler, self).do_GET()

    def do_HEAD(self):
        super(MyHandler, self).do_HEAD()


def run(server_class=HTTPServer, handler_class=MyHandler, port=80):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')

    load_on_init = get_config()["load_on_init"]
    print("Opening initialization tasks.")
    for room_id in load_on_init:
        if open_room(str(room_id)):
            print("Opened room_id %d during initialization." % room_id)
        else:
            print("Failed to open room_id %d during initialization." % room_id)

    httpd.serve_forever()

run(port=2004)
