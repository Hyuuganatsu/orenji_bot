import asyncio

from graia.saya import Saya
from graia.broadcast import Broadcast
from graia.saya.builtins.broadcast import BroadcastBehaviour

from graia.application import GraiaMiraiApplication, Session

import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))

loop = asyncio.get_event_loop()
broadcast = Broadcast(loop=loop)

saya = Saya(broadcast)
saya.install_behaviours(BroadcastBehaviour(broadcast))

app = GraiaMiraiApplication(
        broadcast=broadcast,
        connect_info=Session(
            host="http://localhost:8080",
            authKey="191932207",
            account=1657321174,
            websocket=True,
        )
)

modpath = os.getcwd() + '/modules'

with saya.module_context():
    modules = [f for f in os.listdir(modpath) if os.path.isfile(os.path.join(modpath, f))]
    for module in modules:
        module = module.split('.', 1)[0]
        saya.require(f'modules.{module}')

app.launch_blocking()

try:
    loop.run_forever()
except KeyboardInterrupt:
    exit()
