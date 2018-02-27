import os
import sys
import time
import subprocess
import atexit
import signal
import argparse

while True:
    subprocess.Popen(["python", "roku.py"] + sys.argv[1:]).wait()
    print("Restarting.")
