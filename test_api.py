import requests
import json
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_wildberries_search(query="пиджак серый", number_of_photos=2, min_price=None, max_price=None):
    """
    Тестирование поиска товаров в Wildberries через API
    
    Args:
        query: Поисковый запрос
        number_of_photos: Количество требуемых результатов
        min_price: Минимальная цена (опционально) - фильтрует по основной цене
        max_price: Максимальная цена (опционально) - фильтрует по скидочной цене
    """
    url = "http://localhost:8000/search"
    
    # Параметры запроса
    data = {
        "query": query,
        "number_of_photos": number_of_photos,
        "source": "wildberries"
    }
    
    # Добавляем параметры цены, если они указаны
    if min_price is not None:
        data["min_price"] = min_price
    
    if max_price is not None:
        data["max_price"] = max_price
    
    logger.info(f"Отправляем запрос на {url} с данными: {data}")
    
    # Отправляем запрос
    try:
        response = requests.post(url, json=data)
        logger.info(f"Получен ответ со статус-кодом: {response.status_code}")
        
        # Проверяем статус ответа
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Успешный ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Получаем ID задачи
            task_id = result.get('task_id')
            logger.info(f"ID задачи: {task_id}")
            
            # Проверяем статус задачи
            if task_id:
                check_task_status(task_id)
            
            return True
        else:
            logger.error(f"Ошибка при запросе: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Исключение при запросе: {str(e)}")
        return False

