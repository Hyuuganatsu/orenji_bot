import datetime

from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import FriendMessage, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member, Friend
from graia.ariadne.message.element import Plain, Image

from collections import defaultdict
#from ChatGPT.src.revChatGPT.V3 import Chatbot
from revChatGPT.V3 import Chatbot
import re
import aiohttp
from loguru import logger
from config.config import OPENAI_API_KEY, BACKEND_URL

# module config
from config.module_config import check_module_enabled

# 插件信息
__name__ = "chatGPTClient"
__description__ = "与chatGPT进行对话"
__author__ = "orenji"
__usage__ = "自动使用"

saya = Saya.current()
channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法: {__usage__}")
# channel.author(__author__)

#api实例池
conversation_pool = defaultdict(lambda:Chatbot(api_key=OPENAI_API_KEY, max_tokens=1500))

chat_cmd_pattern = re.compile(r'^/chat .+')


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
@check_module_enabled("chatGPT")
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
        conversation_pool[sender.id] = Chatbot(api_key=OPENAI_API_KEY, max_tokens=1500)
        return
    response = chatbot.ask(prompt)
    # logger.warning(response)
    if response:
        await app.send_group_message(group, MessageChain([Plain("Q:"+prompt+"\nA:"+response)]))

@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def friend_message_listener(
    app: Ariadne,
    friend: Friend,
    message: MessageChain,
):
    text = message.display
    if text[0] == '/':
        # command mode
        cmd = text[1:6]
        if cmd == "reset":
            conversation_pool[friend.id] = Chatbot(api_key=OPENAI_API_KEY, max_tokens=3000)
            return
        elif cmd == "check":
            year, month = text[7:].split(" ")
            year, month = int(year), int(month)
            async with aiohttp.ClientSession() as session:
                async with session.post(BACKEND_URL + "api/usage/get",
                                        json={"qq_id": friend.id, "year_month": "{}-{}".format(year, month)}
                                        ) as response:
                    response_json = await response.json()
                    #logger.info(response_json)
                    await app.send_friend_message(friend, MessageChain([Plain("{}年{}月使用金额：{:.3f}元".format(year, month, float(response_json["usage"])))]))
    else:
        # chat mode
        prompt = text

        # api实例
        chatbot = conversation_pool[friend.id]

        response = chatbot.ask(prompt)
        #logger.warning(response)
        if response:
            await app.send_friend_message(friend, MessageChain([Plain(response)]))

        # record usage in backend database
        now = datetime.datetime.now()
        async with aiohttp.ClientSession() as session:
            async with session.post(BACKEND_URL + "api/usage/set",
                                    json={"qq_id": friend.id, "additional_usage": 0*0.00001392}
                                    ) as response:
                pass