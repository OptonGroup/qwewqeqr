#!/bin/bash

# Проверка наличия файла .env
if [ ! -f .env ]; then
  echo "Файл .env не найден. Создаю пример файла .env..."
  cat > .env << EOL
# API ключи для работы ассистента
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Настройки для логирования
LOG_LEVEL=INFO
EOL
  echo "Создан пример файла .env. Пожалуйста, заполните его правильными значениями API ключей."
  exit 1
fi

# Сборка и запуск контейнеров
echo "Сборка и запуск Docker контейнеров..."
docker-compose up -d --build

# Проверка статуса контейнеров
echo "Проверка статуса контейнеров..."
docker-compose ps

echo ""
echo "Приложение запущено!"
echo "Фронтенд доступен по адресу: http://localhost:3000"
echo "API бэкенда доступен по адресу: http://localhost:8000"
echo "Документация API: http://localhost:8000/docs" 