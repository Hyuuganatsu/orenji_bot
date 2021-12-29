# orenji_bot

本仓库为量产型🍊的代码仓库。功能使用了[Mirai](https://github.com/mamoe/mirai)、[graia](https://github.com/GraiaProject/Application)等框架实现。

## 功能
1. 的地得小警察 `modules/DedidePolice.py`：检测群消息中误用的“的地得”，并发消息at该群友提出修改方案。
- 主要使用`AlbertForMaskedLM`模型的预测来判断使用是否正确。例如：消息`香的一匹`（`的`用错，应为`得`）会被处理为`香[MASK]一匹`后输入`AlbertForMaskedLM`，经过计算后取`[MASK]`位置的probability distribution中的地得三个字的概率`{'的':0.1, '得':0.7, '地':0.05}`，比较最高概率de是否与输入中的de一致。因概率最高者为`得`，所以小警察会发送群消息`@群友 的->得`。相关库与框架：[pytorch](https://github.com/pytorch/pytorch), [transformers](https://github.com/huggingface/transformers), [albert_zh](https://github.com/brightmart/albert_zh).
- 2021-12-29更新：标注了所有数据，平衡后的数据集共1200条。改用bert-base-chinese代替albert，精度为93.81%。已将该模型更新部署到服务器。
- 2021-12-28更新：清洗+标注了1700条从群聊中收集的数据并finetune了模型。raw分布：的:地:得=1400:86:219，`的`占总数据的82%。从中以大约1:0.5:1的比例采样了500条作为dataset。预训练权重加载自huggface/albert_chinese_large，finetune共50epoch。eval set比例为10%，最终acc为90.91%。~~已将该模型更新部署到服务器。~~
- `为什么不公开数据集？`因为是从群内收集，含群友隐私。未来对数据脱敏处理后有可能公开。
- ~~[jieba](https://github.com/fxsjy/jieba)~~分词用于判断哪~~些的地得是单独的字。存在于词组中的的地得不属于检测范畴。本项目使用jieba的自定义词典来屏蔽成语（如`众矢之的`）和容易引起混淆的常用词（如`的卢马`、`的地得`）。~~

2. diss群友 `modules/cai.py`：使用随机语句diss群友。
- 例：`/cai test ==> 这个test也太逊了`

## 如何部署
因为🍊太懒，这部分还没有写。

## 特别鸣谢
感谢[sinceL](https://github.com/vayske)以及他的[Rumina](https://github.com/vayske/Rumina)对本项目部署以及代码编写的帮助！
