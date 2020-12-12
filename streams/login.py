import json
from bilibiliuploader import BilibiliUploader

config = json.load(open("config.json"))
uploader = BilibiliUploader()
uploader.login(config['bilibili_username'], config['bilibili_password'])
uploader.save_login_data(file_name="bilibili_token.json")
print("success")

