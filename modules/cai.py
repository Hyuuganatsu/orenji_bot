# python
from random import choice, random
from string import Template

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.model import Group, Member

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema


bakas = [Template('${name}小老弟行不行啊'), Template('这个${name}真的太逊了'), Template('菜${name}'), Template('${name}好菜'), Template('${name}太菜了'),
         Template('没用的${name}'), Template('废物${name}'), Template('嫌弃${name}'), Template('笨蛋${name}'), Template('${name}好笨'),
         Template('${name}太笨了'), Template('猪鼻${name}'), Template('请把${name}送回它的垃圾箱')]


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


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[DetectPrefix('/cai ')]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    name = message.asDisplay().split(' ', 1)
    print(name)
    baka_template = choice(bakas)
    # 30%几率diss到自己
    if random() < 0.3:
        msg = '还骂别人呢 ' + baka_template.substitute(name=sender.name)
    elif name[1] != '':
        msg = baka_template.substitute(name=name[1])
    else:
        msg = baka_template.substitute(name="")
    await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))
