# python
import datetime
import re
import magic
import base64
import aiohttp
import hashlib
#import cv2
#import numpy

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote, Plain, At, Forward, ForwardNode
from graia.ariadne.message.parser.base import DetectPrefix, DetectSuffix
from graia.ariadne.model import Group, Member
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch, FullMatch, ElementMatch, ParamMatch, \
    RegexResult, SpacePolicy, ResultValue
from loguru import logger
from config.config import ACCOUNT

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from config.config import BACKEND_URL
from utils.utils import get_image_bytes_from_msg_id, clear_local_q_and_append_Image, setu_detect_buffer, clear_local_q
from config.module_config import check_module_enabled


add_setu_cmd_pattern = re.compile(r'^(@\d+ )?好(死)?$')
delete_setu_cmd_pattern = re.compile(r'^(@\d+ )?一般$')
hao_exact_cmd_pattern = re.compile(r'^好$')

# 插件信息
__name__ = "setu_client"
__description__ = "和backend的数据库交互，实现存取色图"
__author__ = "Orenji"
__usage__ = "在群里发setu即可从数据库随机取一张色图"

saya = Saya.current()
channel = Channel.current()

# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法：{__usage__}")
# channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
@check_module_enabled("setu_client")
async def buffer_image_listener(
    message: MessageChain,
        group: Group
):
    # monitoring images. setu_detect_buffer will always have the latest image of that group.
    if Image in message:
        await clear_local_q_and_append_Image(message.get_first(Image), group)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([RegexMatch(r'^好$')])]))
@check_module_enabled("setu_client")
async def add_setu_by_buffer_listener(
    app: Ariadne,
    group: Group,
    event: MessageEvent
):
    logger.warning("收到添加")

    # if quote in event, give this job to add_setu_by_quote_listener
    if event.quote: return

    # get setu queue for this group
    q = setu_detect_buffer[group.id]
    if q:
        image_bytes = await q[0].get_bytes()
        # try to add setu to backend db
        try:
            return_msg = await add_image_bytes_to_backend_db(image_bytes, False)
            if return_msg: await app.send_group_message(group, MessageChain([Plain(return_msg)]))
        except Exception as e:  # if the image is broken(no url and no base64), return
            logger.warning("尝试添加色图到数据库失败，", e)
        q.popleft()
        logger.info("尝试添加到数据库，因为有人跟了好。群:{}({})".format(group.name, group.id))



@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([ElementMatch(At,optional=True),
                                                                                           RegexMatch(r'好(死)?')])]))
@check_module_enabled("setu_client")
async def add_setu_by_quote_listener(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    event: MessageEvent
):
    logger.warning("收到添加，检查是否有quote")
    if not event.quote: return
    logger.warning("有quote")

    # fetch the reply object
    quote = event.quote

    # fetch the original message that the reply refers to. The given api quote.origin can fetch the original messageChain, but the Image inside is transcoded to Plain text (we can't get the original image this way).
    image_bytes = await get_image_bytes_from_msg_id(app, quote.id)

    # try to add setu to backend db
    try:
        force_add_flag = True if message.display.__contains__("好死") else False
        return_msg = await add_image_bytes_to_backend_db(image_bytes, force_add_flag)
        if return_msg: await app.send_group_message(group, MessageChain([Plain(return_msg)]))
    except Exception as e:  # if the image is broken(no url and no base64), return
        logger.warning("通过回复色图好或好死添加到数据库失败，", e)
    logger.info("尝试添加到数据库，因为有人回复了好。群:{}({})".format(group.name, group.id))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([ElementMatch(At,optional=True),
                                                                                           FullMatch("一般")])]))
@check_module_enabled("setu_client")
async def delete_setu_by_quote_listener(
        app: Ariadne,
        group: Group,
        event: MessageEvent
):
    #logger.warning("收到删除，检查是否有quote")
    if not event.quote: return
    #logger.warning("有quote")
    quote = event.quote
    image_bytes = await get_image_bytes_from_msg_id(app, quote.id)
    #logger.warning("取得删除图片的bytes")
    logger.info("尝试从数据库删除该色图")
    try:
        return_msg = await delete_image_bytes_from_backend_db(image_bytes)
        if return_msg: await app.send_group_message(group, MessageChain([Plain(return_msg)]))
    except Exception as e:  # if the image is broken(no url and no base64), return
        logger.warning("尝试从数据库删除该色图失败，", e)



