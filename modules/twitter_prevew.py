# python
import base64
import io
import os.path
import subprocess
import uuid
from functools import partial

import aiohttp
import PIL
import yt_dlp
import selenium.common.exceptions
from bs4 import BeautifulSoup

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.connection import CallMethod
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group
from graia.ariadne.message.element import Plain, Image, MultimediaElement, File
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from loguru import logger
from pydantic import Field
from config.module_config import check_module_enabled
from selenium.webdriver.remote.webelement import WebElement

from utils.utils import clear_local_q_and_append_Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from asyncio import sleep

from loguru import logger


# 插件信息
__name__ = "TwitterDispatcher"
__description__ = "推特链接解析"
__author__ = "SinceL+Orenji"
__usage__ = "自动使用"

saya = Saya.current()
channel = Channel.current()

check_link: Twilight = Twilight(
    [
        RegexMatch(r'https://(x|twitter).com/.*')
    ]
)

IMAGE_SIZE=["4096x4096", "large", "medium", "small"]

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--disable-gpu')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--disable-extensions')
options.add_argument('start-maximized')


driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
driver.get("https://twitter.com")
driver.add_cookie({"name": "auth_token", "value": "7e060e1d3a5155f7b6ef7f288392cce63b9f5ee4"})

@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[check_link]))
@check_module_enabled("twitter_prevew")
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    group: Group,
    source: Source
):
    twitter_url = message.display
    msg = []
    img_list = []
    logger.info(f'Resolving Twitter URL: {twitter_url}')
    video_data = None

    # resolve page
    driver.get(twitter_url)

    await sleep(3)

    # the main tweet
    article = driver.find_element(By.TAG_NAME, "article")

    # text + self media block + retweet block(may contains media)
    post = article.find_elements(By.CSS_SELECTOR, "div:first-child > div:first-child > div:nth-child(2) > div[data-testid=tweetText]") # if having multiple posts
    if not post:
        post = article.find_element(By.CSS_SELECTOR, "div:first-child > div:first-child > div:nth-child(3)") # single post

    try: # tweet may not have text (only image)
        # textual part of the post
        post_text = article.find_element(By.CSS_SELECTOR, "div[data-testid=tweetText]")
        text = get_element_text_with_emoji(post_text)

    except selenium.common.exceptions.NoSuchElementException:
        text = ""

    links = article.find_elements(By.TAG_NAME, 'a')
    poster_name, poster_id = links[1], links[2]
    msg.append(Plain(f'{get_element_text_with_emoji(poster_name)}{get_element_text_with_emoji(poster_id)}:\n{text}'))

    try:
        post_self_media = post.find_elements(By.CSS_SELECTOR, "div:first-child > img") # if post is article, structure is different
        if not post_self_media: # if post is normal post
            post_self_media = post.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:first-child > div:first-child").find_elements(By.CSS_SELECTOR, 'img.css-9pa8cd')

        # try to fetch image
        for image in post_self_media:
            if image.get_attribute("alt") == "": continue
            url = image.get_attribute("src")
            url = url[:url.rfind("=")]
            for size in IMAGE_SIZE:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url + "=" + size) as response:
                        if response.status != 404:
                            pil_image = PIL.Image.open(io.BytesIO(await response.read()))
                            rgb_image = pil_image.convert('RGB')
                            jpeg_image = io.BytesIO()
                            rgb_image.save(jpeg_image, format='JPEG')
                            image_obj = Image(base64=base64.b64encode(jpeg_image.getvalue()).decode("UTF-8"))
                            msg.append(image_obj)
                            img_list.append(image_obj)
                            break
    except selenium.common.exceptions.NoSuchElementException:
        pass

    # try to fetch video or gif
    try:
        post.find_element(By.TAG_NAME, "video")
        id = uuid.uuid4().__str__()
        video_filename = id + ".mp4"
        resized_video_filename = "resized_" + video_filename
        gif_filename = id + ".gif"

        download_options = {
            'format': 'bestvideo+bestaudio/best',  # Downloads best video and audio
            'outtmpl': video_filename,  # Template for output filename
            'merge_output_format': 'mp4'  # Ensures the output is in MP4 format
        }

        # if it's a gif, download video, convert to gif and send as Image
        try:
            post.find_element(By.XPATH, "//span[text()='GIF']")
            with yt_dlp.YoutubeDL(download_options) as ydl:
                ydl.download([post.find_element(By.TAG_NAME, "video").get_attribute("currentSrc")])
            ffmpeg_cmd = ['ffmpeg', '-i', video_filename, '-vf', 'loop=0', gif_filename]
            subprocess.run(ffmpeg_cmd, check=True)
            with open(gif_filename, 'rb') as gif_file:
                gif = Image(data_bytes=gif_file.read())
                msg.append(gif)
        except selenium.common.exceptions.NoSuchElementException:
            # if it's just a video, send as short video
            with yt_dlp.YoutubeDL(download_options) as ydl:
                ydl.download([twitter_url])

            # resize to square, padding with black
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_filename,
                '-vf', "scale='if(gt(iw,ih),1080,-2)':'if(gt(ih,iw),1080,-2)',pad=1080:1080:(ow-iw)/2:(oh-ih)/2",
                '-c:a', 'copy',
                resized_video_filename
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            # create thumbnail
            ffmpeg_cmd = ['ffmpeg', '-i', video_filename, '-ss', '00:00:00', '-vframes', '1', '-q:v', '2', gif_filename]
            subprocess.run(ffmpeg_cmd, check=True)

            with open(resized_video_filename, "rb") as video, open(gif_filename, "rb") as thumbnail:
                video_data = (base64.b64encode(video.read()).decode("UTF-8"), base64.b64encode(thumbnail.read()).decode("UTF-8"))

        # clean up downloaded video and gif
        for filename in [video_filename, gif_filename, resized_video_filename]:
            if os.path.exists(filename):
                os.remove(filename)

    except selenium.common.exceptions.NoSuchElementException:
        pass

    if len(msg) > 0:
        await app.send_group_message(group, MessageChain(msg))
        if video_data:
            await app.connection.call(
                "sendGroupMessage",
                CallMethod.POST,
                {
                    "target": int(group.id),
                    "messageChain": [
                        {"type": "ShortVideo", "base64": video_data[0], "thumbnailBase64": video_data[1]}
                    ]
                }
            )
        if img_list:
            await clear_local_q_and_append_Image(img_list[0], group)
        # try:
        #     await app.recall_message(source)
        # except PermissionError:
        #     logger.warning("没有足够权限撤回！")

def get_element_text_with_emoji(element: WebElement):
    # Get the inner HTML of the element
    html_content = element.get_attribute('innerHTML')

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Replace emoji <img> tags with their alt attribute
    for img in soup.find_all('img'):
        emoji = img.get('alt', '')  # Get the alt text, or use an empty string if not available
        img.replace_with(emoji)  # Replace the <img> tag with the emoji

    # Get the final text, now including emojis
    return soup.get_text()

# class ShortVideo(MultimediaElement):
#     """指示消息中的shipin元素"""
#
#     type = "ShortVideo"
#
#     id: Optional[str] = Field(None, alias="videoId")
#
#     def __init__(
#         self,
#         id: Optional[str] = None,
#         url: Optional[str] = None,
#         *,
#         path: Optional[Union[Path, str]] = None,
#         base64: Optional[str] = None,
#         data_bytes: Union[None, bytes, BytesIO] = None,
#         **kwargs,
#     ) -> None:
#         super().__init__(id=id, url=url, path=path, base64=base64, data_bytes=data_bytes, **kwargs)
#
#     # length: Optional[int]
#     # """语音长度"""
#
#     def __str__(self) -> str:
#         return "[shipin]"