def check_task_status(task_id):
    """
    Проверка статуса задачи по ID
    """
    url = f"http://localhost:8000/status/{task_id}"
    
    logger.info(f"Проверяем статус задачи {task_id}")
    
    # Проверяем статус каждую секунду до завершения
    import time
    max_attempts = 30
    attempts = 0
    
    while attempts < max_attempts:
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                logger.info(f"Статус задачи: {status}, прогресс: {status_data.get('progress')}%")
                
                # Если задача завершена или произошла ошибка, выводим результат
                if status in ['completed', 'failed']:
                    logger.info(f"Задача завершена со статусом: {status}")
                    logger.info(f"Детали: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
                    
                    # Если есть информация о товарах, выводим её
                    products = status_data.get('product_details', [])
                    if products:
                        logger.info(f"Найдено товаров: {len(products)}")
                        for i, product in enumerate(products[:5], 1):  # Выводим первые 5 товаров
                            logger.info(f"Товар {i}: {product.get('name')} - Цена: {product.get('price')} руб., Цена со скидкой: {product.get('sale_price')} руб.")
                    
                    # Получаем параметры запроса
                    query_params = {}
                    if "query" in status_data:
                        # Попробуем извлечь параметры цены из исходного запроса
                        # Это упрощение, в реальном сценарии нужно сохранять параметры запроса
                        query_params = {
                            "min_price": status_data.get("min_price"),
                            "max_price": status_data.get("max_price")
                        }
                    
                    # Анализ результатов фильтрации
                    analyze_price_filter_results(status_data, min_price=query_params.get('min_price'), max_price=query_params.get('max_price'))
                    
                    return
            
            # Если статус не получен, ждем секунду перед следующей попыткой
            time.sleep(1)
            attempts += 1
            
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса: {str(e)}")
            time.sleep(1)
            attempts += 1
    
    logger.warning(f"Превышено максимальное количество попыток ({max_attempts})")

def analyze_price_filter_results(status_data, min_price=None, max_price=None):
    """
    Анализ результатов фильтрации по цене
    
    Args:
        status_data: Данные о статусе задачи
        min_price: Минимальная цена
        max_price: Максимальная цена
    """
    products = status_data.get('product_details', [])
    if not products:
        return
    
    logger.info("-" * 50)
    logger.info("Анализ результатов фильтрации по цене:")
    
    # Проверка фильтра по максимальной цене
    if max_price is not None:
        logger.info(f"Проверка фильтра max_price={max_price}:")
        for product in products:
            name = product.get('name', 'Неизвестный товар')
            price = product.get('price', 0)
            sale_price = product.get('sale_price', 0)
            
            if sale_price <= float(max_price):
                logger.info(f"✓ {name} - Основная цена: {price} руб., Цена со скидкой: {sale_price} руб.")
                if price > float(max_price):
                    logger.info(f"  Основная цена > {max_price}, но цена со скидкой ≤ {max_price}, что соответствует ожидаемому поведению API")
            else:
                logger.warning(f"⚠ {name} - Цена со скидкой ({sale_price} руб.) превышает указанный лимит {max_price} руб.")
    
    # Проверка фильтра по минимальной цене
    if min_price is not None:
        logger.info(f"Проверка фильтра min_price={min_price}:")
        for product in products:
            name = product.get('name', 'Неизвестный товар')
            price = product.get('price', 0)
            sale_price = product.get('sale_price', 0)
            
            if price >= float(min_price):
                logger.info(f"✓ {name} - Основная цена: {price} руб., Цена со скидкой: {sale_price} руб.")
                logger.info(f"  Основная цена ≥ {min_price}, что соответствует ожидаемому поведению API")
            else:
                logger.warning(f"⚠ {name} - Основная цена ({price} руб.) меньше указанного минимума {min_price} руб.")
    
    logger.info("-" * 50)

def test_with_price_filter():
    """
    Тест поиска с фильтрацией по цене:
    1. Поиск дешевых товаров (до 5000 рублей)
    2. Поиск дорогих товаров (от 10000 рублей)
    3. Поиск товаров в диапазоне цен (от 5000 до 20000 рублей)
    """
    logger.info("=" * 50)
    logger.info("ТЕСТ 2: Поиск с фильтрацией по цене")
    logger.info("=" * 50)
    
    # Тест на поиск дешевых товаров
    logger.info("2.1 Поиск дешевых товаров (до 5000 рублей)")
    test_wildberries_search(query="пиджак серый", number_of_photos=2, max_price=5000)
    
    # Тест на поиск дорогих товаров
    logger.info("\n2.2 Поиск дорогих товаров (от 10000 рублей)")
    test_wildberries_search(query="пиджак серый", number_of_photos=2, min_price=10000)
    
    # Тест на поиск товаров в диапазоне цен
    logger.info("\n2.3 Поиск товаров в диапазоне цен (от 5000 до 20000 рублей)")
    test_wildberries_search(query="пиджак серый", number_of_photos=2, min_price=5000, max_price=20000)

def test_edge_cases():
    """
    Тестирование граничных случаев при фильтрации по цене
    """
    logger.info("=" * 50)
    logger.info("ТЕСТ 3: Граничные случаи при фильтрации по цене")
    logger.info("=" * 50)
    
    # Тест с очень низкой максимальной ценой
    logger.info("3.1 Поиск с очень низкой максимальной ценой (max_price=1000)")
    test_wildberries_search(query="пиджак серый", number_of_photos=2, max_price=1000)
    
    # Тест с очень высокой минимальной ценой
    logger.info("\n3.2 Поиск с очень высокой минимальной ценой (min_price=50000)")
    test_wildberries_search(query="пиджак серый", number_of_photos=2, min_price=50000)
    
    # Тест с минимальной ценой выше максимальной (эта ситуация обрабатывается в API)
    logger.info("\n3.3 Поиск с минимальной ценой выше максимальной (min_price=30000, max_price=10000)")
    test_wildberries_search(query="пиджак серый", number_of_photos=2, min_price=30000, max_price=10000)

if __name__ == "__main__":
    logger.info("Запуск тестирования API")
    
    # Тест 1: Базовый поиск
    logger.info("=" * 50)
    logger.info("ТЕСТ 1: Базовый поиск товаров")
    logger.info("=" * 50)
    test_wildberries_search()
    
    # Тест 2: Поиск с фильтрацией по цене
    test_with_price_filter()
    
    # Тест 3: Граничные случаи
    test_edge_cases()
    
    logger.info("=" * 50)
    logger.info("Тестирование завершено")
    logger.info("=" * 50) 