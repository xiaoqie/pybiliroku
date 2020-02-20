import urllib
import urllib.request
import json
import time
import subprocess
import os
import sys
import traceback

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
    ret_code = os.system(' '.join(cmd))
    if ret_code != 0:
        raise Exception(f"{cmd} returns non-zero status {ret_code}.")


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
    execute_and_check_output([sys.executable, script])


while True:
    try:
        #run_task("to_mp4.py")
        run_task("encode.py")
        run_task("upload.py")
        #os.system("rm -rf trash")
    except Exception as e:
        send_mail('An error has occured', f"<pre>{str(e)}\n{traceback.format_exc()}\nIf it happens repeatly, maybe cookies have expired.</pre>")
    time.sleep(100)

