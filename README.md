# orenji_bot

本仓库为量产型🍊的代码仓库。功能使用了[Mirai](https://github.com/mamoe/mirai)、[Graia](https://github.com/GraiaProject/)等框架实现。

## 更新内容
- 2022-3-2更新：
  - 更新了graia相关库，现在为[graia-saya](https://github.com/GraiaProject/Saya)管理module，[graia-ariadne](https://github.com/GraiaProject/Ariadne/)作为主框架。
  - 增加了新功能：`图片超分辨率(2x super resolution)`。在群里回复一条带图片的消息并输入“2x”即可调用此功能。此功能依赖我的超分辨率http服务：[sr-orenji](http://sr-orenji.ml:6990/)(具体请见此仓库 edit later)。
- 2021-12-29更新：
  - 标注了所有数据，平衡后的数据集共1200条。改用bert-base-chinese代替albert，精度为93.81%。已将该模型更新部署到服务器。
- 2021-12-28更新：
  - 清洗+标注了1700条从群聊中收集的数据并finetune了模型。raw分布：的:地:得=1400:86:219，`的`占总数据的82%。从中以大约1:0.5:1的比例采样了500条作为dataset。预训练权重加载自huggface/albert_chinese_large，finetune共50epoch。eval set比例为10%，最终acc为90.91%。~~已将该模型更新部署到服务器。~~


## 功能
1. 的地得小警察 `modules/dedide_police.py`：检测群消息中误用的“的地得”，并发消息at该群友提出修改方案。
    - 主要使用`AlbertForMaskedLM`模型的预测来判断使用是否正确。例如：消息`香的一匹`（`的`用错，应为`得`）会被处理为`香[MASK]一匹`后输入`AlbertForMaskedLM`，经过计算后取`[MASK]`位置的probability distribution中的地得三个字的概率`{'的':0.1, '得':0.7, '地':0.05}`，比较最高概率de是否与输入中的de一致。因概率最高者为`得`，所以小警察会发送群消息`@群友 的->得`。相关库与框架：[pytorch](https://github.com/pytorch/pytorch), [transformers](https://github.com/huggingface/transformers), [albert_zh](https://github.com/brightmart/albert_zh).
    - 为什么不公开数据集？因为是从群内收集，含群友隐私。未来对数据脱敏处理后有可能公开。
    - ~~[jieba](https://github.com/fxsjy/jieba)~~分词用于判断哪~~些的地得是单独的字。存在于词组中的的地得不属于检测范畴。本项目使用jieba的自定义词典来屏蔽成语（如`众矢之的`）和容易引起混淆的常用词（如`的卢马`、`的地得`）。~~
    - 例：![Alt text](images/dedide_example.png?raw=true "dedide_example")

2. 图片超分辨率 `modules/super_resolution.py`：在群里回复一条带图片的消息并输入“2x”即可获得该图片长和宽分别无损（尽量）\*2的版本。如对一张`1920*1080`的图片超分辨率，结果将会是 `3840*2160`。
    - 流程：收到群消息->判断是否为形如“@123 2x”的超分辨率命令->判断该消息是否回复了其他消息->获取原消息图片->调用超分辨率服务[sr-orenji](http://sr-orenji.ml:6990/)，提交任务->每1秒检查任务结果->任务完成，收到2倍版本，发到群里
    - 模型：[Real-CUGAN](https://github.com/bilibili/ailab/tree/main/Real-CUGAN) by bilibili-ailab。使用了`up2x-latest-no-denoise.pth`的weights，`tile_mode`强制为4，此版本不可选择`cache_mode`。
    - 例：![Alt text](images/sr_example.png?raw=true "sr_example")

3. diss群友 `modules/cai.py`：使用随机语句diss群友。
    - 例：![Alt text](images/cai_example.png?raw=true "cai_example")

## 如何部署
因为🍊太懒，这部分还没有写。

## 特别鸣谢
感谢[sinceL](https://github.com/vayske)以及他的[sirius](https://github.com/vayske/sirius)对本项目部署以及代码编写的帮助！
