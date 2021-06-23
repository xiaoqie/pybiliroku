import json
from bilibiliuploader import BilibiliUploader

config = json.load(open("config.json"))["297"]
uploader = BilibiliUploader()
uploader.login_by_access_token_file("bilibili_token.json")
print(uploader.expires_in)
#token = json.load(open("bilibili_token.json"))
#uploader.access_token = token["access_token"]
#uploader.refresh_token = token["refresh_token"]
#uploader.do_token_refresh()
#uploader.login(config['bilibili_username'], config['bilibili_password'])
#uploader.save_login_data(file_name="bilibili_token.json")
print("success")

