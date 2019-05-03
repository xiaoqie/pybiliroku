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
    output = subprocess.check_output(cmd, universal_newlines=True)
    return output

def send_mail(title, content, attachment=""):
    fro = 'xiaoq@ponyfan.club'
    to = 'xiaoqie108@gmail.com'

    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = title
    msg.add_header("Message-ID", "<biliupload@ponyfan.club>")
    msg.add_header("In-Reply-To", "<biliupload@ponyfan.club>")
    msg.add_header("References", "<biliupload@ponyfan.club>")
    msg.attach(MIMEText(content, "html"))

    if attachment:
        part = MIMEApplication("stdout & stderr:\n" + attachment, Name="output.txt")
        part['Content-Disposition'] = 'attachment; filename="output.txt"'
        msg.attach(part)

    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(fro, to, msg.as_string())
    smtp.close()

def run_task(script):
    t0 = time.time()

    datetime_before = execute_and_check_output(['date'])
    disk_space_before = execute_and_check_output(['df', '-h', '--type', 'ext4'])
    tree_output_before = execute_and_check_output(['tree', "--noreport", "-h", '.'])
    encode_output = execute_and_check_output([sys.executable, script])
    tree_output_after = execute_and_check_output(['tree', '.'])
    os.system('rm -rf trash')
    disk_space_after = execute_and_check_output(['df', '-h', '--type', 'ext4'])
    datetime_after = execute_and_check_output(['date'])

    task_duration = time.time() - t0

    email_content = f"""
<html>
<body>
<pre style="font: monospace">
{script} has completed.
start time: {datetime_before}
end time:   {datetime_after}
duration:   {task_duration} seconds
---------------------------------------------------
Disk space before:
{disk_space_before}
Disk space after:
{disk_space_after}
---------------------------------------------------
Directory content before:
{tree_output_before}
Directory content after:
{tree_output_after}
</pre>
</body>
</html>
    """

    print(task_duration)
    if task_duration > 20 or always_send_mail:
        send_mail("Biliupload Notification", email_content, encode_output)


while True:
    if is_roku_free():
        print("pybiliroku is free now, starting task")
        try:
            run_task("to_mp4.py")
            run_task("encode.py")
            run_task("upload.py")
        except Exception as e:
            send_mail('An error has occured', str(e) + '\nIf it happens repeatly, maybe cookies have expired.')
    else:
        print("pybiliroku is busy now")
    time.sleep(3600)

