import torch
# import jieba
from transformers import BertTokenizer, AlbertForMaskedLM
from torch.nn.functional import softmax

dataset_file = "assets/dataset.txt"
dict_file = "assets/dict.txt"

# jieba
#jieba.load_userdict(dict_file)

# tokenizer
tokenizer_path = 'voidful/albert_chinese_large'
tokenizer = BertTokenizer.from_pretrained(tokenizer_path)
with open(dict_file, "r") as f:
    word = f.readline().rstrip()
    tokenizer._add_tokens(word)
_dict = tokenizer.vocab
chars = {"0":"的","1":"地","2":"得"}
char_ids = {tokenizer.convert_tokens_to_ids(c) for c in chars}
print(char_ids)

# model
model_path = 'models/finetuned_albert_chinese_large_49.pt'
model = AlbertForMaskedLM.from_pretrained(model_path)
while 1:
    text = input()
    indices = set()
    for idx, c in enumerate(text):
        if c in chars.values(): indices.add(idx)
    if indices:
        with open(dataset_file, "a") as f:
            f.write(text + "\n")
        idx = min(list(indices))
        old_char = text[idx]
        rst = []

        check = list(text)
        check[idx] = '[MASK]'
        check = "".join(check)
        print(check)
        maskpos = tokenizer.encode(check, add_special_tokens=True).index(103)

        input_ids = torch.tensor(tokenizer.encode(check, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        outputs = model(input_ids, labels=input_ids)
        _, prediction_scores = outputs[:2]
        logit_prob = softmax(prediction_scores[0, maskpos], dim=-1).data.tolist()
        for c in chars.values():
            rst.append((c, logit_prob[_dict[c]]))
        rst.sort(key=lambda x: x[1], reverse=True)
        print(rst)
        if old_char != rst[0][0]:
            print(" {}->{}".format(old_char, rst[0][0]))