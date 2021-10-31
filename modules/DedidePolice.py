from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import At, Plain, Image
import torch
import jieba
from transformers import BertTokenizer, AlbertForMaskedLM
from torch.nn.functional import softmax

dataset_file = "assets/dataset.txt"
dict_file = "assets/dict.txt"

# jieba
jieba.load_userdict(dict_file)


pretrained = 'voidful/albert_chinese_large'
tokenizer = BertTokenizer.from_pretrained(pretrained)
model = AlbertForMaskedLM.from_pretrained(pretrained)
_dict = tokenizer.vocab
chars = ["的", "地", "得"]
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
    app: GraiaMiraiApplication,
    message: MessageChain,
    sender: Member,
    group: Group
):
    text = message.asDisplay()

    indices = set()
    for c in chars:
        try:
            indices.add(text.index(c))
        except:
            pass
    if indices:
        segs = jieba.cut(text)
        single_char_indices = set()
        cur = 0
        for seg in segs:
            if len(seg) == 1:
                single_char_indices.add(cur)
            cur += len(seg)

        check_indices = single_char_indices & indices

        print(check_indices, single_char_indices, indices)

        if check_indices:
            # 记录下该句到数据库
            with open(dataset_file, "a") as f: f.write(text + "\n")
            idx = min(list(check_indices))
            old_char = text[idx]
            rst = []

            check = list(text)
            check[idx] = '[MASK]'
            check = "".join(check)

            maskpos = tokenizer.encode(check, add_special_tokens=True).index(103)

            input_ids = torch.tensor(tokenizer.encode(check, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
            outputs = model(input_ids, labels = input_ids)
            _, prediction_scores = outputs[:2]
            logit_prob = softmax(prediction_scores[0, maskpos],dim=-1).data.tolist()
            for c in chars:
                rst.append((c, logit_prob[_dict[c]]))
            rst.sort(key=lambda x: x[1], reverse=True)
            if old_char != rst[0][0]:
                await app.sendGroupMessage(group, MessageChain.create([At(target=sender.id), Plain(" {}->{}".format(old_char, rst[0][0]))]))
