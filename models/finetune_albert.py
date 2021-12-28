import math
import torch
from torch.nn.functional import softmax

from configs import *
from torch.utils.data import DataLoader
from transformers import AlbertForMaskedLM, AutoTokenizer, Trainer
from custom_dataset import pretrain_mlm_dataset, collate


# prepare tokenizer
tokenizer = AutoTokenizer.from_pretrained(pretrained)
print([tokenizer.convert_tokens_to_ids(c) for c in ("的","地","得")])

# prepare model
model = AlbertForMaskedLM.from_pretrained(pretrained)
model = model.to(DEVICE)

# prepare dataset and dataloader
texts, targets = [], []
with open(DATASET_path, "r") as f:
    lines = f.readlines()
    for line in lines:
        texts.append(line.split("<s>")[1].split("</s>")[0])
        targets.append(line.split("<de>")[1].split("</de>")[0])
dataset_size = len(texts)
print("found {} examples in dataset.".format(dataset_size))
train_len = math.floor(len(texts)*0.9)

train_dataset = pretrain_mlm_dataset(texts[:train_len], targets[:train_len], tokenizer)
eval_dataset = pretrain_mlm_dataset(texts[train_len:], targets[train_len:], tokenizer)
print("train dataset has {} batches, eval dataset has {} batches.".format(train_len//BATCH_SIZE, (dataset_size-train_len)//BATCH_SIZE))

train_loader = DataLoader(train_dataset,BATCH_SIZE,False,collate_fn=collate)
eval_loader = DataLoader(eval_dataset,BATCH_SIZE,False,collate_fn=collate)

# prepare optimizer
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

# prepare lr scheduler
lr_scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, DECAY, -1)


def evaluate():
    # Evaluate
    tf, count = 0, 0
    for i, (input_ids, target_map) in enumerate(eval_loader):
        input_ids = input_ids.to(DEVICE)
        target_map = target_map.to(DEVICE)
        outputs = model(input_ids, labels=target_map)
        _, prediction_scores = outputs[:2]

        output_scores = prediction_scores[target_map != -100]
        logit_prob = softmax(output_scores, dim=-1)

        predicted_ids = torch.argmax(logit_prob, dim=-1)
        target_ids = target_map[target_map != -100]
        n = target_ids.shape[0]
        tf += sum(predicted_ids == target_ids)
        count += n
    return "evaluation accuracy: ", round(float(tf / count), 4)

def save(epoch):
    model.save_pretrained(f"models/finetuned_albert_chinese_large_{epoch}.pt")
    #torch.save()

# Train
eval_result = []
for e in range(EPOCH):
    for i, (input_ids, target_map) in enumerate(train_loader):
        input_ids = input_ids.to(DEVICE)
        target_map = target_map.to(DEVICE)

        outputs = model(input_ids,labels=target_map)
        loss = outputs[0]
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print("Epoch {} step {}, loss={}".format(e, i, loss.data))
    lr_scheduler.step()
    eval_result.append(evaluate())
    save(e)

for line in eval_result:
    print(line)
#torch.save(model, "models/finetuned_albert_chinese_large.pt")




# text = "你是我[MASK]"
# maskpos = tokenizer.encode(text, add_special_tokens=True).index(MASK_idx)
# print(tokenizer.encode(text, add_special_tokens=True))
# print(tokenizer(text, return_tensors="pt"))

