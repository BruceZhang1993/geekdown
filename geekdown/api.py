import asyncio
import json
from http.cookies import BaseCookie
from pathlib import Path
from random import random
import time

from PIL import Image
from aiohttp import CookieJar, ClientSession
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from yarl import URL

from geekdown.models import Article, VideoPlayauthResponse


class GeektimeAPIException(Exception):
    pass


class Singleton(type):
    """ singleton metaclass """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GeektimeAPI(metaclass=Singleton):
    DEFAULT_HEADER = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/81.0.4044.92 Safari/537.36',
        'Referer': 'https://account.geekbang.org',
        'Host': 'time.geekbang.org',
        'Origin': 'https://account.geekbang.org',
    }
    LOGIN_READY = 'https://account.geekbang.org/account/info/user'
    LOGIN_REFERER = 'https://account.geekbang.org/signin?redirect=https%3A%2F%2Ftime.geekbang.org%2F'
    LOGIN_URI = 'https://account.geekbang.org/account/ticket/login'
    CAPTCHA_URI = 'https://account.geekbang.org/account/captcha/ticket'
    PRODUCTS_URI = 'https://time.geekbang.org/serv/v1/my/products/all'
    LABELS_URI = 'https://time.geekbang.org/serv/v1/column/labels'
    USERINFO_URI = 'https://account.geekbang.org/account/user'
    COURSE_ALL_URI = 'https://time.geekbang.org/serv/v1/column/newAll'
    COURSE_INFO_URI = 'https://time.geekbang.org/serv/v1/column/details'
    COURSE_DETAIL_URI = 'https://time.geekbang.org/serv/v1/column/intro'
    ARTICLE_LIST_URI = 'https://time.geekbang.org/serv/v1/column/articles'
    VIDEO_AUTH_URI = 'https://time.geekbang.org/serv/v3/source_auth/video_play_auth'
    VIDEO_INFO_URI = 'https://vod.cn-shanghai.aliyuncs.com/'
    COOKIE_PATH = Path.home() / '.cache' / 'geekdown' / 'geekdown.cookie'
    DOWNLOAD_PATH = Path.home() / 'Documents' / 'Geekdown'

    def __init__(self):
        self.cookie_jar = CookieJar(unsafe=True)
        if self.COOKIE_PATH.exists():
            self.cookie_jar.load(self.COOKIE_PATH)
        else:
            self.COOKIE_PATH.parent.mkdir(parents=True)
        if not self.DOWNLOAD_PATH.exists():
            self.DOWNLOAD_PATH.mkdir(parents=True)
        self.session = ClientSession(cookie_jar=self.cookie_jar, headers=self.DEFAULT_HEADER)

    async def ready(self):
        lfid = f'{int(time.time() * 1000)}-{int(1e7 * random())}-{int(1e7 * random())}'
        gk_process_ev = json.dumps({
            'count': 6,
            'utime': int(time.time() * 1000),
            'referer': 'https://time.geekbang.org/',
            'target': 'page_geektime_login',
            'referrerTarget': 'page_geektime_login',
        })
        c = BaseCookie({'LF_ID': lfid, 'gk_process_ev': gk_process_ev})
        self.cookie_jar.update_cookies([('LF_ID', c.get('LF_ID')), ('gk_process_ev', c.get('gk_process_ev'))],
                                       URL(self.LOGIN_URI))
        async with self.session.get(self.LOGIN_REFERER) as r:
            await r.text()
        async with self.session.get(self.LOGIN_READY) as r:
            await r.text()

    async def login(self, username: str, password: str, captcha: str = ''):
        headers = self.DEFAULT_HEADER
        headers['Referer'] = self.LOGIN_REFERER
        headers['Host'] = 'account.geekbang.org'
        data = {
            'country': 86,
            'cellphone': username,
            'password': password,
            'captcha': captcha,
            'remeber': 1,
            'platform': 3,
            'appid': 1,
        }
        await self.ready()
        async with self.session.post(self.LOGIN_URI, headers=headers, data=json.dumps(data)) as r:
            return await r.json()

    async def captcha(self):
        headers = self.DEFAULT_HEADER
        headers['Referer'] = self.LOGIN_REFERER
        headers['Host'] = 'account.geekbang.org'
        async with self.session.get(self.CAPTCHA_URI, headers=headers) as r:
            image_bytes = await r.content.read()
            with open('/tmp/geekdown_captcha.png', 'wb') as f:
                f.write(image_bytes)
                f.flush()
            image = Image.open(open('/tmp/geekdown_captcha.png', 'rb'))
            loop_ = asyncio.get_event_loop()
            loop_.run_in_executor(None, image.show)

    async def products(self):
        async with self.session.post(self.PRODUCTS_URI) as r:
            return await r.json()

    async def labels(self):
        async with self.session.post(self.LABELS_URI) as r:
            return await r.json()

    async def course_info(self, ids=None):
        if ids is None:
            ids = []
        async with self.session.post(self.COURSE_INFO_URI, data=json.dumps({'ids': ids})) as r:
            return await r.json()

    async def course_detail(self, cid, with_group_buy=True):
        async with self.session.post(self.COURSE_DETAIL_URI,
                                     data=json.dumps({'cid': cid, 'with_group_buy': with_group_buy})) as r:
            return await r.json()

    async def all(self, course_type: int = None):
        async with self.session.post(self.COURSE_ALL_URI,
                                     data=json.dumps({'type': course_type} if course_type else {})) as r:
            return await r.json()

    async def article_list(self, cid):
        data = {
            'cid': cid,
            'order': 'earliest',
            'prev': 0,
            'sample': False,
            'size': 1000,
        }
        async with self.session.post(self.ARTICLE_LIST_URI, data=json.dumps(data)) as r:
            return await r.json()

    def article_to_pdf(self, aid):
        url = f'https://time.geekbang.org/column/article/{aid}'
        print(f'Downloading: {url}')
        cookies = [{'name': cookie.key, 'value': cookie.value} for cookie in self.cookie_jar]
        settings = {
            'recentDestinations': [{'id': 'Save as PDF', 'origin': 'local', 'account': ''}],
            'selectedDestinationId': 'Save as PDF',
            'version': 2,
        }
        prefs = {
            'printing.print_preview_sticky_settings.appState': json.dumps(settings),
            'savefile.default_directory': self.DOWNLOAD_PATH.as_posix(),
        }
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_argument('--kiosk-printing')
        # chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(800, 600)
        driver.get('https://time.geekbang.org')
        for c in cookies:
            driver.add_cookie(c)
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'bottom'))
        )
        # Wait 3 seconds
        time.sleep(3)
        element_class = driver.find_element_by_xpath('//div[text()="下载APP"]') \
            .find_element_by_xpath('./../..').get_attribute('class')
        element_star_class = driver.find_element_by_xpath('//div[text()=""]').get_attribute('class') \
            .replace('iconfont', '').strip()
        js_script = f'''
document.getElementsByClassName('{element_class}')[0].setAttribute('style', 'display:none;');
document.getElementsByClassName('{element_star_class}')[0].setAttribute('style', 'display:none;');
document.getElementsByClassName('bottom')[0].setAttribute('style', 'display:none;');
        '''
        driver.execute_script(js_script)
        driver.execute_script('window.print();')
        driver.close()

    async def get_video_auth(self, aid, vid):
        data = {
            'source_type': 1,
            'aid': aid,
            'video_id': vid,
        }
        async with self.session.post(self.VIDEO_AUTH_URI, data=json.dumps(data)) as r:
            return await r.json()

    async def get_video(self, play_auth):
        pass

    async def user_info(self):
        headers = self.DEFAULT_HEADER
        headers['Referer'] = self.LOGIN_REFERER
        headers['Host'] = 'account.geekbang.org'
        async with self.session.post(self.USERINFO_URI, headers=headers) as r:
            return await r.json()

    @classmethod
    async def download_audio(cls, article: Article):
        if article.audio_download_url:
            print(f'Downloading: {article.audio_download_url}')
            async with ClientSession() as session:
                async with session.get(article.audio_download_url,
                                       headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) '
                                                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                                                              '81.0.4044.92 Safari/537.36',
                                                'Authority': 'static001.geekbang.org',
                                                'Accept': '*/*'}) as r:
                    with open((cls.DOWNLOAD_PATH / f'{article.article_title}.mp3').as_posix(), 'wb') as f:
                        f.write(await r.content.read())
                        f.flush()

    def save_cookie(self):
        self.cookie_jar.save(self.COOKIE_PATH)


async def main():
    api = GeektimeAPI()
    data = await api.get_video_auth(248858, '659c18f05fa24ed99c14308b6a7ef513')
    auth = VideoPlayauthResponse(**data).data.play_auth
    print(await api.get_video(auth))
    await api.session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
