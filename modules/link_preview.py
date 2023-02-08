### this module hasn't been refactored to use twilight.

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

# 插件信息
__name__ = "LinkDispatcher"
__description__ = "链接解析姬"
__author__ = "SinceL"
__usage__ = "自动使用"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法: {__usage__}")
channel.author(__author__)

pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    group: Group
):
    if group.id != 954642206:
        text = message.display
        urls: List[str] = re.findall(pattern, text)
        for url in urls:
            url = url.replace(r'/#/', r'/', 1) # wyy
            message = await get_info(url)
            if message:
                await app.send_group_message(group, message)

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