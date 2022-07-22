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
        text = message.asDisplay()
        urls: List[str] = re.findall(pattern, text)
        for url in urls:
            url = url.replace(r'/#/', r'/', 1) # wyy
            message = await get_info(url)
            if message:
                await app.sendGroupMessage(group, message)

async def get_info(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text()
            soup = BeautifulSoup(data, 'html.parser')
            title = soup.find_all('meta', property='og:title')[-1].attrs['content']
            cover = soup.find_all('meta', property='og:image')[-1].attrs['content']
            url = soup.find_all('meta', property='og:url')[-1].attrs['content']
            if cover:
                if 'hqdefault' in cover:
                    cover = cover.replace('hqdefault', 'maxresdefault') # y2b
                return MessageChain.create(Image(url=cover), Plain(title), Plain(url))