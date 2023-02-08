import asyncio
from graia.ariadne.message.chain import MessageChain, Plain
import glob
import os
from graia.broadcast import Broadcast
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import config, WebsocketClientConfig, HttpClientConfig, WebsocketServerConfig, HttpServerConfig, WebsocketClientInfo
from graia.ariadne.model import Friend
from creart import create

from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour

from local_secret_config import ACCOUNT

os.chdir(os.path.dirname(os.path.realpath(__file__)))

# instantiate saya
saya = create(Saya)

# instantiate ariadne
app = Ariadne(config(
        ACCOUNT,
        "191932207",
        WebsocketClientConfig(host="http://host.docker.internal:8849"),
        HttpClientConfig(host="http://host.docker.internal:8849")
)
)

# import saya modules
modpath = os.getcwd() + '/modules'
with saya.module_context():
    modules = [f for f in os.listdir(modpath) if os.path.isfile(os.path.join(modpath, f))]
    for module in modules:
        module = module.split('.', 1)[0]
        saya.require(f'modules.{module}')

# start loop
app.launch_blocking()
