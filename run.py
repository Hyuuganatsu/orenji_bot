import os
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import config, WebsocketClientConfig, HttpClientConfig
from creart import create

from graia.saya import Saya

from config.config import ACCOUNT

os.chdir(os.path.dirname(os.path.realpath(__file__)))

# instantiate saya
saya = create(Saya)

# instantiate ariadne
app = Ariadne(config(
        ACCOUNT,
        "191932207",
        WebsocketClientConfig(host="http://host.docker.internal:8850"),
        HttpClientConfig(host="http://host.docker.internal:8850")
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
