# Используем легкую версию Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с библиотеками и устанавливаем их
COPY requirements.txt .
RUN pip install -no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Команда для запуска бота
CMD ["python", "main.py"]