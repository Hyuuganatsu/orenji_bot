import asyncio
from collections import defaultdict, deque

from graia.ariadne.message.element import Image

# 用message.id获取其中图片的bytes
async def get_image_bytes_from_msg_id(app, id):
    original_event = await app.get_message_from_id(message=id)
    if not original_event: return
    original_message = original_event.message_chain
    if Image not in original_message: return
    image = original_message.get(Image)[0]
    return await image.get_bytes()

###
# 色图buffer。 Dict[group.id:str, q:deque]
###
setu_detect_buffer = defaultdict(deque)

# 清空色图buffer，并把新Image放入
async def clear_local_q_and_append_Image(img_obj, group):
    q = setu_detect_buffer[group.id]
    #print("获取到群{}的队列{}，buffer为{}".format(group.id, q, setu_detect_buffer))
    while q:
        q.popleft()
    q.append(img_obj)
    #print("队列更新为{}，buffer为{}".format(group.id, q, setu_detect_buffer))
    await asyncio.sleep(0)

# 清空色图buffer
async def clear_local_q(group):
    q = setu_detect_buffer[group.id]
    #print("获取到群{}的队列{}，buffer为{}".format(group.id, q, setu_detect_buffer))
    while q:
        q.popleft()
    #print("队列更新为{}，buffer为{}".format(group.id, q, setu_detect_buffer))
    await asyncio.sleep(0)

###
# stable-diffusion 工作队列。任务会被顺序执行。
###
stable_diffusion_work_queue = deque()

async def check_sd_queue_state():
    if stable_diffusion_work_queue.__len__() == 0: return True
    else: return False

