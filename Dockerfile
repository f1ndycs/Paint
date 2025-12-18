FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем сервер
COPY server_async.py .

# Устанавливаем зависимости
RUN pip install websockets

# Открываем порт WebSocket
EXPOSE 8765

# Команда запуска
CMD ["python", "server_async.py"]