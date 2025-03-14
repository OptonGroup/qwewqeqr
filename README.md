# Анализатор банковских выписок и финансовый помощник

Это приложение представляет собой сервис для анализа банковских выписок и получения финансовых рекомендаций. Приложение состоит из двух компонентов: бэкенда на FastAPI и фронтенда на Next.js.

## Возможности

- Анализ банковских выписок (поддерживаются выписки Тинькофф)
- Классификация транзакций по категориям
- Визуализация расходов и доходов
- Рекомендации по оптимизации расходов
- Поиск товаров по API Wildberries
- Интеграция с Pinterest для поиска стилевых решений
- Чат-ассистент с несколькими ролями (нутрициолог, стилист, косметолог, дизайнер)

## Запуск с использованием Docker

### Предварительные требования

- Docker и Docker Compose
- Создайте файл `.env` с необходимыми переменными окружения (см. пример ниже)

### Шаги для запуска

1. Клонируйте репозиторий:
   ```bash
   git clone <url-репозитория>
   cd <директория-проекта>
   ```

2. Создайте файл `.env` с необходимыми API ключами:
   ```
   # API ключи для работы ассистента
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # Настройки для логирования
   LOG_LEVEL=INFO
   ```

3. Соберите и запустите контейнеры с помощью Docker Compose:
   ```bash
   # Linux/Mac
   chmod +x start.sh
   ./start.sh
   
   # Windows
   start.bat
   
   # Или вручную
   docker-compose build
   docker-compose up -d
   ```

4. Приложение будет доступно по следующим адресам:
   - Фронтенд: http://localhost:3000
   - API бэкенда: http://localhost:8000
   - Документация API: http://localhost:8000/docs

## Устранение неполадок при сборке Docker-образов

### Проблема с версией в docker-compose.yml

Если вы видите предупреждение:
```
the attribute 'version' is obsolete, it will be ignored, please remove it to avoid potential confusion
```

Это нормально, атрибут `version` считается устаревшим в последних версиях Docker Compose.

### Проблема с типизацией TypeScript

Если при сборке вы видите ошибку типизации TypeScript (например, для переменной `gender`), проверьте, что в файле `web-interface/src/app/api/search-pinterest/route.ts` правильно указаны типы:

```typescript
// В интерфейсе PinterestSearchResult
gender?: 'male' | 'female' | undefined;

// В присвоении значения
gender: gender === 'any' ? undefined : (gender as 'male' | 'female')
```

### Проблема с отсутствующими fallback-изображениями

Если сборка не проходит из-за отсутствия изображений, вы можете создать их вручную:

```bash
node create_fallback_images.js
```

## Разработка

### Структура проекта

- `api.py` - основной файл бэкенда FastAPI
- `web-interface/` - директория с фронтенд-приложением Next.js
- `assistant.py` - модуль чат-ассистента
- `wildberries_api.py` - интеграция с API Wildberries
- `pinterest.py` - интеграция с Pinterest
- `visual_analyzer.py` - модуль для анализа изображений
- `cors_setup.py` - настройка CORS для бэкенда

### Запуск без Docker (для разработки)

#### Бэкенд

1. Создайте виртуальное окружение Python и активируйте его:
   ```bash
   python -m venv venv
   source venv/bin/activate  # для Linux/Mac
   venv\Scripts\activate  # для Windows
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Запустите сервер:
   ```bash
   uvicorn api:app --reload
   ```

#### Фронтенд

1. Перейдите в директорию web-interface:
   ```bash
   cd web-interface
   ```

2. Установите зависимости:
   ```bash
   npm install
   ```

3. Запустите сервер разработки:
   ```bash
   npm run dev
   ```

## API документация

После запуска бэкенда, документация API доступна по адресу: http://localhost:8000/docs

## Лицензия

© 2024 Все права защищены. 