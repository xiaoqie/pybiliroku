import os
import sys
import time
import subprocess
import atexit
import signal
import argparse

while True:
    cmd = [sys.executable, "roku.py"] + sys.argv[1:]
    subprocess.Popen(cmd).wait()
    print("Restarting %s" % ' '.join(cmd))
