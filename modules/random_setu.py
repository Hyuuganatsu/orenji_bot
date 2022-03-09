# python
import base64
from random import choice, random
from string import Template
import aiohttp

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import DetectPrefix, DetectSuffix
from graia.ariadne.model import Group, Member

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema


bakas = [Template('${name}小老弟行不行啊'), Template('这个${name}真的太逊了'), Template('逊馁，${name}'), Template('菜${name}'),
         Template('菜狗${name}'), Template('咸鱼 ${name} 咸鱼'), Template('嫌弃${name}'), Template('笨蛋${name}')]


# 插件信息
__name__ = "random_setu"
__description__ = "被调用时发一张色图到群里"
__author__ = "Orenji"
__usage__ = "在群里发/setu"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('/setu'), DetectSuffix('/setu')]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    async with aiohttp.ClientSession() as session:
        # send sr request with data={image:binary, tile_mode:str}
        request_body = {
            "r18": 0,
            "num": 1,
            "size": "original"
        }
        async with session.post("https://api.lolicon.app/setu/v2", data=request_body) as response:
            data = await response.json()
            img_original_url = data["data"][0]["urls"]["original"]
            async with session.get(img_original_url) as response:
                if response.status == 200:
                    img_bytes = await response.read()
                    await app.sendGroupMessage(group, MessageChain([Image(base64=base64.b64encode(img_bytes).decode('UTF-8'))]))

