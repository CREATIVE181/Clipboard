# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Указываем порт, который будет слушать приложение
EXPOSE 5005

# Запускаем Flask
CMD ["gunicorn", "-w", "4", "app:app", "--bind", "0.0.0.0:5005"]
