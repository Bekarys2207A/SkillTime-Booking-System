# Используем актуальный легковесный образ Python
FROM python:3.12-slim

WORKDIR /app

# Устанавливаем необходимые пакеты для psycopg2 и проверки зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект в контейнер
COPY . /app

# Создаём папку для загрузки файлов
RUN mkdir -p /app/uploads

# Открываем порт Django
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]