@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("setu")])]))
@check_module_enabled("setu_client")
async def get_random_setu_from_db_listener(
    app: Ariadne,
    group: Group,
):

    logger.info("正获取随机色图")
    async with aiohttp.ClientSession() as session:
        async with session.get(BACKEND_URL+"api/setu/get-random") as response:
            image_bytes = await response.read()
            # print("正在修改左上角像素")
            # img_buffer_numpy = numpy.frombuffer(image_bytes, dtype=numpy.uint8)  # 将 图片字节码bytes  转换成一维的numpy数组 到缓存中
            # frame = cv2.imdecode(img_buffer_numpy, 1)
            # old_pixel = frame[0, 0]
            # frame[0, 0] = ((old_pixel[0]+1)%256, (old_pixel[1]+1)%256, (old_pixel[2]+1)%256)
            # output_io = io.BytesIO()
            # image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
            logger.info("正在发回")
            await app.send_group_message(group, MessageChain([Image(base64=base64.b64encode(image_bytes).decode('UTF-8'))]))
            await clear_local_q(group)

@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("setu").space(SpacePolicy.FORCE),
                                                                                           "text" @ RegexMatch(r".+")])]))
@check_module_enabled("setu_client")
async def query_setu_by_text_from_db_listener(
    app: Ariadne,
    group: Group,
    text: MessageChain = ResultValue()
):
    text = text.display
    logger.info(text)
    async with aiohttp.ClientSession() as session:
        async with session.post(BACKEND_URL + "api/engine/query", json={"text": text}) as response:
            data = await response.json()
            images = data.get("images", None)
            logger.info("got image")
            if not images:
                await app.send_group_message(group, MessageChain([Plain("没有符合的图片~")]))
                return
            for image_str in images:
                await app.send_group_message(group, MessageChain([Image(base64=image_str)]))

@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([
    # pattern like "@12768888 2x" is a sr command
    ElementMatch(At, optional=True),
    FullMatch('sim'),
    "count" @ ParamMatch(optional=True)
])]))
@check_module_enabled("setu_client")
async def query_setu_by_image_from_db_listener(
    app: Ariadne,
    group: Group,
    event: MessageEvent,
    count: RegexResult
):
    # fetch the reply object
    if not event.quote: return

    # fetch the original message that the reply refers to. The given api quote.origin can fetch the original messageChain, but the Image inside is transcoded to Plain text (we can't get the original image this way).
    image_bytes = await get_image_bytes_from_msg_id(app, event.quote.id)
    payload = {"image_str": base64.b64encode(image_bytes).decode('UTF-8')}
    if count.matched: payload["count"] = min(int(count.result.display), 5)

    async with aiohttp.ClientSession() as session:
        async with session.post(BACKEND_URL + "api/engine/query", json=payload) as response:
            data = await response.json()
            images = data.get("images", None)
            logger.info("got {} images".format(len(images)))
            if not images:
                await app.send_group_message(group, MessageChain([Plain("没有符合的图片~")]))
            elif len(images) == 1:
                await app.send_group_message(group, MessageChain([Image(base64=images[0])]))
            else:
                message = MessageChain([Image(base64=image_str) for image_str in images])
                logger.warning(message)
                await app.send_group_message(group, Forward([ForwardNode(target=ACCOUNT, message=message, time=datetime.datetime.now(), name="量产型🍊")]))



##
## http handlers
##

# add setu handler
async def add_image_bytes_to_backend_db(image_bytes:bytes, force:bool):
    async with aiohttp.ClientSession() as session:
        async with session.post(BACKEND_URL + "api/setu/add", data={"setu": image_bytes, "mime": magic.from_buffer(image_bytes).split()[0], "force":str(int(force))}) as response:
            if response.status == 204:
                logger.info("成功加入数据库")
                return "好死" if force else "好"
            elif response.status == 400:
                logger.info("已经添加过该图片")
                return "好过了"
            elif response.status == 418:
                logger.info("后端拒绝该图")
                #return "一般"
            elif response.status == 404:
                logger.info("请求中不包含setu文件")
            else:
                logger.info("backend internal error")
            return

# delete setu handler
async def delete_image_bytes_from_backend_db(image_bytes):
    img_sha = hashlib.sha256(image_bytes).hexdigest()
    async with aiohttp.ClientSession() as session:
        async with session.delete(BACKEND_URL + "api/setu/delete/"+img_sha) as response:
            if response.status == 404:
                logger.info("数据库中不存在该图")
            elif response.status == 400:
                logger.info("表项已删除，但硬盘上本来就不存在该图")
            elif response.status == 204:
                logger.info("成功删除")
                return "确实一般"
            else:
                logger.info("backend internal error")
            return
