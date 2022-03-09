# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, At
from graia.ariadne.model import Group, Member

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# nlp model
import torch
from transformers import BertTokenizer, AutoModelForMaskedLM
from torch.nn.functional import softmax

dataset_file = "assets/dataset.txt"
dict_file = "assets/dict.txt"


# tokenizer
tokenizer_path = 'bert-base-chinese'
tokenizer = BertTokenizer.from_pretrained(tokenizer_path)
with open(dict_file, "r") as f:
    tokenizer._add_tokens(f.readline().rstrip())
_dict = tokenizer.vocab
chars = {"0":"的","1":"地","2":"得"}
char_ids = {tokenizer.convert_tokens_to_ids(c) for c in chars}

# model
model_path = 'models/finetuned_bert_chinese_large_7.pt'
model = AutoModelForMaskedLM.from_pretrained(model_path)


# 插件信息
__name__ = "的地得小警察"
__description__ = "检查群消息里的的地得是否正确"
__author__ = "Orenji"
__usage__ = "自动被调用"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def group_message_listener(
    app: Ariadne,
    message: MessageChain,
    sender: Member,
    group: Group
):
    text = message.asDisplay()

    indices = set()
    for idx, c in enumerate(text):
        if c in chars.values(): indices.add(idx)
    if indices:
        with open(dataset_file, "a") as f:
            f.write(text + "\n")
        # idx = min(list(indices))
        # old_char = text[idx]
        # rst = []
        #
        # check = list(text)
        # check[idx] = '[MASK]'
        # check = "".join(check)
        # print(check)
        # maskpos = tokenizer.encode(check, add_special_tokens=True).index(103)
        #
        # input_ids = torch.tensor(tokenizer.encode(check, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        # outputs = model(input_ids, labels=input_ids)
        # _, prediction_scores = outputs[:2]
        # logit_prob = softmax(prediction_scores[0, maskpos], dim=-1).data.tolist()
        # for c in chars.values():
        #     rst.append((c, logit_prob[_dict[c]]))
        # rst.sort(key=lambda x: x[1], reverse=True)
        # print(rst)
        # if old_char != rst[0][0]:
        #     await app.sendGroupMessage(group, MessageChain.create([At(target=sender.id), Plain(" {}->{}".format(old_char, rst[0][0]))]))
