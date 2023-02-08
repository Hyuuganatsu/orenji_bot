### this module hasn't been refactored to use twilight.

# python
import asyncio
import base64
import re
import random
import io
from typing import Optional
import aiohttp
from config import BACKEND_URL
from .utils import get_image_bytes_from_msg_id, clear_local_q_and_append_Image
from PIL import Image as PILImage

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote, Plain, Source
from graia.ariadne.model import Group, Member
from loguru import logger

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

sd_cmd_pattern = re.compile(r'^(@.+ )?/gen .+( [sml])?')
generate_image_size = {'p':(512, 768), 'l':(768, 512), 'default':(512, 512)}

# 插件信息
__name__ = "stable-diffusion"
__description__ = "call stable-diffusion service to generate anime image"
__author__ = "Orenji"
__usage__ = "command: /gen [prompt(masterpiece and best quality is automatically added)] _[size {s,m,l}]"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group,
    source: Source
):

    text = message.display
    if re.match(sd_cmd_pattern, text) != None:

        ###disable this functionality
        #await app.send_group_message(group, MessageChain([Plain("/gen暂时下线~")]))

        ###enable
        # get the image (maybe exist)
        image = None
        # fetch the reply object
        if Quote in message:
            quote = message.get(Quote)[0]

            # fetch the original message that the reply refers to. The given api quote.origin can fetch the original messageChain, but the Image inside is transcoded to Plain text (we can't get the original image this way).
            image = await get_image_bytes_from_msg_id(app, quote.id)
            logger.warning("get image bytes")

        if not image:
            # get the prompt
            if text[-2] == " " and text[-1] in {'p','l'}:
                prompt = " ".join(text.split()[1:-1])
                size = text.split()[-1]
            else:
                prompt = " ".join(text.split()[1:])
                size = "default"
        else:
            if text[-2] == " " and text[-1] in {'p','l'}:
                prompt = " ".join(text.split()[1:-1])
                size = text.split()[-1]
            else:
                prompt = " ".join(text.split("/gen ")[1:])
                size = "default"

        logger.warning("{}, {}".format(prompt, size))
        try:
            data = {"prompt": "masterpiece, best quality, "+prompt,
                    "seed": random.randint(0, 1 << 32),
                    "n_samples": 1,
                    "sampler": "k_euler_ancestral",
                    "width": generate_image_size[size][0],
                    "height": generate_image_size[size][1],
                    "scale": 11.5,
                    "steps": 45,
                    "noise": 0.1,
                    "masks": None,
                    "image": base64.b64encode(image).decode('UTF-8') if image else None,
                    "uc": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, bad feet, 3D hentai, 3D style, cosplay, red_ribbon",
                    }
            data_for_print = data.copy()
            del data_for_print["image"]
            logger.warning(data_for_print)

            async with aiohttp.ClientSession() as session:
                async with session.post(BACKEND_URL+"stable_diffusion", json=data) as response:
                    logger.info(response)
                    data = await response.json()
                    if "image" not in data:
                        logger.warning("requesting stable diffusion service failed!")
                        return

            # update buffer manually, as someone might 好 to this 2xed Image
            generated_image = Image(base64=data["image"])
            #Quote(id=source.id, groupId=group.id, senderId=sender.id, targetId=group.id, origin=message)
            await app.send_group_message(group, MessageChain([Plain(prompt),generated_image]))
            await clear_local_q_and_append_Image(generated_image, group)
        except Exception as e:
            logger.warning(e)
