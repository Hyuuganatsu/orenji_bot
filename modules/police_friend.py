# from graia.saya import Saya, Channel
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.application import GraiaMiraiApplication
# from graia.application.event.messages import *
# from graia.application.event.mirai import *
# from graia.application.message.elements.internal import At, Plain, Image
# import torch
# from transformers import BertTokenizer, AlbertForMaskedLM
# from torch.nn.functional import softmax
# from .DedidePolice import model, tokenizer
#
# pretrained = 'voidful/albert_chinese_large'
# #tokenizer = BertTokenizer.from_pretrained(pretrained)
# #model = AlbertForMaskedLM.from_pretrained(pretrained)
# _dict = tokenizer.vocab
# chars = ["的", "地", "得"]
# # 插件信息
# __name__ = "的地得小警察1"
# __description__ = "检查群消息里的的地得是否正确1"
# __author__ = "Orenji1"
# __usage__ = "自动被调用1"
#
# saya = Saya.current()
# channel = Channel.current()
#
# channel.name(__name__)
# channel.description(f"{__description__}\n使用方法：{__usage__}")
# channel.author(__author__)
#
#
# @channel.use(ListenerSchema(listening_events=[FriendMessage]))
# async def group_message_listener(
#         app: GraiaMiraiApplication,
#         message: MessageChain,
#         sender: Friend,
# ):
#     text = message.asDisplay()
#
#     indices = []
#     for c in chars:
#         try:
#             indices.append(text.index(c))
#         except:
#             pass
#     indices.sort()
#     if indices:
#         idx = min(indices)
#         old_char = text[idx]
#         rst = []
#
#         check = list(text)
#         check[idx] = '[MASK]'
#         check = "".join(check)
#
#         maskpos = tokenizer.encode(check, add_special_tokens=True).index(103)
#
#         input_ids = torch.tensor(tokenizer.encode(check, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
#         outputs = model(input_ids, labels = input_ids)
#         _, prediction_scores = outputs[:2]
#         logit_prob = softmax(prediction_scores[0, maskpos],dim=-1).data.tolist()
#         for c in chars:
#             rst.append((c, logit_prob[_dict[c]]))
#         rst.sort(key=lambda x: x[1], reverse=True)
#         if old_char != rst[0][0]:
#             print(sender.id)
#             await app.sendFriendMessage(sender, MessageChain.create([Plain("{}->{}".format(old_char, rst[0][0]))]))