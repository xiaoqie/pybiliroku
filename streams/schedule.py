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
    try:
        output = subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise Exception(f"{' '.join(cmd)} returned non-zero status, output:\n {e.output}")
    return str(output).strip()

def send_mail(title, content, attachment=""):
    config = json.load(open("config.json"))

    msg = MIMEMultipart()
    msg['From'] = config['email_address']
    msg['To'] = 'xiaoqie108@gmail.com'
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = title
    msg.add_header("In-Reply-To", "<biliupload@ponyfan.club>")
    msg.add_header("References", "<biliupload@ponyfan.club>")
    msg.attach(MIMEText(content, "html"))

    if attachment:
        part = MIMEText("stdout & stderr:\n" + attachment)
        part['Content-Disposition'] = 'attachment; filename="output.txt"'
        msg.attach(part)

    smtp = smtplib.SMTP(config['smtp_server'])
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(msg['From'], config['email_password'])
    smtp.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp.close()

def run_task(script):
    t0 = time.time()

    datetime_before = execute_and_check_output(['date'])
    disk_space_before = execute_and_check_output(['df', '-h', '--type', 'ext4'])
    tree_output_before = execute_and_check_output(['tree', '-N', "--noreport", "-h", '.'])
    encode_output = execute_and_check_output([sys.executable, script])
    tree_output_after = execute_and_check_output(['tree', '-N', "--noreport", "-h", '.'])
    disk_space_after = execute_and_check_output(['df', '-h', '--type', 'ext4'])
    datetime_after = execute_and_check_output(['date'])

    task_duration = time.time() - t0

    email_content = f"""
<html>
<body>
<pre>
{script} has completed.
start time: {datetime_before}
end time:   {datetime_after}
duration:   {task_duration} seconds
---------------------------------------------------
Disk space before:
{disk_space_before}
Disk space after:
{disk_space_after}
</pre>
</body>
</html>
    """

    print(task_duration)
    if task_duration > 20 or always_send_mail:
        send_mail("Biliupload Notification", email_content, encode_output)


while True:
    try:
        #run_task("to_mp4.py")
        run_task("encode.py")
        #run_task("upload.py")
        #os.system("rm -rf trash")
    except Exception as e:
        send_mail('An error has occured', f"<pre>{str(e)}\nIf it happens repeatly, maybe cookies have expired.</pre>")
    time.sleep(10)

