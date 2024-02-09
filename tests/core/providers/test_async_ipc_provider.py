import os
import pathlib
import pytest
import socket
import tempfile
from threading import (
    Thread,
)
import time
import uuid

from web3 import AsyncWeb3
from web3.exceptions import (
    ProviderConnectionError,
)
from web3.providers.async_ipc import (
    AsyncIPCProvider,
)
from web3.types import (
    RPCEndpoint,
)


@pytest.fixture
def jsonrpc_ipc_pipe_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        ipc_path = os.path.join(temp_dir, f"{uuid.uuid4()}.ipc")
        try:
            yield ipc_path
        finally:
            if os.path.exists(ipc_path):
                os.remove(ipc_path)


@pytest.mark.asyncio
async def test_provider_is_connected(jsonrpc_ipc_pipe_path, serve_empty_result):
    """
    AsyncIPCProvider.is_connected() returns False when disconnected
    """
    async with AsyncWeb3.persistent_websocket(
        AsyncIPCProvider(pathlib.Path(jsonrpc_ipc_pipe_path))
    ) as w3:
        # clears cache
        await w3.provider.disconnect()
        assert await w3.is_connected() is False
        with pytest.raises(ProviderConnectionError):
            await w3.is_connected(show_traceback=True)


def test_ipc_tilda_in_path():
    expected_path = str(pathlib.Path.home()) + "/foo"
    assert AsyncIPCProvider("~/foo").ipc_path == expected_path
    assert AsyncIPCProvider(pathlib.Path("~/foo")).ipc_path == expected_path


@pytest.fixture
def simple_ipc_server(jsonrpc_ipc_pipe_path):
    serv = socket.socket(socket.AF_UNIX)
    serv.bind(jsonrpc_ipc_pipe_path)
    serv.listen(1)
    try:
        yield serv
    finally:
        serv.close()


@pytest.fixture
def serve_empty_result(simple_ipc_server):
    def reply():
        connection, client_address = simple_ipc_server.accept()
        try:
            connection.recv(1024)
            connection.sendall(b'{"id": 0, "result": {}')
            time.sleep(0.1)
            connection.sendall(b"}")
        finally:
            # Clean up the connection
            connection.close()
            simple_ipc_server.close()

    thd = Thread(target=reply, daemon=True)
    thd.start()

    try:
        yield
    finally:
        thd.join()


@pytest.mark.asyncio
async def test_async_waits_for_full_result(jsonrpc_ipc_pipe_path, serve_empty_result):
    async with AsyncWeb3.persistent_websocket(
        AsyncIPCProvider(pathlib.Path(jsonrpc_ipc_pipe_path))
    ) as w3:
        result = await w3.provider.make_request("method", [])
        assert result == {"id": 0, "result": {}}
        # Cleanup
        await w3.provider.disconnect()


@pytest.mark.asyncio
async def test_await_persistent_websocket(jsonrpc_ipc_pipe_path, serve_empty_result):
    w3 = await AsyncWeb3.persistent_websocket(AsyncIPCProvider(pathlib.Path(jsonrpc_ipc_pipe_path)))
    result = await w3.provider.make_request("method", [])
    assert result == {"id": 0, "result": {}}
    await w3.provider.disconnect()


@pytest.mark.asyncio
async def test_persistent_websocket(jsonrpc_ipc_pipe_path, serve_empty_result):
    w3 = AsyncWeb3.persistent_websocket(AsyncIPCProvider(pathlib.Path(jsonrpc_ipc_pipe_path)))
    await w3.provider.connect()
    result = await w3.provider.make_request("method", [])
    assert result == {"id": 0, "result": {}}
    await w3.provider.disconnect()


@pytest.mark.asyncio
async def test_emulate_websocket_v2_tests():
    pass
