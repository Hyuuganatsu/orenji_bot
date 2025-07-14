# python
from random import choice, random
from string import Template
from datetime import datetime

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ParamMatch, RegexResult, ForceResult, SpacePolicy
from graia.ariadne.model import Group, Member
from loguru import logger


# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# module config
from config.module_config import check_module_enabled


CAI_TEMPLATE_STRINGS = [
    '${name}是真的不行',
    '这个${name}真的太逊了',
    '菜${name}',
    '${name}好菜',
    '${name}太菜了',
    '没用的${name}',
    '废物${name}',
    '嫌弃${name}',
    '笨蛋${name}',
    '${name}好笨',
    '${name}太笨了',
]

bakas = [Template(str) for str in CAI_TEMPLATE_STRINGS]


# 插件信息
__name__ = "cai"
__description__ = "cai"
__author__ = "Orenji"
__usage__ = "自动被调用"

saya = Saya.current()
channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法：{__usage__}")
# channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("/cai"),
                                                                                           ParamMatch(optional=True) @ "diss_target"])]))
@check_module_enabled("cai")
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
        msg = '还骂别人呢，' + baka_template.substitute(name=sender.name)
    elif not name:
        # 如果未指定目标，则随机diss活跃用户
        member_list = await app.get_member_list(group)
        # 过滤7天内发言的用户
        active_member_list = [
            member for member in member_list if member.last_speak_timestamp >= datetime.now().timestamp() - 7 * 24 * 3600]
        random_diss_target = choice(active_member_list)
        msg = baka_template.substitute(name=random_diss_target.name)
    else:
        msg = baka_template.substitute(name=name)
    await app.send_group_message(group, MessageChain(Plain(msg)))

