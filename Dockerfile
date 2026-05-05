FROM python:3.10-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ код (включая main.py) в папку /app контейнера
COPY . .

# Команда запуска теперь берется из docker-compose, так что тут можно оставить так
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]