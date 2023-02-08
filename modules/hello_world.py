# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Friend

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

#project
from loguru import logger

# 插件信息
__name__ = "hello_world"
__description__ = "test friend listener"
__author__ = "Orenji"
__usage__ = "send a private message to bot. You should receive a response as \"Hello, World!\""

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def friend_message_listener(app: Ariadne, friend: Friend):
    logger.warning("caught friend message!")
    await app.send_friend_message(friend, MessageChain(Plain("Hello, World!")))