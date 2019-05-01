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


def get_title_of(day):
    ls = os.listdir("297")
    videos = []
    for file in ls:
        name, ext = os.path.splitext(file)
        if ext == ".ass":
            videos.append(name)

    videos = sorted(videos)

    date2videos = defaultdict(lambda: [])
    date2users = defaultdict(lambda: [])
    for video in videos:
        datetime_string = '-'.join(video.split('-')[0:5])
        datetime_obj = datetime.datetime.strptime(datetime_string, '%Y-%m-%d_%H-%M-%S')
        date_str = str(datetime_obj - datetime.timedelta(hours=8)).split(' ')[0]
        title = video[len('0000-00-00_00-00-00-'):]
        closing_bracket = title.find('】')
        if closing_bracket != -1:
            user = title[1:closing_bracket]
            date2users[date_str] += [user]
            title = title[closing_bracket + 1:]
        else:
            date2users[date_str] = ['lolo']
        date2videos[date_str] += [title]

    return ('+'.join(list(set(date2videos[day]))), ','.join(list(set(date2users[day]))))


def get_available_days():
    return [file for file in os.listdir('297') if os.path.isdir(f'297/{file}')]


def get_uploaded_videos():
    driver.get("https://member.bilibili.com/v2#/upload-manager/article")

    if '创作中心' not in driver.title:
        driver.close()
        raise Exception('cookies may have expired')

    elements = driver.find_elements_by_css_selector(".ellipsis.name")
    titles = [element.get_attribute('innerHTML') for element in elements]
    return titles


def upload(day):
    # driver.get("https://member.bilibili.com/v2#/upload/video/frame")
    files = '\n'.join([os.path.abspath(f'297/{day}/{file}') for file in sorted(os.listdir(f'297/{day}'), key=lambda s: int(s[1:-4])) if file.endswith('.mp4')])
    driver.get("https://member.bilibili.com/video/upload.html")
    # input_tag = driver.find_element_by_css_selector('.webuploader-element-invisible')
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
            os.system(f"rm -rf 297/{day}")
            return  # success
        if time.time() - t0 > 3600:
            raise Exception("timeout")

        item_warps = driver.find_elements_by_css_selector('.file-list-v2-item-wrp')
        for item_warp in item_warps:
            title = item_warp.find_elements_by_css_selector('.item-title')
            # intro = item_warp.find_elements_by_css_selector('.upload-status-intro')
            # speed = item_warp.find_elements_by_css_selector('.upload-speed')
            # remain_time = item_warp.find_elements_by_css_selector('.remain-time')
            # print(' '.join([elem.get_attribute('innerHTML') for elem in title + intro]))
            print(title[0].get_attribute('innerHTML'), item_warp.find_elements_by_css_selector('.item-upload-info')[0].text)
        print("----------------------------------------")

        time.sleep(1)


driver = None
try:
    if not get_available_days():
        sys.exit()

    chromeOptions = Options()
    chromeOptions.set_headless(True)

    driver = webdriver.Chrome(chrome_options=chromeOptions)
    driver.implicitly_wait(50)
    driver.get("https://www.bilibili.com/")
    with open('cookies.pickle', 'rb') as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)

    uploaded_titles = get_uploaded_videos()
    #print(uploaded_titles)
    uploaded_days = [title[-len('2018-08-14'):] for title in uploaded_titles]
    uploaded_datetimes = [datetime.datetime.strptime(datetime_string, '%Y-%m-%d') for datetime_string in uploaded_days]
    last_uploaded_datetime = sorted(uploaded_datetimes)[-1]

    available_days = get_available_days()
    available_datetimes = [datetime.datetime.strptime(datetime_string, '%Y-%m-%d') for datetime_string in available_days]
    unuploaded_datetimes = [dt for dt in available_datetimes if dt > last_uploaded_datetime]

    for deletable_days in list(set(available_days) & set(uploaded_days)):
        os.makedirs('trash', exist_ok=True)
        cmd = f'mv 297/{deletable_days}/ trash/'
        print(cmd)
        os.system(cmd)

    if unuploaded_datetimes:
    # if True:
        upload_target = sorted(unuploaded_datetimes)[0].strftime('%Y-%m-%d')
        print('uploading', upload_target)
        upload(upload_target)
except Exception as e:
    print("!!!ERROR!!!")
    traceback.print_exc(file=sys.stdout)
finally:
    if driver:
        driver.quit()
