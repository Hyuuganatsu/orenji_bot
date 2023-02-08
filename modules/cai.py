# python
from random import choice, random
from string import Template

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ParamMatch, RegexResult, ForceResult
from graia.ariadne.model import Group, Member
from loguru import logger

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema


bakas = [Template('${name}小老弟行不行啊'), Template('这个${name}真的太逊了'), Template('逊馁，${name}'), Template('菜${name}'),
         Template('菜狗${name}'), Template('咸鱼 ${name} 咸鱼'), Template('嫌弃${name}'), Template('笨蛋${name}')]


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


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("/cai"),
                                                                                           ParamMatch() @ "diss_target"])]))
async def group_message_listener(
    app: Ariadne,
    sender: Member,
    group: Group,
    diss_target: RegexResult
):
    name = diss_target.result
    baka_template = choice(bakas)
    # 30%几率diss到自己
    if random() < 0.3:
        msg = '还骂别人呢 ' + baka_template.substitute(name=sender.name)
    else:
        msg = baka_template.substitute(name=name)
    await app.send_group_message(group, MessageChain(Plain(msg)))
