import socket
import threading
import pickle
from typing import Dict, List, Any


class NetworkServer:
    """
    Сервер для многопользовательского графического редактора.
    Обрабатывает подключения клиентов и синхронизирует состояние холста.
    """

    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

        self.clients: List[socket.socket] = []
        self.client_names: Dict[socket.socket, str] = {}
        self.canvas_state = {
            'drawings': [],
            'texts': [],
            'background': 'white',
            'current_mode': 'none'  # Добавляем текущий режим в состояние
        }

        print(f"Сервер запущен на {self.host}:{self.port}")

    def broadcast(self, data: Dict[str, Any], exclude_client: socket.socket = None):
        """Отправляет данные всем подключенным клиентам, кроме исключённого"""
        serialized_data = pickle.dumps(data)
        for client in self.clients:
            if client != exclude_client:
                try:
                    client.send(serialized_data)
                except:
                    self.remove_client(client)

    def remove_client(self, client: socket.socket):
        """Удаляет клиента из списка подключённых"""
        if client in self.clients:
            self.clients.remove(client)
            client_name = self.client_names.get(client, "Unknown")
            print(f"Клиент {client_name} отключился")
            if client in self.client_names:
                del self.client_names[client]

    def handle_client(self, client: socket.socket):
        """Обрабатывает соединение с клиентом"""
        try:
            # Первое сообщение - имя клиента
            client_name = client.recv(1024).decode('utf-8')
            self.client_names[client] = client_name
            print(f"Подключился новый клиент: {client_name}")

            # Отправляем текущее состояние холста новому клиенту
            client.send(pickle.dumps({
                'type': 'init',
                'data': self.canvas_state
            }))

            while True:
                data = client.recv(4096)
                if not data:
                    break

                try:
                    message = pickle.loads(data)
                    self.process_message(client, message)
                except pickle.UnpicklingError:
                    print("Ошибка при распаковке данных от клиента")
                    continue

        except ConnectionResetError:
            pass
        finally:
            self.remove_client(client)
            client.close()

    def process_message(self, client: socket.socket, message: Dict[str, Any]):
        message_type = message.get('type')

        if message_type == 'draw':
            # Обновляем только рисунки и фон
            self.canvas_state['drawings'] = message['data']['drawings']
            self.canvas_state['background'] = message['data']['background']
            # Режим не обновляем из сообщения 'draw'

            self.broadcast({
                'type': 'update',
                'data': self.canvas_state
            }, exclude_client=client)

        elif message_type == 'mode_change':
            # Обрабатываем изменение режима
            self.canvas_state['current_mode'] = message['data']['mode']
            self.broadcast({
                'type': 'mode_update',
                'data': {'mode': message['data']['mode']}
            })

        elif message_type == 'clear':
            self.canvas_state = {
                'drawings': [],
                'background': 'white',
                'current_mode': 'none'
            }
            self.broadcast({
                'type': 'clear',
                'data': self.canvas_state
            })

    def start(self):
        """Запускает сервер для принятия подключений"""
        while True:
            client, address = self.server.accept()
            self.clients.append(client)

            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()


class NetworkClient:
    """
    Клиент для подключения к серверу графического редактора.
    Отправляет действия на сервер и получает обновления состояния.
    """

    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.listening = False

    def connect(self, client_name: str) -> bool:
        """Подключается к серверу и отправляет имя клиента"""
        try:
            # Создаем новый сокет при каждом подключении
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
            self.client.send(client_name.encode('utf-8'))
            self.connected = True
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            self.connected = False
            return False

    def send(self, data: Dict[str, Any]):
        """Отправляет данные на сервер"""
        if not self.connected:
            return False

        try:
            serialized_data = pickle.dumps(data)
            self.client.send(serialized_data)
            return True
        except Exception as e:
            print(f"Ошибка отправки данных: {e}")
            self.connected = False
            return False

    def start_listening(self, callback):
        """Запускает поток для прослушивания обновлений от сервера"""
        if not self.connected or self.listening:
            return

        self.listening = True

        def listen():
            while self.listening:
                try:
                    data = self.client.recv(4096)
                    if not data:
                        break

                    message = pickle.loads(data)
                    callback(message)
                except:
                    break

            self.connected = False
            self.listening = False

        thread = threading.Thread(target=listen)
        thread.daemon = True
        thread.start()

    def disconnect(self):
        """Отключается от сервера"""
        self.listening = False
        self.connected = False
        try:
            if self.client:
                self.client.close()
        except:
            pass
        finally:
            self.client = None  # Обнуляем сокет после закрытия

def start_server():
    """Запускает сервер графического редактора"""
    server = NetworkServer()
    server.start()


if __name__ == '__main__':
    start_server()