from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain, Image

from collections import defaultdict
from revChatGPT.V3 import Chatbot
import re
from loguru import logger
from config import OPENAI_API_KEY

# 插件信息
__name__ = "chatGPTClient"
__description__ = "与chatGPT进行对话"
__author__ = "orenji"
__usage__ = "自动使用"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法: {__usage__}")
channel.author(__author__)

#api实例池
conversation_pool = defaultdict(lambda:Chatbot(api_key=OPENAI_API_KEY))

chat_cmd_pattern = re.compile(r'^/chat .+')


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def group_message_listener(
    app: Ariadne,
    sender: Member,
    message: MessageChain,
    group: Group
):
    text = message.display
    if re.match(chat_cmd_pattern, text) == None:
        return
    prompt = text.split("/chat ")[1]
    # api实例
    chatbot = conversation_pool[sender.id]

    # 用户手动重置上下文
    if prompt == "reset":
        conversation_pool[sender.id] = Chatbot(api_key=OPENAI_API_KEY)
        return
    response = chatbot.ask(prompt)
    # logger.warning(response)
    if response:
        await app.send_group_message(group, MessageChain([Plain("Q:"+prompt+"\nA:"+response)]))