# coding:utf-8
#selenium模拟登录知乎 保存cookie到本地 验证码识别
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions as ex
from selenium.webdriver import ActionChains

import requests
import time
import pickle
import os,base64
import re

# os.popen('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenum\AutomationProfile"')

class Zhihu:
    def __init__(self,home_url):
        self.home_url = home_url
        self.header = {
            'User-Agent': 'user-agentMozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }

	#保存session，下次可直接使用，避免再次登录
    def save_session(self,session):
        with open('zhihu_session.txt','wb') as f:
            pickle.dump(session, f)
            print("Cookies have been writed.")

	#加载session
    def load_session(self):
        with open('zhihu_session.txt', 'rb') as f:
            s = pickle.load(f)
        return s

	#判断是否登录
    def is_login(self,browser):
        try:
            return bool(
                browser.find_element_by_css_selector(".GlobalSideBar-navText")
            )
        except ex.NoSuchElementException:
            return False

	#判断是否有验证码 并返回验证码类型
    def is_captch(self,browser):
        ca_type = {}
        result = browser.find_element_by_css_selector(".SignFlow-captchaContainer img").get_attribute("src")
        if result != 'data:image/jpg;base64,null':
            type = browser.find_element_by_css_selector(".SignFlow-captchaContainer img").get_attribute("class")
            ca_type['url'] = result
            if type =='Captcha-chineseImg':
                ca_type['type'] = 'chinese' #中文验证码
            else:
                ca_type['type'] = 'english' #英文验证码
        else:
            ca_type['url'] = 'none'
            ca_type['type'] = 'none'#没有验证码

        return ca_type

	#获取验证码图片保存到当前目录并识别
    def get_captcha(self,type,url,browser):
        content = re.search('data:image/jpg;base64,(.*)',url.replace('%0A',''))
        hq = content.group(1)
        img = base64.b64decode(hq)
        with open('captcha.jpg', 'wb') as f:
            f.write(img)
            f.close()
            # 自动打开刚获取的验证码
            from PIL import Image
            try:
                img = Image.open('captcha.jpg')
                img.show()
                if type == 'chinese':
                    self.disti_captcha_chinese(browser)
                img.close()
                if type == 'english':
                    self.disti_captcha_english(browser)
            except:
                pass

	# 识别英文验证码
    def disti_captcha_english(self, browser):
        seq = input('请输入验证码\n>')
        browser.find_element_by_xpath("//input[@name='captcha']").send_keys(seq)
        browser.find_element_by_css_selector(
            ".Button.SignFlow-submitButton").click()

	#识别中文验证码
    def disti_captcha_chinese(self,browser):
        points = [[22.796875, 22], [42.796875, 22], [63.796875, 21], [84.796875, 20], [107.796875, 20],
                  [129.796875, 22], [150.796875, 22]]
        input_points = []
        seq = input('请输入倒立文字位置\n>')
        for i in seq:
            input_points.append(points[int(i) - 1])
        img = browser.find_element_by_css_selector(".Captcha-chineseImg")
        location = img.location
        size = img.size
        x1,y1 = input_points[0][0]+location['x'],input_points[0][1]+location['y']
        x2, y2 = input_points[1][0] + location['x'], input_points[1][1] + location['y']
        ActionChains(browser).move_by_offset(x1, y1).click().perform()
        ActionChains(browser).move_by_offset(x2, y2).click().perform()
        browser.find_element_by_css_selector(
            ".Button.SignFlow-submitButton").click()

	#初次登录用selenium模拟，并获得cookies
    def GetCookies(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        browser = webdriver.Chrome(executable_path='./chromedriver.exe',
                                   options=chrome_options)
        # 初次建立连接
        browser.get("https://www.zhihu.com/signin")
        if not self.is_login(browser):
            browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys("手机号")
            #self.driver.implicitly_wait(10)
            #driver.manage().timeouts().implicitlyWait(3, SECONDS)
            browser.find_element_by_css_selector(".Input-wrapper input ").send_keys("密码")
            browser.find_element_by_css_selector(
                ".Button.SignFlow-submitButton").click()
            ca_type = self.is_captch(browser)
            if ca_type['type'] !="none":
                self.get_captcha(ca_type['type'],ca_type['url'],browser)
            time.sleep(10)
        if  self.is_login(browser):
            cookies = browser.get_cookies()
            browser.quit()
            return cookies

	#获取session
    def get_session(self):
        s = requests.Session()
        if not os.path.exists('zhihu_session.txt'):   #如果没有session，则创建一个，并且保存到文件中
            s.headers.clear()
            for cookie in self.GetCookies():
                s.cookies.set(cookie['name'], cookie['value'])
            self.save_session(s)
        else:                                   #如果已存在session，则直接加载使用
            s = self.load_session()
        return s

	#开始爬取
    def Crawl(self):
        s = self.get_session()
        html = s.get(self.home_url).text
        return html

zhihu = Zhihu('https://www.zhihu.com/')
zhihu.Crawl()



