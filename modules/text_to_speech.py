# python
import re
import aiohttp
from local_secret_config import BACKEND_URL

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote, Plain
from graia.ariadne.model import Group, Member

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

tts_cmd_pattern = re.compile(r'^/say\d [^ ]+$')


# 插件信息
__name__ = "text-to-speech"
__description__ = "post to my web app http://sr-orenji.ml:6990/text_to_speech to get a speech in QQ audio."
__author__ = "Orenji"
__usage__ = "/say[character_idx] [text]"

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
    group: Group
):

    full_text = message.asDisplay()
    speaker_id = int(full_text.split()[0].split("/say")[1])
    text = full_text.split()[1]
    if re.match(tts_cmd_pattern, text) != None: # has pattern like "@12768888 2x", maybe a sr command

        # try to request super resolution service using this image. If success, return the upscaled image
        try:
            async with aiohttp.ClientSession() as session:
                # send sr request with data={image:binary, tile_mode:str}
                async with session.post(BACKEND_URL, data={"text": text, "spaker_id": speaker_id}) as response:
                    data = await response.json()
                    if "audio_bytes" not in data:
                        print("requesting super resolution service failed!")
                        return
                    audio_bytes = data["audio_bytes"]
                    mine = data["mime"]

            await app.sendGroupMessage(group, MessageChain([Plain("got audio bytes")]))

        except Exception as e: # if the image is broken(no url and no base64), return
            print(e)