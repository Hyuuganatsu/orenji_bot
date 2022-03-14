# orenji_bot
#### English  |  [简体中文](README_zh_CN.md)

This is the repository of orenji_bot🍊, a QQ chatbot equipped with nlp and cv capabilities. 

Functionalities are implemented using [Mirai](https://github.com/mamoe/mirai), [Graia](https://github.com/GraiaProject/) and so on.

## Updates
- 2022-3-11: 
  - Add new feature: `send random anime image from lolicon`. This will call [lolicon API](https://api.lolicon.app/#/setu?id=size)'s service(external).
  - Add new feature: `image database client`. Bot will recognize valuable anime images that members send in group with some rules, and then save it to orenji_backend's database. It can also get an anime image randomly from database, and send it to group.
- 2022-3-2: 
  - Updated versions of graia. Currently [graia-saya](https://github.com/GraiaProject/Saya) manages modules and [graia-ariadne](https://github.com/GraiaProject/Ariadne/) works as the main framework.
  - Add new feature: `anime image super resolution`. To trigger this feature, just reply to a group message that has at least one image and typ "2x". This feature relies on my http super-resolution service: [sr-orenji](http://sr-orenji.ml:6990/) (details in [super-resolution-web](https://github.com/buptorange/super-resolution-web-public)). 
- 2021-12-29: 
  - Annotated all data and got the balanced dataset with 1200 examples. Change to use bert-base-chinese instead of albert, got an accuracy of 93.81%. The new model is already in service.
- 2021-12-28: 
  - Cleaned+Annotated 1700 sentences that are obtained from group chat. Then used them to finetune the model. Raw ratio: 的:地:得=1400:86:219, `的` accounts for 82% of all examples. Sampled 500 examples from that to be the training set with a ratio of 1:0.5:1. Pretrained weights are from `huggface/albert_chinese_large`, and finetune is performed 50 epoches. Eval set splits 10% off the whole set, and the final accuracy is 90.91%. ~~The new model is already in service.~~


## Functionalities
1. `的地得 Police(Chinese Particle Correction)` in `modules/dedide_police.py`: monitor misuse of "的地得" in group message. If someone is misusing, bot will @ that member and make a correction.
    - Mainly use `AlbertForMaskedLM`'s predictions to judge correctness of particle usage. For Example: a message with `香的一匹`(`的` is a misuse which should be `得`) will be preprocessed to `香[MASK]一匹` and input to `AlbertForMaskedLM`. After computation, probabilities of characters `的, 地, 得` can be obtained from the output probability distribution of `[MASK]`, resuting in a dict like `{'的':0.1, '得':0.7, '地':0.05}`. By comparing if the character with the highest probability is the same as that in original messgae, we can judge the correctness. In this example, as the model thinks `得` is most probably a right answer here, bot will send a group message`@member_name 的->得` to inform that member. Related libraries and frameworks: [pytorch](https://github.com/pytorch/pytorch), [transformers](https://github.com/huggingface/transformers), [albert_zh](https://github.com/brightmart/albert_zh).
    - Why not make the dataset publicly available？As the corpus are collected from a private group containing private information.
    - ~~[jieba](https://github.com/fxsjy/jieba) tokenizer was used to detect which words are single charactered. 的地得 in idioms or given words will not be judged. (like `众矢之的` or `的卢马`, `的地得`).~~
    - Use case: ![Alt text](images/dedide_example.png?raw=true "dedide_example")

2. `Anime Image Super Resolution` in `modules/super_resolution.py`: Replying to a group messsage with at least one image attached and typing "2x" will give you a lossless (as far as possible) 4x resolution version of the original image (with height and width both being 2x). Like if you 2x a `1920*1080` image, size of the output image will be `3840*2160`.
    - Procedure: Receive group message -> Use Regex to check if command pattern "@123 2x" exists -> Check if this message replies to another message that has image -> Fetch the image in the replied message -> Call super resolution service [sr-orenji](http://sr-orenji.ml:6990/) by submitting a task -> Check if task is finished -> Task finished, received 2x version, send to group
    - Model: [Real-CUGAN](https://github.com/bilibili/ailab/tree/main/Real-CUGAN) by bilibili-ailab. The bot's call will definitely use `up2x-latest-no-denoise.pth`'s weights, together with param `tile_mode` being 4. This implementation doesn't support `cache_mode`. 
    - Use case: ![Alt text](images/sr_example.png?raw=true "sr_example")

3. `Diss Group Member` in `modules/cai.py`: Use random statements to diss a group member.
    - Use case: ![Alt text](images/cai_example.png?raw=true "cai_example")
     
4. `Send Random Anime Image from Lolicon` in `modules/random_setu.py`: Call [lolicon API](https://api.lolicon.app/#/setu?id=size) to get a random image's url, then fetching bytes of the image and send to group. The style of returned image fully relies on lolicon.
    - This functionality contains two endpoints: 1. `/setu`: send a random all-ages image, 2. `/r18`: send a random r18 image.

5. `Image Database Client` in `modules/setu_client.py`: As the client of an anime image database (set up elsewhere), bot can interact with the remote server to add image to database, delete image in database or get one random image from database.
    - Add:
      - How to trigger: 
        - Anytime a member replies to a message that has at least one image and types `好`.
        - Each group has its own buffer for storing the latest image. When buffer is not None and someone sends a plain message `好`.
      - Server and bot response: 
        - 204: Image accepted. Bot will send a plain message `好` to group.
        - 400: Image already in database. Bot no action.
        - 404: No image field found in request. Bot no action.
        - 418: With gatekeeper(an image classification dl model)'s computation, server thinks this is not an anime image, so reject. Bot no action.
        - 500: Server-side error. Bot no action.
    - Delete
      - How to trigger: 
        - Anytime a member replies to a message that has at least one image and types `一般`. Sha256 of that image will be calculated to be the unique identifier for server to delete from database.
      - Server and bot response: 
        - 204: Successfully delete from database. Bot no action.
        - 400: Entry deleted, but the image originally didn't exist on disk. Bot no action.
        - 404: Image doesn't exist in database. Bot no action.
        - 500: Server-side error. Bot no action.
    - Get one random image:
      - How to trigger: 
        - Anytime a member send a plain image "setu".
      - Server and bot response: 
        - 200: Server responsed image bytes succesfully. Bot will encode it and send to group.
        - 404: Server database is empty. Bot no action.
        - 500: Server-side error. Bot no action.
      - Use case: ![Alt text](images/get-random_example.png?raw=true "sr_example")

## How to deploy
Not finished, as 🍊 is lazy.

## Acknowledgement
Thanks to [sinceL](https://github.com/vayske) and his [sirius](https://github.com/vayske/sirius) regarding many help on deployment and implementation!

Thanks to [Hongwei Fan](https://github.com/hwfan) regarding the gatekeeper's model selection and preprocessing procedure in training!
