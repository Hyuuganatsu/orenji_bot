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


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('/setu')]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    text = message.asDisplay()
    query = None
    if len(text) > 6:
        query = await parse_search_query(text[6:])
    not_r18_image_bytes = await get_setu_bytes_from_lilocon_api(False, query)
    if type(not_r18_image_bytes) == bytes:
        await app.sendGroupMessage(group, MessageChain([Image(base64=base64.b64encode(not_r18_image_bytes).decode('UTF-8'))]))
    elif type(not_r18_image_bytes) == str:
        await app.sendGroupMessage(group, MessageChain([Plain(not_r18_image_bytes)]))
    else:
        await app.sendGroupMessage(group, MessageChain([Plain("连接到lolicon api失败~")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('/r18')]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    text = message.asDisplay()
    query = None
    if len(text) > 5:
        query = await parse_search_query(text[5:])
    r18_image_bytes = await get_setu_bytes_from_lilocon_api(True, query)
    if type(r18_image_bytes) == bytes:
        await app.sendGroupMessage(group, MessageChain([Image(base64=base64.b64encode(r18_image_bytes).decode('UTF-8'))]))
    elif type(r18_image_bytes) == str:
        await app.sendGroupMessage(group, MessageChain([Plain(r18_image_bytes)]))
    else:
        await app.sendGroupMessage(group,MessageChain([Plain("连接到lolicon api失败~")]))


##
## http handlers
##
async def get_setu_bytes_from_lilocon_api(r18: bool=False, query: list=None):
    async with aiohttp.ClientSession() as session:
        # send sr request with data={image:binary, tile_mode:str}
        json_param = {
            "r18": int(r18),
            "num": 1,
            "size": "original"
        }
        if query: json_param["tag"] = query
        async with session.post("https://api.lolicon.app/setu/v2", json=json_param) as response:
            data = await response.json()
            if len(data["data"]) == 0:
                return "没有符合的图片~"
            img_original_url = data["data"][0]["urls"]["original"]
            async with session.get(img_original_url) as response:
                if response.status == 200:
                    return await response.read()
                else: return None

##
## query parser
##
async def parse_search_query(query: str=""):
    and_lines = query.split("and")
    rtn = [line.split("or") for line in and_lines]
    rtn = [[tag.lstrip().rstrip() for tag in line]for line in rtn]
    return rtn
