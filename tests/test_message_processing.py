import unittest

class TestMessageProcessing(unittest.TestCase):

    def setUp(self):
        self.canvas_state = {
            "drawings": [],
            "background": "white"
        }

    def test_draw_message_updates_canvas(self):
        message = {
            "type": "draw",
            "data": {
                "drawings": ["line1"],
                "background": "black"
            }
        }

        # имитация логики сервера
        self.canvas_state["drawings"] = message["data"]["drawings"]
        self.canvas_state["background"] = message["data"]["background"]

        self.assertEqual(self.canvas_state["drawings"], ["line1"])
        self.assertEqual(self.canvas_state["background"], "black")

    def test_clear_message(self):
        self.canvas_state["drawings"] = ["line1"]

        self.canvas_state["drawings"] = []
        self.canvas_state["background"] = "white"

        self.assertEqual(self.canvas_state["drawings"], [])
        self.assertEqual(self.canvas_state["background"], "white")