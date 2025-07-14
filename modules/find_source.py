from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, At
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, ElementMatch, FullMatch
from graia.ariadne.util.saya import listen, dispatch
from collections import OrderedDict
from typing import Dict
import os
import json
from config.module_config import check_module_enabled

# --- 插件信息 --- #
__name__ = "FindSource"
__description__ = "source: 查询图片出处"
__author__ = "EndEdge"
__usage__ = "指令:\n" \
            "\tsource\n" \
            "使用例:\n" \
            "\t回复带有图片的消息\"source\""

channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}")
# channel.author(__author__)

# --- 初始化 --- #
message_cache: Dict[int, MessageChain] = {}

# forcing minsim to 80 is generally safe for complex images, but may miss some edge cases. If
# images being checked are primarily low detail, such as simple sketches on white paper, increase this to cut
# down on false positives.
minsim = '80!'

# every user's api_key has limit request number per hours and per day,
# you can add more api_keys to increase the number.
api_keys = ['7ff21baadbaf61c3fb2b987285ea7de0b234e861']
data_file = os.getcwd() + '/resources/saucenao_db_data.json'

def init_db_data():
    with open(data_file) as file:
        data = json.load(file)
    digit_str = ''
    for key, value in data.items():
        digit_str = str(value) + digit_str
    return int(digit_str, 2)


db_bitmask = init_db_data()

# --- 获取消息图片出处 --- #
@listen(GroupMessage)
@dispatch(
    Twilight(
        ElementMatch(At, optional=True),
        FullMatch('source')
    )
)
@check_module_enabled("find_source")
async def group_message_listener(
    app: Ariadne,
    event: GroupMessage,
    group: Group
):
    if event.quote:
        quote_id = event.quote.id
        # fetch the original message that the reply refers to. The given api quote.origin can fetch the original
        # messageChain, but the Image inside is transcoded to Plain text (we can't get the original image this way).
        original_event = await app.get_message_from_id(message=quote_id)
        if not original_event:
            return
        last_message = original_event.message_chain
    else:
        last_message = message_cache[group.id] if group.id in message_cache else None  # type: ignore
    if last_message:
        images = last_message.get(Image)
        for image in images:
            msg = await find_source(image.url)
            await app.send_group_message(group, MessageChain(msg))

# --- 缓存图片消息 --- #
@listen(GroupMessage)
@check_module_enabled("find_source")
async def cache_message(
    message: MessageChain,
    group: Group
):
    if message.has(Image):
        message_cache[group.id] = message

# --- 以图搜图 --- #
async def find_source(img):
    session = Ariadne.service.client_session
    for api_key in api_keys:
        api_url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim=' + minsim + '&dbmask=' + str(
            db_bitmask) + '&api_key=' + api_key
        async with session.post(api_url, params={'url': img}) as response:
            if response.status == 200:
                text = await response.text()
                break

    if not response or response.status != 200:
        if response and response.status == 403:
            return [Plain('无效请求，可能需要重新配置api key')]
        else:
            # generally non 200 statuses are due to either overloaded servers or the user is out of searches
            return [Plain('暂时超过搜索次数限制，请稍后再试')]

    results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(text)
    if int(results['header']['status']) != 0:
        return [Plain('API异常，请稍后再试')]

    if int(results['header']['results_returned']) == 0:
        return [Plain('暂时无法找到原图')]

    if float(results['results'][0]['header']['similarity']) < float(results['header']['minimum_similarity']):
        return [Plain('暂时无法找到原图')]

    thumbnail = results['results'][0]['header']['thumbnail']

    title = ''
    if 'title' in results['results'][0]['data']:
        title = results['results'][0]['data']['title']
    elif 'jp_name' in results['results'][0]['data'] and len(results['results'][0]['data']['jp_name']) != 0:
        title = results['results'][0]['data']['jp_name']
    elif 'eng_name' in results['results'][0]['data'] and len(results['results'][0]['data']['eng_name']) != 0:
        title = results['results'][0]['data']['eng_name']

    member_name = ''
    if 'member_name' in results['results'][0]['data']:
        member_name = results['results'][0]['data']['member_name']
    elif 'author_name' in results['results'][0]['data']:
        member_name = results['results'][0]['data']['author_name']
    elif 'creator_name' in results['results'][0]['data']:
        member_name = results['results'][0]['data']['creator_name']
    elif 'creator' in results['results'][0]['data']:
        member_name = results['results'][0]['data']['creator']
    elif 'user_name' in results['results'][0]['data']:
        member_name = results['results'][0]['data']['user_name']

    urls = []
    if 'ext_urls' in results['results'][0]['data']:
        urls = results['results'][0]['data']['ext_urls']

    if len(title) == 0 and len(member_name) == 0 and len(urls) == 0:
        return [Plain('暂时无法找到原图')]

    title = title + '\n' if len(title) > 0 else title
    member_name = member_name + '\n' if len(member_name) > 0 else member_name
    img_url = urls[0] if len(urls) > 0 else ''
    show_text = title + member_name + img_url

    return [Image(url=thumbnail), Plain(show_text)]