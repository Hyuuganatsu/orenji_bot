# python
import bs4
import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Plain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.ariadne.model import Group

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# scheduler
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

# project
from config import APPLICABLE_RATE_TYPES

# 插件信息
__name__ = "exchange rate reminder"
__description__ = "每天定时发送汇率信息到群里"
__author__ = "Orenji"
__usage__ = "自动被调用"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(SchedulerSchema(timers.crontabify("0 0 * * * 0"))) # Beijing time 08h:00m
@channel.use(SchedulerSchema(timers.crontabify("00 10 * * * 0"))) # Beijing Time 18h:00m
async def automatic_rate_reminder(app: Ariadne):

    #await app.send_group_message(303488479, MessageChain(Plain(await get_rate_str()))) # bot_test
    await app.send_group_message(249857359, MessageChain(Plain(await get_rate_str()))) # 创作组
    await app.send_group_message(954642206, MessageChain(Plain(await get_rate_str())))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("/rate")])]))
async def active_get_rate_listener(
    app: Ariadne,
    group: Group
):
    await app.send_group_message(group.id, MessageChain(Plain(await get_rate_str())))


# get rate info from BOC website
async def get_rate_str() -> str:
    msg = "这是今天的汇率喵~\n================\n"#"  货币\t \t中间价\n"
    update_time = ""
    session = aiohttp.ClientSession()
    async with session.get("https://www.boc.cn/sourcedb/whpj/enindex_1619.html") as response:
        soup = bs4.BeautifulSoup(await response.content.read())
        table = soup.find_all("table")[7]
        for tr in table("tr"):
            if not tr.td: continue
            currency_type = tr.td.string
            if currency_type in APPLICABLE_RATE_TYPES.keys():
                msg += "{}\t\t{}\n".format(APPLICABLE_RATE_TYPES[currency_type],tr("td")[5].string)
                update_time = tr("td")[6].string
    await session.close()
    msg += "================\n" + update_time
    return msg