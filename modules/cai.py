from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import At, Plain, Image
from random import choice

def FirstChar(message, string: str):
    if type(message.__root__[0]) is not Plain:
        return False
    return message.__root__[0].text.startswith(string)

# 插件信息
__name__ = "cai"
__description__ = "cai"
__author__ = "Orenji"
__usage__ = "自动被调用"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def group_message_listener(
    app: GraiaMiraiApplication,
    message: MessageChain,
    sender: Member,
    group: Group
):
    message = message.asSendable()
    if FirstChar(message, '/cai'):
        name = message.__root__[0].text.split(' ', 1)
        bakas = ['[$name$]小老弟行不行啊','这个[$name$]真的太逊了','菜[$name$]']
        baka = choice(bakas)
        name.append('')
        if name[1] != '':
            msg = baka.replace('[$name$]', name[1])
        else:
            msg = baka.replace('[$name$]', '')
        await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))
    elif FirstChar(message, '/yz'):
        await app.sendGroupMessage(group, MessageChain.create([At(951681820), Plain(" 鱼籽剧本写完了吗？")]))
