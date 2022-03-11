# python
import base64
from random import choice, random
from string import Template
import aiohttp

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.base import DetectPrefix, DetectSuffix
from graia.ariadne.model import Group, Member

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema


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
    not_r18_image_bytes = await get_setu_bytes_from_lilocon_api(False)
    if not_r18_image_bytes:
        await app.sendGroupMessage(group,
                                   MessageChain([Image(base64=base64.b64encode(not_r18_image_bytes).decode('UTF-8'))]))
    else:
        await app.sendGroupMessage(group, MessageChain([Plain("连接到lolicon api失败~")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('/r18'), DetectSuffix('/r18')]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    r18_image_bytes = await get_setu_bytes_from_lilocon_api(True)
    if r18_image_bytes:
        await app.sendGroupMessage(group, MessageChain([Image(base64=base64.b64encode(r18_image_bytes).decode('UTF-8'))]))
    else:
        await app.sendGroupMessage(group,MessageChain([Plain("连接到lolicon api失败~")]))


##
## http handlers
##
async def get_setu_bytes_from_lilocon_api(r18: bool=False):
    async with aiohttp.ClientSession() as session:
        # send sr request with data={image:binary, tile_mode:str}
        request_body = {
            "r18": int(r18),
            "num": 1,
            "size": "original"
        }
        async with session.post("https://api.lolicon.app/setu/v2", data=request_body) as response:
            data = await response.json()
            img_original_url = data["data"][0]["urls"]["original"]
            async with session.get(img_original_url) as response:
                if response.status == 200:
                    return await response.read()
                else: return None