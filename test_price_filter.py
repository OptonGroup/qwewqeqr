import asyncio
import logging
from wildberries import Wildberries

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_price_filter.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_price_filters():
    """
    Тестирование фильтрации по цене в API Wildberries
    """
    logger.info("=" * 50)
    logger.info("ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ ПО ЦЕНЕ")
    logger.info("=" * 50)
    
    # Инициализация клиента
    wb = Wildberries()
    
    try:
        # Тест 1: Базовый поиск без фильтров цены
        logger.info("\n1. Базовый поиск без фильтров цены")
        products = await wb.search_products(
            query="пиджак серый",
            limit=3
        )
        log_products(products, "Базовый поиск")
        
        # Тест 2: Поиск с фильтром максимальной цены (скидочной)
        logger.info("\n2. Поиск с фильтром максимальной цены (max_price=5000)")
        products_max_price = await wb.search_products(
            query="пиджак серый",
            limit=3,
            max_price=5000
        )
        log_products(products_max_price, "Фильтр max_price=5000")
        
        # Тест 3: Поиск с фильтром минимальной цены (основной)
        logger.info("\n3. Поиск с фильтром минимальной цены (min_price=10000)")
        products_min_price = await wb.search_products(
            query="пиджак серый",
            limit=3,
            min_price=10000
        )
        log_products(products_min_price, "Фильтр min_price=10000")
        
        # Тест 4: Поиск с фильтром минимальной и максимальной цены
        logger.info("\n4. Поиск с фильтром минимальной и максимальной цены (min_price=5000, max_price=20000)")
        products_range = await wb.search_products(
            query="пиджак серый",
            limit=3,
            min_price=5000,
            max_price=20000
        )
        log_products(products_range, "Фильтр min_price=5000, max_price=20000")
        
        logger.info("\nПодробный анализ результатов фильтрации по цене:")
        
        # Анализ результатов Теста 2 (max_price=5000)
        if products_max_price:
            logger.info("-" * 50)
            logger.info("Анализ результатов с max_price=5000:")
            for product in products_max_price:
                price = product.get('price', 0)
                sale_price = product.get('sale_price', 0)
                name = product.get('name', 'Неизвестный товар')
                
                if sale_price <= 5000 and price > 5000:
                    logger.info(f"✓ Подтверждение: {name} - основная цена {price} руб., скидочная цена {sale_price} руб.")
                    logger.info(f"  Основная цена > 5000, но скидочная <= 5000, что соответствует ожидаемому поведению API")
                else:
                    logger.info(f"ℹ Товар: {name} - основная цена {price} руб., скидочная цена {sale_price} руб.")
        
        # Анализ результатов Теста 3 (min_price=10000)
        if products_min_price:
            logger.info("-" * 50)
            logger.info("Анализ результатов с min_price=10000:")
            for product in products_min_price:
                price = product.get('price', 0)
                sale_price = product.get('sale_price', 0)
                name = product.get('name', 'Неизвестный товар')
                
                if price >= 10000:
                    logger.info(f"✓ Подтверждение: {name} - основная цена {price} руб., скидочная цена {sale_price} руб.")
                    logger.info(f"  Основная цена >= 10000, что соответствует ожидаемому поведению API")
                else:
                    logger.info(f"⚠ Неожиданно: {name} - основная цена {price} руб., скидочная цена {sale_price} руб.")
                    logger.info(f"  Основная цена < 10000, что не соответствует ожидаемому поведению API")
        
        logger.info("=" * 50)
        logger.info("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        logger.info("=" * 50)
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
    finally:
        await wb.close()
        logger.info("Соединение закрыто")

def log_products(products, test_name):
    """
    Логирование информации о найденных товарах
    """
    if not products:
        logger.info(f"[{test_name}] Не найдено товаров")
        return
    
    logger.info(f"[{test_name}] Найдено товаров: {len(products)}")
    for i, product in enumerate(products, 1):
        name = product.get('name', 'Неизвестный товар')
        price = product.get('price', 0)
        sale_price = product.get('sale_price', 0)
        discount = 0
        if price > 0:
            discount = round((1 - sale_price / price) * 100)
        
        logger.info(f"[{test_name}] Товар {i}: {name}")
        logger.info(f"[{test_name}]   Основная цена: {price} руб.")
        logger.info(f"[{test_name}]   Скидочная цена: {sale_price} руб.")
        logger.info(f"[{test_name}]   Скидка: {discount}%")

if __name__ == "__main__":
    asyncio.run(test_price_filters()) 