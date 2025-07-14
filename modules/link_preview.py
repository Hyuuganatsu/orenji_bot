### this module hasn't been refactored to use twilight.
from graia.ariadne.message import Source
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group
from graia.ariadne.message.element import Plain, Image
from bs4 import BeautifulSoup
import aiohttp
import re
from typing import List
from loguru import logger
import bilibili_api
from config.module_config import check_module_enabled

# 插件信息
__name__ = "LinkDispatcher"
__description__ = "链接解析姬"
__author__ = "SinceL"
__usage__ = "自动使用"

saya = Saya.current()
channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法: {__usage__}")
# channel.author(__author__)

url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
bilibili_pattern = r'https?://www\.bilibili\.com/video/(BV\w+)[/?]?'
bilibili_share_pattern = r'https?://b23\.tv/(\w+)'
url_trim_pattern = r'(.*?)(\?.*)?$'

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
@check_module_enabled("link_preview")
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    source: Source
):
    text = message.display
    urls: List[str] = re.findall(url_pattern, text)
    for url in urls:
        url = url.replace(r'/#/', r'/', 1) # wyy
        bilibili_share_match = re.search(bilibili_share_pattern, url)
        if bilibili_share_match:
            url = await bilibili_api.get_real_url(url)
        bilibili_match = re.search(bilibili_pattern, url)
        if bilibili_match:
            v = bilibili_api.video.Video(bvid=bilibili_match.group(1))
            info = await v.get_info()
            trim_match = re.match(url_trim_pattern, url)
            message = MessageChain(Image(url=info["pic"]), Plain(info["title"] + " "), Plain(trim_match.group(1) if trim_match else url))
        else:
            message = await get_info(url)
        if message:
            await app.send_group_message(group, message)
            # try:
            #     await app.recall_message(source)
            # except PermissionError:
            #     logger.warning("没有足够权限撤回！")


async def get_info(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text()
            soup = BeautifulSoup(data, 'html.parser')
            title = get_element(soup, 'og:title')
            cover = get_element(soup, 'og:image')
            url = get_element(soup, 'og:url')
            if title and url:
                if cover:
                    #if 'hqdefault' in cover:
                        #cover = cover.replace('hqdefault', 'maxresdefault') # y2b
                    if 'https:' not in cover:   # bilibili
                        cover = 'https:' + cover
                    if '@' in cover:            # bilibili
                        cover  = cover.split('@')[0]
                    return MessageChain(Image(url=cover), Plain(f"{title} "), Plain(url))
                return MessageChain(Plain(f"{title} "), Plain(url))
            return None

def get_element(soup: BeautifulSoup, prop: str):
    elements = soup.find_all('meta', property=prop)
    if len(elements) > 0:
        return elements[-1].attrs['content']
    return ""