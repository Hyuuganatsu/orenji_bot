# python
import io
import asyncio
import aiohttp
from typing import Optional
from PIL import Image as PILImage

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch
from loguru import logger

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from local_secret_config import BACKEND_URL
from .utils import get_image_bytes_from_msg_id, clear_local_q_and_append_Image


# 插件信息
__name__ = "super-resolution"
__description__ = "call my web app http://sr-orenji.ml:6990/ to generate a 2x version of the designated image"
__author__ = "Orenji"
__usage__ = "reply to an image, and type \"2x\" to call this api"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([
    RegexMatch(r'(@\d+ )?2x') # has pattern like "@12768888 2x", maybe a sr command
])]))
async def super_resolution_command_listener(
    app: Ariadne,
    group: Group,
    event: MessageEvent
):
    # fetch the reply object
    if not event.quote: return
    quote = event.quote

    # fetch the original message that the reply refers to. The given api quote.origin can fetch the original messageChain, but the Image inside is transcoded to Plain text (we can't get the original image this way).
    image_bytes = await get_image_bytes_from_msg_id(app, quote.id)

    #if image is oversize, refuse to 2x.
    with PILImage.open(io.BytesIO(image_bytes)) as img:
        w, h = img.size
        if w * h >= 6000000: # size must <= 2560*1440
            await app.send_group_message(group, MessageChain(Plain("{}*{}太大啦，服务器会吃不消的~".format(w, h))))
            return


    # try to request super resolution service using this image. If success, return the upscaled image
    try:
        sr_image_base64 = await run_super_resolution(image_bytes = image_bytes)
        await app.send_group_message(group, MessageChain(Image(base64 = sr_image_base64)))

        # update buffer manually, as someone might 好 to this 2xed Image
        img_2x = Image(base64=sr_image_base64)
        await clear_local_q_and_append_Image(img_2x, group)
        #print(img_2x.get_bytes())

    except Exception as e: # if the image is broken(no url and no base64), return
        logger.warning("super resolution错误，", e)

async def run_super_resolution(image_bytes: bytes) -> Optional[str]:
    async with aiohttp.ClientSession() as session:
        # send sr request with data={image:binary, tile_mode:str}
        async with session.post(BACKEND_URL, data={"raw_image": image_bytes, "tile_mode":"4"}) as response:
            data = await response.json()
            if "task_id" not in data:
                logger.warning("requesting super resolution service failed!")
                return
            task_id = data["task_id"]

        # try to retrieve result every one second
        for i in range(600):
            await asyncio.sleep(1)
            async with session.get(BACKEND_URL+'get-result/{}'.format(task_id)) as response:
                data = await response.json()
                if "state" not in data:
                    logger.warning("requesting sr result failed!")
                    return
                if data["state"] == True:
                    return data["image"] # sr-inference success, return image in base64

