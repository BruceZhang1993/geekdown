from datetime import datetime
from enum import IntEnum
from typing import List, Any, Optional, Union

from pydantic import BaseModel, validator


class ColumnType(IntEnum):
    article = 1
    micro = 2
    video = 3


class ProductItem(BaseModel):
    class Extra(BaseModel):
        last_aid: int
        column_id: int
        column_title: str
        column_subtitle: str
        author_name: str
        author_intro: str
        column_cover: str
        column_type: ColumnType
        article_count: int
        is_include_audio: bool

    title: str
    cover: str
    type: str
    extra: Extra


class Page(BaseModel):
    count: int
    more: Optional[bool]


class Product(BaseModel):
    id: int
    title: str
    page: Page
    list: List[ProductItem]


class Nav(BaseModel):
    id: int
    name: str
    color: str
    icon: str


class LabelData(BaseModel):
    class Label(BaseModel):
        pid: int
        name: str
        sort: int
        lid: int

    nav: List[Nav]
    labels: List[Label]


class Userinfo(BaseModel):
    uid: int
    uid_str: str
    type: int
    cellphone: str
    country: str
    nickname: str
    avatar: Optional[str]
    gender: str
    birthday: str
    graduation: str
    profession: str
    industry: str
    description: str
    province: str
    city: str
    mail: str
    wechat: str
    github_name: str
    github_email: str
    company: str
    post: str
    expirence_years: str
    school: str
    real_name: str
    name: str
    address: str
    mobile: str
    contact: str
    position: str
    passworded: bool
    create_time: datetime
    join_infoq: Union[int, str, None]
    actives: dict
    is_student: bool
    student_expire_time: int
    platform: Optional[int]
    app_id: Optional[int]


class Course(BaseModel):
    id: int
    column_ctime: datetime
    column_groupbuy: bool
    column_price: int
    column_price_first: int
    column_price_market: int
    column_sku: int
    column_type: ColumnType
    had_sub: bool
    is_channel: bool
    is_experience: bool
    last_aid: int
    last_chapter_id: int
    price_type: int
    sub_count: int


class CourseInfo(BaseModel):
    id: int
    author_intro: str
    author_name: str
    column_bgcolor: str
    column_cover: str
    column_cover_small: str
    column_cover_wxlite: str
    column_ctime: datetime
    column_price: int
    column_price_market: int
    column_price_sale: int
    column_sku: int
    column_subtitle: str
    column_title: str
    column_type: ColumnType
    column_unit: str
    had_sub: bool
    is_channel: bool
    is_experience: bool
    is_onboard: bool
    price_type: int
    sub_count: int
    update_frequency: str


class CourseDetail(BaseModel):
    id: int
    article_count: int
    article_learned_count: int
    article_req_learned_count: int
    article_req_total_count: int
    article_total_count: int
    author_header: str
    author_info: str
    author_intro: str
    author_name: str
    channel_back_amount: int
    column_begin_time: datetime
    column_bgcolor: str
    column_cover: str
    column_cover_explore: str
    column_cover_inner: str
    column_cover_wxlite: str
    column_ctime: datetime
    column_end_time: datetime
    column_intro: str
    column_name: str
    column_poster: str
    column_poster_wxlite: str
    column_price: int
    column_price_market: int
    column_share_title: str
    column_sharesale: bool
    column_sharesale_data: str
    column_sku: int
    column_subtitle: str
    column_title: str
    column_type: ColumnType
    column_unit: str
    column_utime: datetime
    column_video_cover: str
    column_video_media: str
    column_wxlite_code: str
    first_promo: dict
    footer_cover_data: Optional[str]
    freelyread_count: int
    freelyread_total: int
    groupbuy_for_gift: dict
    had_faved: bool
    had_sub: bool
    is_channel: bool
    is_experience: bool
    is_finish: bool
    is_include_audio: bool
    is_include_preview: bool
    is_member_sub: bool
    is_onborad: bool
    is_preorder: bool
    is_sale_product: bool
    is_shareget: bool
    is_sharesale: bool
    last_aid: int
    last_chapter_id: int
    lecture_url: str
    nav_id: int
    nps: dict
    product_type: str
    rate_percent: int
    show_chapter: bool
    sub_count: int
    update_frequency: str


class Article(BaseModel):
    id: int
    article_title: str
    article_summary: str
    video_cover: Optional[str]
    video_id: Optional[str]
    video_time: Optional[str]
    video_size: Optional[int]
    audio_download_url: Optional[str]
    audio_title: Optional[str]
    audio_time: Optional[str]
    audio_size: Optional[int]
    audio_url: Optional[str]


# Response models
class BaseResponse(BaseModel):
    class Error(BaseModel):
        code: Optional[int]
        msg: Optional[str]
    code: int
    error: Union[list, Error, dict]
    extra: Union[list, dict]
    data: Any

    def data_output(self, data=None, level=0):
        if data is None:
            data = self.data
        if isinstance(data, list):
            for item in data:
                self.data_output(item, level)
                print()
        else:
            for name, value in data:
                if isinstance(value, list) or isinstance(value, BaseModel):
                    print(' ' * level * 2 + f'{name} =>')
                    self.data_output(value, level + 1)
                else:
                    print(' ' * level * 2 + f'{name} => {value}')


class BuyProductResponse(BaseResponse):
    data: List[Product]


class LabelResponse(BaseResponse):
    data: LabelData


class UserinfoResponse(BaseResponse):
    data: Userinfo


class LoginResponse(BaseResponse):
    data: Union[Userinfo, list, dict]


class AllCoursesResponse(BaseResponse):
    class AllCoursesData(BaseModel):
        list: List[Course]
        nav: List[Nav]
        page: Page

    data: AllCoursesData


class CourseInfoResponse(BaseResponse):
    data: List[CourseInfo]


class CourseDetailResponse(BaseResponse):
    data: CourseDetail


class ArticleListResponse(BaseResponse):
    class ArticleListData(BaseModel):
        list: List[Article]
        page: Page
    data: ArticleListData


class VideoPlayauthResponse(BaseResponse):
    class VideoPlayauth(BaseModel):
        play_auth: str
    data: VideoPlayauth
