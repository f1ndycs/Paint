import unittest
from unittest.mock import MagicMock

from network_client import NetworkClient

class TestNetworkClient(unittest.TestCase):

    def setUp(self):
        self.client = NetworkClient("ws://0.0.0.0:8765")
        self.client.websocket = MagicMock()
        self.client.connected = True

    def test_send_without_connection(self):
        self.client.connected = False
        result = self.client.send({"type": "draw"})
        self.assertIsNone(result)

    def test_disconnect(self):
        self.client.disconnect()
        self.assertFalse(self.client.connected)

    def test_callback_called(self):
        callback = MagicMock()
        data = {"type": "update"}

        callback(data)

        callback.assert_called_once_with(data)