import time
import os
import sys
import pickle
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = None
try:
    chromeOptions = Options()
    chromeOptions.add_experimental_option('w3c', False)

    driver = webdriver.Chrome(chrome_options=chromeOptions)
    driver.implicitly_wait(50)
    driver.get("https://passport.bilibili.com/login")

    element = WebDriverWait(driver, 300).until(EC.title_contains("干杯"))
    pickle.dump(driver.get_cookies(), open("cookies.pickle","wb"))
finally:
    driver.quit()

