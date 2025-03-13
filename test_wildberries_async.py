#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для асинхронного клиента Wildberries API.
"""

import asyncio
import argparse
import json
import sys
import logging
import traceback
from typing import List, Dict, Any, Optional
from wildberries_async import WildberriesAsyncAPI

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Добавляем глобальный таймаут для всех операций
GLOBAL_TIMEOUT = 30  # секунд

async def test_search(api: WildberriesAsyncAPI, query: str, limit: int = 5, timeout: int = GLOBAL_TIMEOUT):
    """
    Тестирует поиск товаров.
    
    Args:
        api: Экземпляр API клиента
        query: Поисковый запрос
        limit: Максимальное количество результатов
        timeout: Таймаут операции в секундах
    """
    logger.info(f"Тестирование поиска товаров по запросу: '{query}', лимит: {limit}")
    
    try:
        # Добавляем таймаут на выполнение операции
        products = await asyncio.wait_for(
            api.search_products_async(query, limit),
            timeout=timeout
        )
        
        if not products:
            logger.warning(f"По запросу '{query}' не найдено товаров")
            return
        
        logger.info(f"Найдено {len(products)} товаров:")
        
        for i, product in enumerate(products[:3], 1):
            logger.info(f"{i}. {product['name']} - {product['brand']}")
            logger.info(f"   Цена: {product['price']} руб. (Скидка: {product['sale_price']} руб.)")
            logger.info(f"   Рейтинг: {product['rating']}, Отзывы: {product['feedbacks']}")
            logger.info(f"   URL: {product['url']}")
            logger.info(f"   Цвета: {', '.join(product['colors'])}")
            logger.info(f"   Изображения: {len(product['images'])}")
            logger.info("---")
        
        # Сохраняем первый товар в файл для использования в других тестах
        if products:
            with open("last_product.json", "w", encoding="utf-8") as f:
                json.dump(products[0], f, ensure_ascii=False, indent=2)
            logger.info(f"Первый товар сохранен в файл last_product.json")
        
        return products
    
    except asyncio.TimeoutError:
        logger.error(f"Превышено время ожидания ({timeout} сек.) при поиске товаров по запросу '{query}'")
        return None
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {str(e)}")
        logger.error(f"Детали ошибки: {traceback.format_exc()}")
        return None

async def test_similar_products(api: WildberriesAsyncAPI, product_id: Optional[int] = None, limit: int = 5, timeout: int = GLOBAL_TIMEOUT):
    """
    Тестирует поиск похожих товаров.
    
    Args:
        api: Экземпляр API клиента
        product_id: ID товара (если None, берется из last_product.json)
        limit: Максимальное количество результатов
        timeout: Таймаут операции в секундах
    """
    # Если product_id не указан, пытаемся взять из файла
    if product_id is None:
        try:
            with open("last_product.json", "r", encoding="utf-8") as f:
                product = json.load(f)
                product_id = product["id"]
        except Exception as e:
            logger.error(f"Не удалось прочитать ID товара из файла: {str(e)}")
            return None
    
    logger.info(f"Тестирование поиска похожих товаров для товара с ID: {product_id}, лимит: {limit}")
    
    try:
        # Добавляем таймаут на выполнение операции
        similar_products = await asyncio.wait_for(
            api.get_similar_products_async(product_id, limit),
            timeout=timeout
        )
        
        if not similar_products:
            logger.warning(f"Для товара с ID {product_id} не найдено похожих товаров")
            return
        
        logger.info(f"Найдено {len(similar_products)} похожих товаров")
        
        # Печатаем информацию о похожих товарах
        for i, product in enumerate(similar_products[:3], 1):
            logger.info(f"{i}. ID: {product.get('id')}")
            logger.info(f"   Название: {product.get('name', 'Н/Д')}")
            logger.info("---")
        
        return similar_products
    
    except asyncio.TimeoutError:
        logger.error(f"Превышено время ожидания ({timeout} сек.) при поиске похожих товаров для ID {product_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при поиске похожих товаров: {str(e)}")
        logger.error(f"Детали ошибки: {traceback.format_exc()}")
        return None

async def test_download_images(api: WildberriesAsyncAPI, product: Optional[Dict[str, Any]] = None, max_images: int = 2, timeout: int = GLOBAL_TIMEOUT):
    """
    Тестирует URL изображений товара без их загрузки.
    
    Args:
        api: Экземпляр API клиента
        product: Информация о товаре (если None, берется из last_product.json)
        max_images: Максимальное количество изображений для проверки
        timeout: Таймаут операции в секундах
    """
    # Если товар не указан, пытаемся взять из файла
    if product is None:
        try:
            with open("last_product.json", "r", encoding="utf-8") as f:
                product = json.load(f)
        except Exception as e:
            logger.error(f"Не удалось прочитать информацию о товаре из файла: {str(e)}")
            return None
    
    logger.info(f"Тестирование URL изображений для товара: {product.get('name', 'Н/Д')}, макс. кол-во: {max_images}")
    
    try:
        # Проверяем наличие изображений в информации о товаре
        images = product.get("images", [])
        
        if not images:
            logger.warning(f"У товара нет изображений")
            return []
        
        # Ограничиваем количество изображений
        images = images[:max_images]
        
        logger.info(f"Найдено {len(images)} URL изображений:")
        
        for i, image_url in enumerate(images, 1):
            logger.info(f"{i}. {image_url}")
        
        return images
    
    except Exception as e:
        logger.error(f"Ошибка при проверке URL изображений: {str(e)}")
        logger.error(f"Детали ошибки: {traceback.format_exc()}")
        return None

async def run_all_tests(query: str, limit: int = 5, cache_enabled: bool = True, timeout: int = GLOBAL_TIMEOUT):
    """
    Запускает все тесты последовательно.
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов
        cache_enabled: Флаг включения кеширования
        timeout: Таймаут операций в секундах
    """
    logger.info(f"Запуск всех тестов с запросом: '{query}', лимит: {limit}, кеширование: {cache_enabled}")
    logger.info(f"Глобальный таймаут: {timeout} сек.")
    
    # Создаем экземпляр API клиента
    api = WildberriesAsyncAPI(cache_enabled=cache_enabled)
    logger.info("Создан экземпляр WildberriesAsyncAPI")
    
    try:
        # 1. Тест поиска товаров
        logger.info("=== ТЕСТ 1: Поиск товаров ===")
        products = await test_search(api, query, limit, timeout)
        
        # 2. Тест поиска похожих товаров (если найден хотя бы один товар)
        if products:
            logger.info("=== ТЕСТ 2: Поиск похожих товаров ===")
            similar_products = await test_similar_products(api, products[0]["id"], limit, timeout)
        
            # 3. Тест загрузки изображений (используем первый товар)
            if products[0].get("images"):
                logger.info("=== ТЕСТ 3: Загрузка изображений ===")
                await test_download_images(api, products[0], 2, timeout)
        
        # 4. Тестируем кеширование, запускаем тот же поиск еще раз
        if cache_enabled:
            logger.info("=== ТЕСТ 4: Проверка кеширования (повторный поиск) ===")
            await test_search(api, query, limit, timeout)
    
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в ходе тестирования: {str(e)}")
        logger.error(f"Детали ошибки: {traceback.format_exc()}")
    
    finally:
        # Закрываем сессию HTTP
        logger.info("Закрытие HTTP сессии...")
        await api.close()
        logger.info("Тестирование завершено")

def main():
    """
    Точка входа в программу.
    """
    # Разбор аргументов командной строки
    parser = argparse.ArgumentParser(description="Тестовый скрипт для асинхронного клиента Wildberries API")
    parser.add_argument("--query", type=str, default="платье летнее", help="Поисковый запрос")
    parser.add_argument("--limit", type=int, default=5, help="Максимальное количество результатов")
    parser.add_argument("--no-cache", action="store_true", help="Отключить кеширование")
    parser.add_argument("--timeout", type=int, default=GLOBAL_TIMEOUT, help=f"Глобальный таймаут в секундах (по умолчанию: {GLOBAL_TIMEOUT})")
    args = parser.parse_args()
    
    try:
        # Запускаем все тесты
        asyncio.run(run_all_tests(args.query, args.limit, not args.no_cache, args.timeout))
    except KeyboardInterrupt:
        logger.info("Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        logger.error(f"Детали ошибки: {traceback.format_exc()}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 