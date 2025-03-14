# Инструкции по работе с Docker

## Сборка и запуск приложения

### Способ 1: Использование скриптов

#### Linux/Mac

```bash
chmod +x start.sh
./start.sh
```

#### Windows

```bash
start.bat
```

### Способ 2: Ручная сборка и запуск

```bash
# Сборка образов
docker-compose build

# Запуск контейнеров
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## Остановка приложения

```bash
docker-compose down
```

## Управление данными

### Очистка кэша

```bash
# Остановите контейнеры
docker-compose down

# Удалите папки кэша
rm -rf cache/ metrics/ static/ photo/ vision_cache/ pinterest_cache/ wildberries_cache/

# Создайте пустые папки
mkdir -p cache metrics static photo vision_cache pinterest_cache wildberries_cache

# Запустите контейнеры заново
docker-compose up -d
```

## Обновление проекта

```bash
# Получите последние изменения из репозитория
git pull

# Пересоберите образы
docker-compose build

# Перезапустите контейнеры
docker-compose up -d
```

## Устранение неполадок

### Проблема: Контейнеры не запускаются

Решение:

1. Проверьте логи:
   ```bash
   docker-compose logs
   ```

2. Убедитесь, что порты 3000 и 8000 свободны:
   ```bash
   # Linux/Mac
   lsof -i :3000
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :3000
   netstat -ano | findstr :8000
   ```

3. Перезапустите Docker:
   ```bash
   # Linux
   sudo systemctl restart docker
   
   # Mac
   killall Docker && open /Applications/Docker.app
   
   # Windows
   Перезапустите Docker Desktop
   ```

### Проблема: Фронтенд не подключается к бэкенду

Решение:

1. Проверьте, что бэкенд запущен и отвечает на запросы:
   ```bash
   curl http://localhost:8000/health
   ```

2. Проверьте настройки CORS в бэкенде:
   ```bash
   # Просмотр логов бэкенда
   docker-compose logs backend
   ```

## Дополнительные команды

### Просмотр запущенных контейнеров

```bash
docker ps
```

### Вход в контейнер

```bash
# Бэкенд
docker-compose exec backend bash

# Фронтенд
docker-compose exec frontend sh
```

### Проверка использования ресурсов

```bash
docker stats
``` 