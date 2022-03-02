import asyncio

import glob
import os
from graia.broadcast import Broadcast
from graia.ariadne.app import Ariadne
from graia.ariadne.adapter import CombinedAdapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import Friend, MiraiSession

from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour


os.chdir(os.path.dirname(os.path.realpath(__file__)))

loop = asyncio.new_event_loop()
broadcast = Broadcast(loop=loop)

saya = Saya(broadcast)
saya.install_behaviours(BroadcastBehaviour(broadcast))


app = Ariadne(connect_info=CombinedAdapter(
        broadcast=broadcast,
        mirai_session=MiraiSession(
            host="http://localhost:8080",
            verify_key="191932207",
            account=1657321174
        ))
)

modpath = os.getcwd() + '/modules'

with saya.module_context():
    modules = [f for f in os.listdir(modpath) if os.path.isfile(os.path.join(modpath, f))]
    for module in modules:
        module = module.split('.', 1)[0]
        saya.require(f'modules.{module}')

# app.launch_blocking()
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     exit()
# @broadcast.receiver("FriendMessage")
# async def friend_message_listener(app: Ariadne, friend: Friend):
#     await app.sendMessage(friend, MessageChain.create([Plain("Hello, World!")]))


app.launch_blocking()
