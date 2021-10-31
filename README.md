# orenji_bot

本仓库为量产型的代码仓库。功能使用了[Mirai](https://github.com/mamoe/mirai)、[graia](https://github.com/GraiaProject/Application)等框架实现。

## 功能
1. 的地得小警察 `modules/DedidePolice.py`：检测群消息中误用的“的地得”，并发消息at该群友提出修改方案。
- 主要使用`AlbertForMaskedLM`模型的预测来判断使用是否正确。例如：消息`香的一匹`（`的`用错，应为`得`）会被处理为`香[MASK]一匹`后输入`AlbertForMaskedLM`，经过计算后取`[MASK]`位置的probability distribution中的地得三个字的概率`{'的':0.1, '得':0.7, '地':0.05}`，比较最高概率de是否与输入中的de一致。因概率最高者为`得`，所以小警察会发送群消息`@群友 的->得`。相关库与框架：[pytorch](https://github.com/pytorch/pytorch), [transformers](https://github.com/huggingface/transformers), [albert_zh](https://github.com/brightmart/albert_zh).
- [jieba](https://github.com/fxsjy/jieba)分词用于判断哪些的地得是单独的字。存在于词组中的的地得不属于检测范畴。本项目使用jieba的自定义词典来屏蔽成语（如`众矢之的`）和容易引起混淆的常用词（如`的卢马`、`的地得`）。

2. diss群友 `modules/cai.py`：使用随机语句diss群友。
- 例：`/cai test ==> 这个test也太逊了`

## 特别鸣谢
感谢[sinceL](https://github.com/vayske)以及他的[Rumina](https://github.com/vayske/Rumina)对本项目部署以及代码编写的帮助！
