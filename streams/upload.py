import datetime
import time
import os
import sys
import pickle
import time
import traceback
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import *


def get_title_of(day):
    videos = get_videos()
    date = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    video_list = videos[date]
    return (' + '.join(list(dict.fromkeys([v.title for v in video_list]))),
            ''.join(list(dict.fromkeys([v.streamer for v in video_list]))))

def get_available_days():
    return [file for file in os.listdir('297') if os.path.isdir(f'297/{file}')]


def get_uploaded_videos():
    driver.get("https://member.bilibili.com/v2#/upload-manager/article")

    print(driver.current_url);
    print(driver.title);
    if '创作中心' not in driver.title:
        driver.close()
        raise Exception('cookies may have expired')

    elements = driver.find_elements_by_css_selector(".ellipsis.name")
    titles = [element.get_attribute('innerHTML') for element in elements]
    return titles


def upload(day):
    files = '\n'.join([os.path.abspath(f'297/{day}/{file}') for file in sorted(os.listdir(f'297/{day}'), key=lambda s: int(s.split("_")[0][1:])) if file.endswith('.mp4')])
    driver.get("https://member.bilibili.com/video/upload.html")
    input_tag = driver.find_element_by_name('buploader')
    input_tag.send_keys(files)

    time.sleep(1)
    driver.find_element_by_css_selector('.template-op p').click()
    time.sleep(1)
    driver.find_element_by_css_selector('.template-list-small-item').click()
    time.sleep(1)
    (title, user) = get_title_of(day)
    driver.find_element_by_css_selector('.input-box-v2-1-val').send_keys(f'【{user}直播录像】{title} {day}')
    time.sleep(1)
    driver.find_element_by_css_selector('.text-area-box-v2-val').send_keys('由lolo授权录播组录制并上传。')
    time.sleep(1)
    driver.find_element_by_css_selector('.submit-btn-group-add').click()

    t0 = time.time()
    while True:
        if driver.find_element_by_css_selector('.upload-3-v2-success-hint-1').is_displayed():
            return  # success

        if time.time() - t0 > 7200:
            raise Exception("timeout")

        item_warps = driver.find_elements_by_css_selector('.file-list-v2-item-wrp')
        for item_warp in item_warps:
            title = item_warp.find_elements_by_css_selector('.item-title')
            print(title[0].get_attribute('innerHTML'), item_warp.find_elements_by_css_selector('.item-upload-info')[0].text)
        print("----------------------------------------")

        time.sleep(1)


driver = None
try:
    if not get_available_days():
        sys.exit()

    chromeOptions = Options()
    chromeOptions.set_headless(True)
    chromeOptions.add_experimental_option('w3c', False)

    driver = webdriver.Chrome(chrome_options=chromeOptions)
    driver.implicitly_wait(50)
    driver.get("https://www.bilibili.com/")
    with open('cookies.pickle', 'rb') as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        del cookie['expiry']
        driver.add_cookie(cookie)

    uploaded_titles = get_uploaded_videos()
    uploaded_days = [title[-len('2018-08-14'):] for title in uploaded_titles]
    uploaded_datetimes = [datetime.datetime.strptime(datetime_string, '%Y-%m-%d') for datetime_string in uploaded_days]
    last_uploaded_datetime = sorted(uploaded_datetimes)[-1]

    available_days = get_available_days()
    available_datetimes = [datetime.datetime.strptime(datetime_string, '%Y-%m-%d') for datetime_string in available_days]
    unuploaded_datetimes = [dt for dt in available_datetimes if dt > last_uploaded_datetime]

    for deletable_days in list(set(available_days) & set(uploaded_days)):
        move_to_trash(f"297/{deletable_days}")

    if unuploaded_datetimes:
    # if True:
        pickle.dump(driver.get_cookies(), open("cookies.pickle","wb"))
        upload_target = sorted(unuploaded_datetimes)[0].strftime('%Y-%m-%d')
        print('uploading', upload_target)
        upload(upload_target)
finally:
    if driver:
        driver.quit()
