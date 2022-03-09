from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Quote
from graia.ariadne.model import Group, Member

async def get_image_bytes_from_msg_id(app, id):
    original_event = await Ariadne.getMessageFromId(self=app, messageId=id)
    if not original_event: return
    original_message = original_event.messageChain
    if Image not in original_message: return
    image = original_message.get(Image)[0]
    return await image.get_bytes()
