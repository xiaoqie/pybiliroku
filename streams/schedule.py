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
    tree_output_after = execute_and_check_output(['tree', "--noreport", "-h", '.'])
    os.system('rm -rf trash')
    disk_space_after = execute_and_check_output(['df', '-h', '--type', 'ext4'])
    datetime_after = execute_and_check_output(['date'])

    task_duration = time.time() - t0

    email_content = f"""
<html>
<head>
    <style type="text/css">
        /* vietnamese */
        @font-face {{
            font-family: 'Inconsolata';
            font-style: normal;
            font-weight: 400;
            src: local('Inconsolata Regular'), local('Inconsolata-Regular'), url(https://fonts.gstatic.com/s/inconsolata/v17/QldKNThLqRwH-OJ1UHjlKGlW5qhWxg.woff2) format('woff2');
            unicode-range: U+0102-0103, U+0110-0111, U+1EA0-1EF9, U+20AB;
        }}
        /* latin-ext */
        @font-face {{
            font-family: 'Inconsolata';
            font-style: normal;
            font-weight: 400;
            src: local('Inconsolata Regular'), local('Inconsolata-Regular'), url(https://fonts.gstatic.com/s/inconsolata/v17/QldKNThLqRwH-OJ1UHjlKGlX5qhWxg.woff2) format('woff2');
            unicode-range: U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF;
        }}
        /* latin */
        @font-face {{
            font-family: 'Inconsolata';
            font-style: normal;
            font-weight: 400;
            src: local('Inconsolata Regular'), local('Inconsolata-Regular'), url(https://fonts.gstatic.com/s/inconsolata/v17/QldKNThLqRwH-OJ1UHjlKGlZ5qg.woff2) format('woff2');
            unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
        }}
        body {{
            font-family: 'Inconsolata', monospace;
        }}
    </style>
</head>
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

