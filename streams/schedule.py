import urllib
import urllib.request
import json
import time
import subprocess
import os
import sys

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate

always_send_mail = False

def get_logging_time():
    try:
        with urllib.request.urlopen("http://127.0.0.1:2004/status", timeout=5) as conn:
            content = conn.read().decode("utf-8")
            result = json.loads(content)
            return result['297']['time']
    except Exception as e:
        return 0

def is_roku_free():
    return time.time() - get_logging_time() > 3*3600

def execute_and_check_output(cmd):
    print(f"Starting {' '.join(cmd)}")
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    return output

def send_mail(title, content, attachment=""):
    fro = 'xiaoq@ponyfan.club'
    to = 'xiaoqie108@gmail.com'

    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = title
    msg.attach(MIMEText(content))

    part = MIMEApplication("stdout & stderr:\n" + attachment, Name="output.txt")
    part['Content-Disposition'] = 'attachment; filename="output.txt"'
    msg.attach(part)

    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(fro, to, msg.as_string())
    smtp.close()

def to_mp4():
    t0 = time.time()

    datetime_before = execute_and_check_output(['date'])
    disk_space_before = execute_and_check_output(['df', '-h'])
    tree_output_before = execute_and_check_output(['tree', '.'])
    encode_output = execute_and_check_output(sys.executable + " to_mp4.py 2>&1 | rtail --no-parse-date --no-tty --id to_mp4")
    tree_output_after = execute_and_check_output(['tree', '.'])
    os.system('rm -rf trash')
    disk_space_after = execute_and_check_output(['df', '-h'])
    datetime_after = execute_and_check_output(['date'])

    task_duration = time.time() - t0

    email_content = f"""
Conversion has completed.
Task duration: {task_duration} seconds
---------------------------------------------
Task started at {datetime_before}

Disk space before the task started:
{disk_space_before}

Directory content before:
{tree_output_before}
---------------------------------------------
Task ended at {datetime_after}

Disk space after the task ended:
{disk_space_after}

Directory content after this:
{tree_output_after}

    """

    print(task_duration)
    if task_duration > 20 or always_send_mail:
        send_mail("conversion complete", email_content, encode_output)

def encode():
    t0 = time.time()

    datetime_before = execute_and_check_output(['date'])
    disk_space_before = execute_and_check_output(['df', '-h'])
    tree_output_before = execute_and_check_output(['tree', '.'])
    encode_output = execute_and_check_output(sys.executable + " encode.py 2>&1 | rtail --no-parse-date --no-tty --id encode")
    tree_output_after = execute_and_check_output(['tree', '.'])
    os.system('rm -rf trash')
    disk_space_after = execute_and_check_output(['df', '-h'])
    datetime_after = execute_and_check_output(['date'])

    task_duration = time.time() - t0

    email_content = f"""
Encoding has completed.
Task duration: {task_duration} seconds
---------------------------------------------
Task started at {datetime_before}

Disk space before the task started:
{disk_space_before}

Directory content before:
{tree_output_before}
---------------------------------------------
Task ended at {datetime_after}

Directory content after this:
{tree_output_after}

Disk space after the task ended:
{disk_space_after}

    """

    print(task_duration)
    if task_duration > 20 or always_send_mail:
        send_mail("encoding complete", email_content, encode_output)

def upload():
    t0 = time.time()

    datetime_before = execute_and_check_output(['date'])
    disk_space_before = execute_and_check_output(['df', '-h'])
    tree_output_before = execute_and_check_output(['tree', '.'])
    encode_output = execute_and_check_output(sys.executable + " upload.py 2>&1 | rtail --no-parse-date --no-tty --id upload")
    tree_output_after = execute_and_check_output(['tree', '.'])
    os.system('rm -rf trash')
    disk_space_after = execute_and_check_output(['df', '-h'])
    datetime_after = execute_and_check_output(['date'])

    task_duration = time.time() - t0

    email_content = f"""
Uploading has completed.
Task duration: {task_duration} seconds
---------------------------------------------
Task started at {datetime_before}

Disk space before the task started:
{disk_space_before}

Directory content before:
{tree_output_before}
---------------------------------------------
Task ended at {datetime_after}

Disk space after the task ended:
{disk_space_after}

Directory content after:
{tree_output_after}

    """

    print(task_duration)
    if "!!!ERROR!!!" in encode_output:
        raise Exception(encode_output)
    if task_duration > 20 or always_send_mail:
        send_mail("upload complete", email_content, encode_output)

while True:
    if is_roku_free():
        print("pybiliroku is free now, starting task")
        try:
            to_mp4()
            encode()
            upload()
        except Exception as e:
            send_mail('An error has occured', str(e) + '\nIf it happens repeatly, maybe cookies have expired.')
    else:
        print("pybiliroku is busy now")
    time.sleep(3600)

