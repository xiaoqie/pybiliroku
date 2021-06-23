import sys
import time
import subprocess

while True:
    cmd = [sys.executable, "roku.py"] + sys.argv[1:]
    print("$ %s" % ' '.join(cmd))
    ret = subprocess.Popen(cmd).wait()
    if ret == 61:
        time.sleep(30)

