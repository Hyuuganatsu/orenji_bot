# python
import re
import base64
import aiohttp

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Voice
from graia.ariadne.model import Group, Member
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ParamMatch, RegexResult, WildcardMatch, SpacePolicy

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from loguru import logger
from graiax import silkcoder
from config.config import BACKEND_URL
from config.module_config import check_module_enabled

# 2023-01-08 delete: this is useless after using Twilight, but it's here for future reference.
#tts_cmd_pattern = re.compile(r'^/say \d+[ 　]')


# 插件信息
__name__ = "text-to-speech"
__description__ = "post to my web app http://sr-orenji.ml:6990/text_to_speech to get a speech in QQ audio."
__author__ = "Orenji"
__usage__ = "/say [character_idx] [text]"

saya = Saya.current()
channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法：{__usage__}")
# channel.author(__author__)

@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([
    FullMatch("/say").space(SpacePolicy.FORCE), # 强制尾随空格
    "speaker_id" @ ParamMatch().space(SpacePolicy.FORCE),
    "text" @ WildcardMatch()
])]))
@check_module_enabled("text_to_speech")
async def group_message_listener(
    app: Ariadne,
    group: Group,
    speaker_id: RegexResult, text: RegexResult
):
    speaker_id = speaker_id.result.display
    text = text.result.display
    logger.info("tts, speaker_id:{}, text:{}".format(speaker_id, text))
    # try to request super resolution service using this image. If success, return the upscaled image
    try:
        async with aiohttp.ClientSession() as session:
            # send sr request with data={text:string, speaker_id:int}
            async with session.post(BACKEND_URL+"api/text_to_speech", data={"text": text, "speaker_id": speaker_id}) as response:
                data = await response.json()
                if "audio_strs" not in data:
                    print("requesting text-to-speech service failed!")
                    return
                audio_bytes = base64.b64decode(data["audio_strs"].encode("UTF8"))
                audio_bytes = await silkcoder.async_encode(audio_bytes, ios_adaptive=True)

        await app.send_group_message(group, MessageChain(Voice(data_bytes=audio_bytes)))

    except Exception as e: # if the image is broken(no url and no base64), return
        logger.warning(e)