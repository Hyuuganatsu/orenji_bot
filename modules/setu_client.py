# python
import hashlib
import os
import re
import magic
import base64
import aiohttp
from collections import deque
from config import BACKEND_URL
from .utils import get_image_bytes_from_msg_id

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote, Plain
from graia.ariadne.message.parser.base import DetectPrefix, DetectSuffix
from graia.ariadne.model import Group, Member

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

add_setu_cmd_pattern = re.compile(r'(@\d+ )?好')
delete_setu_cmd_pattern = re.compile(r'(@\d+ )?一般')

setu_detect_buffer = deque() #stores message id, current buffer size == 1

# 插件信息
__name__ = "setu_client"
__description__ = "和orenji_mini(server)的数据库交互，实现存取色图"
__author__ = "Orenji"
__usage__ = "在群里发/se即可从数据库随机取一张色图"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('好'), DetectSuffix('好')]))
async def buffer_add_setu_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    if setu_detect_buffer:
        image_bytes = await setu_detect_buffer[0].get_bytes()
        # try to add setu to backend db
        try:
            await add_image_bytes_to_backend_db(image_bytes)
        except Exception as e:  # if the image is broken(no url and no base64), return
            print(e)
        setu_detect_buffer.popleft()
        print("尝试添加到数据库，因为有人跟了好")



@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def delete_or_quote_add_setu_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    text = message.asDisplay()
    # monitoring images. setu_detect_buffer will always having the latest image.
    if Image in message:
        setu_detect_buffer.append(message.getFirst(Image))
        while len(setu_detect_buffer) > 1:
            setu_detect_buffer.popleft()

    if re.match(add_setu_cmd_pattern, text) != None: # maybe reply to a nice setu?
        # fetch the reply object
        if Quote not in message: return
        quote = message.get(Quote)[0]

        # fetch the original message that the reply refers to. The given api quote.origin can fetch the original messageChain, but the Image inside is transcoded to Plain text (we can't get the original image this way).
        image_bytes = await get_image_bytes_from_msg_id(app, quote.id)

        # try to add setu to backend db
        try:
            await add_image_bytes_to_backend_db(image_bytes)
        except Exception as e:  # if the image is broken(no url and no base64), return
            print(e)
        print("尝试添加到数据库，因为有人回复了好")

    elif re.match(delete_setu_cmd_pattern, text) != None: # maybe want to delete this setu from db?
        if Quote not in message: return
        quote = message.get(Quote)[0]
        image_bytes = await get_image_bytes_from_msg_id(app, quote.id)
        try:
            await delete_image_bytes_from_backend_db(image_bytes)
        except Exception as e:  # if the image is broken(no url and no base64), return
            print(e)
        print("尝试从数据库删除该色图")


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('/se'), DetectSuffix('/se')]))
async def get_random_setu_from_db_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    print("正获取随机色图")
    async with aiohttp.ClientSession() as session:
        async with session.get(BACKEND_URL+"setu/get-random") as response:
            image_bytes = await response.read()
            print("正在发回")
            await app.sendGroupMessage(group, MessageChain([Image(base64=base64.b64encode(image_bytes).decode('UTF-8'))]))

##
## http handlers
##

# add setu handler
async def add_image_bytes_to_backend_db(image_bytes):
    async with aiohttp.ClientSession() as session:
        async with session.post(BACKEND_URL + "setu/add", data={"setu": image_bytes, "mime": magic.from_buffer(image_bytes).split()[0]}) as response:
            if response.status == 400:
                print("已经添加过该图片")
            elif response.status == 404:
                print("请求中不包含setu文件")
            elif response.status == 204:
                print("成功加入数据库")
            else:
                print("backend internal error")
            return

# delete setu handler
async def delete_image_bytes_from_backend_db(image_bytes):
    img_sha = hashlib.sha256(image_bytes).hexdigest()
    async with aiohttp.ClientSession() as session:
        async with session.delete(BACKEND_URL + "setu/delete/"+img_sha) as response:
            if response.status == 404:
                print("数据库中不存在该图")
            elif response.status == 400:
                print("表项已删除，但硬盘上本来就不存在该图")
            elif response.status == 204:
                print("成功删除")
            else:
                print("backend internal error")
            return