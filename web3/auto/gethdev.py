from web3 import (
    AsyncIPCProvider,
    AsyncWeb3,
    IPCProvider,
    Web3,
)
from web3.middleware import (
    ExtraDataToPOAMiddleware,
)
from web3.providers.ipc import (
    get_dev_ipc_path,
)

w3 = Web3(IPCProvider(get_dev_ipc_path()))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

async_w3 = AsyncWeb3.persistent_websocket(AsyncIPCProvider(get_dev_ipc_path()))
async_w3.middleware_onion.inject(extradata_to_poa_middleware, layer=0)
