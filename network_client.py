import asyncio
import pickle
import threading
import websockets
import socket


class NetworkClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.connected = False

        self.loop = asyncio.new_event_loop()
        threading.Thread(
            target=self._run_loop,
            daemon=True
        ).start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect(self, callback, on_connected, on_error=None):
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True

            if on_connected:
                on_connected()

            async for message in self.websocket:
                data = pickle.loads(message)
                callback(data)

        except Exception as e:
            self.connected = False
            if on_error:
                on_error(str(e))

    def connect(self, callback, on_connected=None, on_error=None):
        asyncio.run_coroutine_threadsafe(
            self._connect(callback, on_connected, on_error),
            self.loop
        )

    def send(self, data):
        if not self.connected:
            return

        async def _send():
            await self.websocket.send(pickle.dumps(data))

        asyncio.run_coroutine_threadsafe(_send(), self.loop)

    def disconnect(self):
        if not self.connected:
            return

        async def _close():
            await self.websocket.close()

        asyncio.run_coroutine_threadsafe(_close(), self.loop)
        self.connected = False