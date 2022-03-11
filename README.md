# orenji_bot

本仓库为量产型🍊的代码仓库。功能使用了[Mirai](https://github.com/mamoe/mirai)、[Graia](https://github.com/GraiaProject/)等框架实现。

## 更新内容
- 2022-3-11更新：
  - 增加了新功能：`发送随机lolicon图片`。该功能调用了[lolicon API](https://api.lolicon.app/#/setu?id=size)的接口。
  - 增加了新功能：`图库client`。bot会根据一些规则识别群友觉得有价值的图片，发给远端数据库存储。也可以从数据库中随机取一张图片发到群里。
- 2022-3-2更新：
  - 更新了graia相关库，现在为[graia-saya](https://github.com/GraiaProject/Saya)管理module，[graia-ariadne](https://github.com/GraiaProject/Ariadne/)作为主框架。
  - 增加了新功能：`图片超分辨率(2x super resolution)`。在群里回复一条带图片的消息并输入“2x”即可调用此功能。此功能依赖我的超分辨率http服务：[sr-orenji](http://sr-orenji.ml:6990/)(具体请见此仓库[super-resolution-web](https://github.com/buptorange/super-resolution-web-public))。
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
     
4. 发送随机lolicon图片 `modules/random_setu.py`：调用[lolicon API](https://api.lolicon.app/#/setu?id=size)的接口，取到随机到的图片的url，然后取其bytes发到群里。返回的图片完全依赖lolicon的口味。
    - 该功能包含两个endpoint：1. `/setu`：随机往群里发一张全年龄图片，2. `/r18`：随机往群里发一张r18图片。

5. 图库client `modules/setu_client.py`：作为图库client，和自建的远端图库server通信，以实现增加图片入库、删除、随机获取等操作。
    - 图片入库(add)：
      - 触发：
        - 群里有人主动以`好`字回复一条带图片的消息时，该图片会被发给server。
        - 每个群都会有自己的当前最新图片的buffer，当buffer不为空且有人发了`好`作为群消息时，buffer里的图片会被发给server。
      - server响应及bot响应：
        - 204：图片已成功入库。bot会发送群消息`好`。
        - 400：已经添加过该图片。bot无动作。
        - 404：请求中不含有图片。bot无动作。
        - 418：server经模型计算，判断该图质量不够高，拒绝入库。bot会发送群消息`一般`。
        - 500：server端错误。bot无动作。
    - 图片删除（delete）：
      - 触发：
        - 群里有人主动以`一般`回复一条带图片的消息时，该图片的sha256会被计算出来，作为标识符发给server，请求从库中删除该图片。
      - server响应及bot响应：
        - 204：已成功从库中删除。bot无动作。
        - 400：表项已删除，但硬盘上本来就不存在该图。bot无动作。
        - 404：库中不存在该图。bot无动作。
        - 500：server端错误。bot无动作。
    - 获取随机图片（get-random）：
      - 触发：
        - 群里有人发送`/se`作为群消息时触发。
      - server响应及bot响应：
        - 200：server成功返回了随机图片bytes。bot对其编码，作为图片发送到群里。
        - 404：server的数据库为空。bot无动作。
        - 500：server端错误。bot无动作。

## 如何部署
因为🍊太懒，这部分还没有写。

## 特别鸣谢
感谢[sinceL](https://github.com/vayske)以及他的[sirius](https://github.com/vayske/sirius)对本项目部署以及代码编写的帮助！

感谢[Hongwei Fan](https://github.com/hwfan)对server端深度学习模型选择及图片预处理提供的帮助！
