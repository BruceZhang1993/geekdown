import argparse
import asyncio
import functools
import sys

from pydantic import ValidationError

from geekdown.api import GeektimeAPI
from geekdown import models as gm
from geekdown.models import ColumnType


class Prompt:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.q = asyncio.Queue(loop=self.loop)
        self.loop.add_reader(sys.stdin, self.got_input)

    def got_input(self):
        asyncio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)

    async def __call__(self, msg, end='\n', flush=False):
        print(msg, end=end, flush=flush)
        return (await self.q.get()).rstrip('\n')


aio_prompt = Prompt()
aio_input = functools.partial(aio_prompt, end='', flush=True)


class Singleton(type):
    """ singleton metaclass """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Command(metaclass=Singleton):
    COMMANDS = ['user', 'all', 'products', 'login', 'info', 'detail', 'alist', 'download']

    def __init__(self, args):
        self.args = args
        self.api = GeektimeAPI()

    @classmethod
    def init(cls):
        parser = argparse.ArgumentParser(description='Geekdown')
        subparser = parser.add_subparsers(dest='subcommand', required=True)
        for command in cls.COMMANDS:
            p = subparser.add_parser(command)
            if command == 'all':
                p.add_argument('--type', '-t', choices=['article', 'micro', 'video'], required=False)
            if command == 'info':
                p.add_argument('courses', nargs='+')
            if command in ['detail', 'alist', 'download']:
                p.add_argument('course', nargs=1)
        return cls(parser.parse_args())

    async def run(self):
        if self.args.subcommand in self.COMMANDS:
            try:
                await getattr(self, self.args.subcommand)()
                await self.api.session.close()
            except ValidationError as err:
                err.errors()
                print(err)

    async def login(self):
        phone = await aio_input('Phone: ')
        passwd = await aio_input('Password: ')
        data_login = await self.api.login(phone, passwd)
        res = gm.LoginResponse(**data_login)
        if res.code == 0:
            self.api.save_cookie()
            print('Login success')
        elif res.error.code == -3005:
            await self.api.captcha()
            captcha = await aio_input('Captcha: ')
            data_login = await self.api.login(phone, passwd, captcha=captcha)
            res1 = gm.LoginResponse(**data_login)
            if res1.code == 0:
                self.api.save_cookie()
                print('Login success')
            else:
                print(f'({res.error.code}) {res.error.msg}')
        else:
            print(f'({res.error.code}) {res.error.msg}')

    async def user(self):
        data_user = await self.api.user_info()
        gm.UserinfoResponse(**data_user).data_output()

    async def all(self):
        data_all = await self.api.all(course_type=getattr(ColumnType, self.args.type) if self.args.type else None)
        gm.AllCoursesResponse(**data_all).data_output()

    async def products(self):
        data_prod = await self.api.products()
        gm.BuyProductResponse(**data_prod).data_output()

    async def info(self):
        data_info = await self.api.course_info(self.args.courses)
        gm.CourseInfoResponse(**data_info).data_output()

    async def detail(self):
        data_detail = await self.api.course_detail(self.args.course[0])
        gm.CourseDetailResponse(**data_detail).data_output()

    async def alist(self):
        data_list = await self.api.article_list(self.args.course[0])
        gm.ArticleListResponse(**data_list).data_output()

    async def download(self):
        data_detail = await self.api.course_detail(self.args.course[0])
        detail = gm.CourseDetailResponse(**data_detail)
        if detail.data.column_type == ColumnType.article:
            data_list = await self.api.article_list(self.args.course[0])
            alist = gm.ArticleListResponse(**data_list).data.list
            loop = asyncio.get_event_loop()
            for article in alist:
                # await GeektimeAPI.download_audio(article)
                await loop.run_in_executor(None, self.api.article_to_pdf, article.id)
