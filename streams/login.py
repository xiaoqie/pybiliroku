import time
import os
import sys
import pickle
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chromeOptions = Options()
chromeOptions.add_experimental_option('w3c', False)

driver = webdriver.Chrome(chrome_options=chromeOptions)
driver.implicitly_wait(50)
driver.get("https://passport.bilibili.com/login/")
