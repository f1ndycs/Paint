import asyncio
import websockets
import pickle
import logging

logging.basicConfig(level=logging.INFO)

clients = set()

canvas_state = {
    "drawings": [],
    "background": "white"
}


async def handler(websocket):
    logging.info("Клиент подключился")
    clients.add(websocket)

    # отправляем текущее состояние
    await websocket.send(pickle.dumps({
        "type": "init",
        "data": canvas_state
    }))

    try:
        async for message in websocket:
            data = pickle.loads(message)

            if data["type"] == "draw":
                canvas_state["drawings"] = data["data"]["drawings"]
                canvas_state["background"] = data["data"]["background"]

                # рассылаем всем
                await broadcast({
                    "type": "update",
                    "data": canvas_state
                }, sender=websocket)

            elif data["type"] == "clear":
                canvas_state["drawings"] = []
                canvas_state["background"] = "white"

                await broadcast({
                    "type": "clear",
                    "data": canvas_state
                })

    except websockets.exceptions.ConnectionClosed:
        logging.info("Клиент отключился")
    finally:
        clients.remove(websocket)


async def broadcast(message, sender=None):
    if not clients:
        return

    data = pickle.dumps(message)

    await asyncio.gather(*[
        client.send(data)
        for client in clients
        if client != sender
    ])


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        logging.info("Async сервер запущен ws://0.0.0.0:8765")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())