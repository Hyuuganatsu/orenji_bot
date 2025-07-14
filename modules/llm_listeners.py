# python
import aiohttp, re

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.ariadne.model import Group, Member
from loguru import logger

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# module config
from config.module_config import check_module_enabled
from config.config import OPENAI_API_KEY

# 插件信息
__name__ = "llm_listeners"
__description__ = "每条消息都会被发送给全部的llm_listeners，用于触发一些回复"
__author__ = "Orenji"
__usage__ = "自动被调用"

saya = Saya.current()
channel = Channel.current()

message_pattern = r"\x1b\[0m(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) V/Bot\.\d+: \[.*?\((\d+)\)\] (.*?)\((\d+)\) -> (.*?)\x1b\[0m\x1b\[m"
message_regex = re.compile(message_pattern)

quote_pattern = r"\[mirai:quote.*from (\d+).*content=([^]]+)\]"
quote_regex = re.compile(quote_pattern)

image_pattern = r"\[mirai:image.*isEmoji=(true|false)\]"
image_regex = re.compile(image_pattern)

at_pattern = r"\[mirai:at:(\d+)\]"
at_regex = re.compile(at_pattern)

app_msg_pattern = r".*\[mirai:app.*"
app_msg_regex = re.compile(app_msg_pattern)

marketplace_emoji_pattern = r".*\[mirai:marketface:.*"
marketplace_emoji_regex = re.compile(marketplace_emoji_pattern)

url_pattern = re.compile(
    r'(?:http|ftp)s?://'  # http:// or https:// or ftp:// or ftps://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

valid_summary_pattern = r"\[(\d+)\]"
valid_summary_regex = re.compile(valid_summary_pattern)

async def get_summarization_input(query_group_id: str):
    sender_id_to_recode_id = {}
    input = ""

    def refresh_map(sender_id: str):
        # add sender id to original id -> simplified id map, to reduce token input
        if sender_id not in sender_id_to_recode_id:
            sender_id_to_recode_id[sender_id] = len(sender_id_to_recode_id)

    with open("/mcl/log", "r") as file:
        lines = file.readlines()

        for line in lines[::-1]:
            if len(input) > 1500:
                break
            search = message_regex.search(line)
            if search:
                # Extracting the groups based on the regex pattern
                date_time = search.group(1)
                group_id = search.group(2)
                sender_nickname = search.group(3)
                sender_id = search.group(4)
                content = search.group(5)

                if group_id == query_group_id:# and datetime.datetime.now() - datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S') <= datetime.timedelta(hours=within):
                    refresh_map(sender_id)

                    # rewrite "at" format
                    at_matches = at_regex.findall(content)
                    for at_match in at_matches:
                        refresh_map(at_match)
                        content = re.sub(at_pattern, f"@{sender_id_to_recode_id[at_match]}", content)

                    # rewrite image or sticker content
                    while image_regex.search(content):
                        content = re.sub(image_pattern, "表情" if image_regex.search(content).group(1) == "true" else "图片", content)

                    # rewrite marketplace emoji
                    while marketplace_emoji_regex.search(content):
                        content = re.sub(marketplace_emoji_pattern, "官方表情", content)

                    # rewrite quote format
                    quote_matches = quote_regex.findall(content)
                    for quote_match in quote_matches:
                        refresh_map(quote_match[0])
                        content = re.sub(quote_pattern, f"&{sender_id_to_recode_id[quote_match[0]]} ", content)

                    # rewrite links
                    content = re.sub(url_pattern, "链接", content)

                    # remove all mirai:app sharing messages
                    if app_msg_regex.search(content):
                        continue

                    if content:
                        input = " ".join([str(sender_id_to_recode_id[sender_id]), content]) + "\n" + input
        # logger.info(sender_id_to_recode_id)
        return (input, sender_id_to_recode_id)

async def run_summarization_inference(input, ids_to_nickname: {str: str}):
    def repl(match):
        # Extract the captured group
        mapped_id = match.group(1)
        # Look up the captured group in the dictionary and return the replacement
        return "[" + ids_to_nickname[mapped_id] + "] "

    headers = {
        "Authorization": "Bearer " + OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    # payload = {
    #     "inputs": {"message": input},
    #     "response_mode": "blocking",
    #     "user": "orenji"
    # }
    payload = {
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "system",
        "content": "你将会接收群聊天记录，请总结其中的3个重要话题。聊天记录的格式是r\"id message\"。id是一个数字，是群成员的唯一标识符，你要记住它们具体代表的是谁。除了一般文字外，&id表示回复某人，@id表示提及某人。你要通过&和@搞清群员们对话的脉络，并且输出每个话题时必须使用[id]的格式来提及参与该话题的具体群员(不要使用[@id]或[&id])。必须要用上述方式提及具体群成员。直接输出话题，不要有引言和结束语。🍊橙子，七月，车神是群成员的昵称，请仔细分辨话题，不要把昵称和聊天内容混淆。"
      },
      {
        "role": "user",
        "content": input
      }
    ]
  }
    raw_summary = ""
    retry = 0
    while not raw_summary and retry < 5:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers,
                                    json=payload) as response:
                data = await response.json()
                # logger.info(data)
                summary = data["choices"][0]["message"]["content"]
                id_matches = valid_summary_regex.findall(summary)
                logger.info(summary)
                if id_matches:
                    raw_summary = re.sub(valid_summary_pattern, repl, summary)
                retry += 1
    return raw_summary


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Twilight([FullMatch("/sum")])]))
@check_module_enabled("llm_listeners")
async def summarize_chat_history_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group,
):
    if group.id == 303488479: # if it's bot_test
        target_group_id = str(249857359) # czz: 249857359, tomcat: 954642206
    else:
        target_group_id = str(group.id)

    # get inference input
    (input, sender_id_to_recode_id) = await get_summarization_input(target_group_id)

    # get nickname for group members whose nicknames are unknown
    recode_id_to_nickname = {str: str}
    for sender_id, recoded_id in sender_id_to_recode_id.items():
        member = await app.get_member(int(target_group_id), int(sender_id))
        recode_id_to_nickname[str(recoded_id)] = member.name

    summary = await run_summarization_inference(input, recode_id_to_nickname)
    if summary:
        await app.send_group_message(group, MessageChain([Plain(summary)]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
@check_module_enabled("llm_listeners")
async def gn_message_distinguisher_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group,
):
    # if not group.id in [249857359, 303488479]:
    return

    headers = {
        "Authorization": "Bearer app-L07GLQYMwSr9TtVumyKWjyQQ",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {"message": message.display},
        "response_mode": "blocking",
        "user": sender.id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("http://192.168.10.110:81/v1/workflows/run", headers=headers, json=payload) as response:
            data = await response.json()
            logger.info(data)
            if data["data"]["outputs"]["result"] == "gn":
                await app.send_group_message(group, MessageChain([Plain("gn")]))



