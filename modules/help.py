# python
import re

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ParamMatch, RegexResult
from graia.ariadne.model import Group, Member
from loguru import logger

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from config.config import APPLICABLE_RATE_TYPES
from config.module_config import check_module_enabled

detail_help_pattern = re.compile(r'^/help [^ ]+$')

general_help = '''以下为简要介绍。主动功能的详细介绍可使用/help [指令]来查看。

## 主动功能
 ## 在聊天框发送
    /help : 展示此帮助信息
    [已关闭] /gen [prompt] _[size(s,m,l)] : 从文字生成动漫图片或从图片+文字生成动漫图片
    /cai [文本] : 让bot diss某人
    /say [人物id] [日文文本] : 让人物说出对应文本，以语音发送
    /chat : 和chatGPT对话。
    /rate : 显示当前汇率。每天北京时间早上八点也会自动执行此指令。
    setu : 从setu库随机抽取一张setu
 ## 对带图片消息回复
    source : 查询图片出处
    sim : 对带图片的消息回复sim以查找setu库中类似的图
    2x : 对带图片的消息回复2x以超分辨率该图
    一般 : 从setu库中删去该图
    好 : 尝试将图片加入setu库

### 被动功能
预览视频网站链接(b站、油管)
预览推文链接'''
helps = {
"/gen": "[/gen] [prompt] [大小(p(ortrait),l(landscape))](可选，不选则是默认)。根据prompt生成动漫图片，生成一张默认m大小的图片大约需20秒。回复一条带图片的消息并使用则可以实现img2img。已默认包含masterpiece和best quality词条以及各种negative prompt。独轮车功能，计算很慢，请求太多可能会崩。portrait为512*768，默认为512*512，landscape为768*512。",
"/cai": "[/cai] [文本] : 让bot diss某人。bot有30%概率diss发起者。",
"/say": "[/say] [人物id] [日文文本] : 让人物说出对应文本，以语音发送。\n现有人物及对应id: {ナツメ:0, 栞那:1, 希:2, 愛衣:3, 涼音:4}\n标点符号会影响语气。",
"/chat": "[/chat] [聊天内容] : 和chatGPT聊天。可以使用中文、英文、日文等语言。每个账号有专属的对话上下文。使用/chat reset来开启一段新的对话（忘记上下文）。",
"/rate": "[/rate] : 显示当前100外币所等值的人民币，数据来源于BOC官网。已加入观察的货币有{}".format(APPLICABLE_RATE_TYPES),
"setu": "[setu] : 从个人维护的setu库随机抽取一张setu。有时发不出来。",
"sim": "[sim] : 对带图片的消息回复sim以查找setu库中类似的图。最多回复三张。图库中已有的图会被过滤掉。",
"source": "[source] : 对带图片的消息回复sim以查找出处。数据源来自saucenao",
"2x": "[2x]: 对带图片的消息回复2x以对该图进行ai超分辨率计算",
"一般": "[一般] : 尝试从setu库中删去该图。\n此指令必须回复某带图片的消息来生效。回复时无需删除 @用户名 部分。",
"好": "[好] : 尝试将该图加入setu库。\n非回复时，尝试将群消息中最后一张图片入库；回复\"好\"到某带图片的消息时，尝试将该消息中的第一张图片入库。回复时无需删除 @用户名 部分。\n若成功入库，bot也会回复\"好\"。"
}

# 插件信息
__name__ = "help"
__description__ = "show help info"
__author__ = "Orenji"
__usage__ = "type /help"

saya = Saya.current()
channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法：{__usage__}")
# channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("/help"),
                                                                                          "command" @ ParamMatch(optional=True)])]))
@check_module_enabled("help")
async def show_help_info_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group,
    command: RegexResult
):
    if not command.matched: # send general help info
        await app.send_group_message(group, MessageChain(Plain(general_help)))
    else:
        cmd = command.result.display
        logger.info("正查询{}的帮助".format(cmd))
        if cmd not in helps:
            await app.send_group_message(group, MessageChain(Plain("指令{}不存在。可查询的指令有: [/cai, /setu, /say, setu, 一般, 好]。".format(cmd))))
        else:
            await app.send_group_message(group, MessageChain(Plain(helps[cmd])))
