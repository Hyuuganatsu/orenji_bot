# import aiohttp
# from graia.saya import Saya, Channel
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.ariadne.app import Ariadne
# from graia.ariadne.event.message import GroupMessage
# from graia.ariadne.message.chain import MessageChain
# from graia.ariadne.model import Group, Member
# from graia.ariadne.message.element import Plain, Image
# from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, SpacePolicy
#
# from local_secret_config import CHATGPT_CONFIG
# from loguru import logger
# from collections import defaultdict
# from revChatGPT.revChatGPT import AsyncChatbot as Chatbot
# import re
# import time
# from loguru import logger
#
# # 插件信息
# __name__ = "chatGPTClient"
# __description__ = "与chatGPT进行对话"
# __author__ = "orenji"
# __usage__ = "自动使用"
#
# saya = Saya.current()
# channel = Channel.current()
#
# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法: {__usage__}")
# channel.author(__author__)
#
# #api实例池
# conversation_pool = defaultdict(lambda:Chatbot(CHATGPT_CONFIG, conversation_id=None))
# #计时器池。每一小时需要刷新token。
# timer_pool = defaultdict(lambda:time.time())
# chat_cmd_pattern = re.compile(r'^/chat .+')
#
#
# @channel.use(ListenerSchema(listening_events=[GroupMessage]))
# async def group_message_listener(
#     app: Ariadne,
#     sender: Member,
#     message: MessageChain,
#     group: Group
# ):
#     text = message.display
#     if re.match(chat_cmd_pattern, text) == None:
#         return
#     prompt = text.split("/chat ")[1]
#     # api实例
#     chatbot = conversation_pool[sender.id]
#     # 若从未使用过api实例或token过期则刷新token
#     if sender.id not in timer_pool.keys() or time.time() - timer_pool[sender.id] >= 3500:
#         chatbot.refresh_session()
#         logger.warning("chatbot session token for {} refreshed!".format(sender.id))
#     # 用户手动重置上下文
#     if prompt == "reset":
#         chatbot.reset_chat()
#         return
#     response = await chatbot.get_chat_response(prompt)
#     timer_pool[sender.id] = time.time()
#     message = response["message"]
#     logger.warning(response)
#     if message:
#         await app.send_group_message(group, MessageChain.create([Plain("Q:"+prompt+"\nA:"+message)]))