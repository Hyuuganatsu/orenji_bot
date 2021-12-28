from torch.utils.data import Dataset
from configs import *
import torch

class pretrain_mlm_dataset(Dataset):
    # This dataset provide examples like: {"text_id: Tensor([102, 103, 104]), "target": Tensor([1, 2])}
    def __init__(self, a, b, c):
        self.texts, self.targets = a, b
        self.tokenizer = c

    def __getitem__(self, index):
        return {"text_id":self.tokenizer.encode(self.texts[index], add_special_tokens=True),
                "target":[self.tokenizer.convert_tokens_to_ids(c) for c in self.targets[index]],
                "index": index}

    def __len__(self):
        assert len(self.texts) == len(self.targets)
        return len(self.texts)

def collate(samples):
    inputs = [t["text_id"]for t in samples]
    targets = [t["target"] for t in samples]
    indices = [t["index"] for t in samples]

    max_size = max(len(t) for t in inputs)

    flatten_target = []

    for i in range(len(inputs)):
        mask_indices = [idx for idx in range(len(inputs[i])) if inputs[i][idx] == MASK_idx]
        inputs[i] = torch.LongTensor(inputs[i]+[PAD_idx]*(max_size-len(inputs[i])))

        maybe_target = torch.full(inputs[i].shape, fill_value=-100, dtype=torch.long)
        for idx in range(len(targets[i])):
            try:
                maybe_target[mask_indices[idx]] = targets[i][idx]
            except Exception as e:
                print(idx, indices)
        flatten_target.append(maybe_target)

    return torch.stack(inputs), torch.stack(flatten_target)
