# python
import aiohttp

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from loguru import logger
from .utils import clear_local_q_and_append_Image
from config import TWITTER_BEARER_KEY


# 插件信息
__name__ = "TwitterDispatcher"
__description__ = "推特链接解析"
__author__ = "SinceL"
__usage__ = "自动使用"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法: {__usage__}")
channel.author(__author__)

bearer_token = TWITTER_BEARER_KEY
header = {'Authorization': f'Bearer {bearer_token}', 'User-Agent': 'v2TweetLookupPython'}

def generateApi(url: str):
    token = url.split('status/')[-1]
    tid = token.split('?')[0]
    return f'https://api.twitter.com/2/tweets?ids={tid}&tweet.fields&expansions=attachments.media_keys,author_id&media.fields=url,preview_image_url&user.fields=name'


check_link: Twilight = Twilight(
    [
        RegexMatch(r'https://twitter.com/.*')
    ]
)
@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[check_link]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    group: Group
):
    if group.id != 954642206:
        url = message.display
        msg = []
        img_list = []
        logger.info(f'Receive Twitter URL: {url}')
        api = generateApi(url)
        session = aiohttp.ClientSession()
        async with session.get(api, headers=header) as response:
            data = await response.json()
            if 'data' in data:
                text = data['data'][0]['text']
                account = data['includes']['users'][0]['username']
                name = data['includes']['users'][0]['name']
                msg.append(Plain(f'{name}@{account}:\n{text}'))
                if 'media' in data['includes']:
                    for media in data['includes']['media']:
                        if media['type'] == 'photo':
                            img = Image(url=media['url'])
                            msg.append(img)
                            img_list.append(img)
                        else:
                            msg.append(Image(url=media['preview_image_url']))
        await session.close()
        if len(msg) > 0:
            await app.send_group_message(group, MessageChain(msg))
            if img_list:
                await clear_local_q_and_append_Image(img_list[0], group)