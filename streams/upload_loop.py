import time
import os
import sys
import traceback


def execute_and_check_output(cmd):
    print(f"Starting {' '.join(cmd)}")
    ret_code = os.system(' '.join(cmd))
    if ret_code != 0:
        raise Exception(f"{cmd} returns non-zero status {ret_code}.")


def run_task(script, room_id):
    execute_and_check_output([sys.executable, script, f"{room_id}"])


while True:
    try:
        run_task("upload.py", 297)
        run_task("upload.py", 8054378)
    except Exception as e:
        print(traceback.format_exc())
        #send_mail('An error has occured', f"<pre>{str(e)}\n{traceback.format_exc()}\nIf it happens repeatly, maybe cookies have expired.</pre>")
    time.sleep(100)

