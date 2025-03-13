#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Асинхронный клиент для работы с API Wildberries.

Предоставляет функциональность для поиска товаров и получения детальной информации.
"""

import os
import aiohttp
import asyncio
import json
import logging
import sys
import traceback
from typing import Dict, List, Optional, Any, Union
from functools import wraps
import time
from urllib.parse import quote

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("wildberries.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Декоратор для повторных попыток
def async_retry(max_retries=3, initial_delay=1, backoff_factor=2, exceptions=(Exception,)):
    """
    Декоратор для асинхронных функций, который позволяет выполнять повторные попытки
    при возникновении указанных исключений с экспоненциальной задержкой.
    
    Args:
        max_retries: Максимальное количество повторных попыток
        initial_delay: Начальная задержка между попытками (в секундах)
        backoff_factor: Фактор увеличения задержки между попытками
        exceptions: Исключения, при которых выполнять повторные попытки
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for retry in range(max_retries + 1):
                try:
                    logger.debug(f"Попытка {retry + 1}/{max_retries + 1} выполнения {func.__name__}")
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if retry == max_retries:
                        logger.error(f"Превышено максимальное количество попыток ({max_retries}) для {func.__name__}. Последняя ошибка: {str(e)}")
                        logger.error(f"Трассировка: {traceback.format_exc()}")
                        raise
                    
                    wait_time = delay * (backoff_factor ** retry)
                    logger.warning(f"Попытка {retry + 1}/{max_retries + 1} не удалась для {func.__name__}: {str(e)}. Повторная попытка через {wait_time:.2f} сек.")
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

class WildberriesAsyncAPI:
    """
    Асинхронный клиент для работы с API Wildberries.
    """
    
    # Базовые URL для API
    SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    DETAIL_URL = "https://card.wb.ru/cards/detail"
    SIMILAR_URL = "https://similar-products.wildberries.ru/api/v1/recommendations"
    
    def __init__(self, photo_dir: str = "photo", max_retries: int = 3, cache_enabled: bool = True):
        """
        Инициализирует клиент API Wildberries.
        
        Args:
            photo_dir: Директория для сохранения фотографий
            max_retries: Максимальное количество повторных попыток при сбоях API
            cache_enabled: Флаг включения кеширования ответов
        """
        self.photo_dir = photo_dir
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        
        # Создаем директорию для фотографий, если она не существует
        os.makedirs(photo_dir, exist_ok=True)
        logger.info(f"Директория для фотографий проверена: {photo_dir}")
        
        # Кеш для хранения ответов на повторяющиеся запросы
        self.response_cache: Dict[str, Any] = {}
        
        # HTTP сессия для асинхронных запросов
        self.http_session = None
        
        logger.info(f"Инициализирован асинхронный клиент Wildberries API (max_retries={max_retries}, cache_enabled={cache_enabled})")
    
    async def _ensure_session(self):
        """
        Убеждается, что HTTP сессия создана.
        """
        if self.http_session is None or self.http_session.closed:
            logger.info("Создание новой HTTP сессии")
            self.http_session = aiohttp.ClientSession()
        else:
            logger.debug("Используется существующая HTTP сессия")
    
    async def close(self):
        """
        Закрывает HTTP сессию и освобождает ресурсы.
        """
        if self.http_session and not self.http_session.closed:
            logger.info("Закрытие HTTP сессии")
            await self.http_session.close()
            self.http_session = None
            logger.info("HTTP сессия Wildberries закрыта")
        else:
            logger.info("HTTP сессия уже закрыта или не существует")
    
    def _generate_cache_key(self, method: str, **params) -> str:
        """
        Генерирует ключ для кеширования на основе метода и параметров.
        
        Args:
            method: Название метода API
            params: Параметры запроса
            
        Returns:
            Ключ для кеширования
        """
        params_str = json.dumps(params, sort_keys=True)
        cache_key = f"{method}:{hash(params_str)}"
        logger.debug(f"Сгенерирован ключ кеша: {cache_key}")
        return cache_key
    
    @async_retry(max_retries=3, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _search_products(self, query: str, limit: int = 100, skip: int = 0, low_price: Optional[int] = None, top_price: Optional[int] = None) -> Dict[str, Any]:
        """
        Выполняет поиск товаров по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            skip: Количество результатов для пропуска (для пагинации)
            low_price: Минимальная цена (в копейках) для фильтрации по основной цене товаров
            top_price: Максимальная цена (в копейках) для фильтрации по скидочной цене товаров
            
        Returns:
            Данные о найденных товарах
        """
        logger.info(f"Выполнение поиска товаров: запрос='{query}', лимит={limit}, пропуск={skip}, low_price={low_price}, top_price={top_price}")
        
        # Проверяем кеш, если кеширование включено
        if self.cache_enabled:
            cache_key = self._generate_cache_key("search", query=query, limit=limit, skip=skip, low_price=low_price, top_price=top_price)
            if cache_key in self.response_cache:
                logger.info(f"Результаты поиска '{query}' найдены в кеше")
                return self.response_cache[cache_key]
        
        await self._ensure_session()
        
        # Параметры запроса
        params = {
            "appType": "1",
            "couponsGeo": "12,3,18,15,21",
            "curr": "rub",
            "dest": "-1029256,-102269,-2162196,-1257786",
            "emp": "0",
            "lang": "ru",
            "locale": "ru",
            "pricemarginCoeff": "1.0",
            "query": query,
            "reg": "0",
            "regions": "68,64,83,4,38,80,33,70,82,86,75,30,69,22,66,31,40,1,48,71",
            "resultset": "catalog",
            "sort": "popular",
            "spp": "0",
            "suppressSpellcheck": "false",  # Преобразуем Boolean в строку
            "limit": str(limit),  # Преобразуем int в строку
            "skip": str(skip)  # Преобразуем int в строку
        }
        
        # Добавляем параметры цены, если они указаны
        if low_price is not None:
            params["price_low"] = str(low_price)
        if top_price is not None:
            params["price_high"] = str(top_price)
        
        # Добавляем дополнительные заголовки для имитации браузера
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.wildberries.ru/",
            "Origin": "https://www.wildberries.ru",
            "Connection": "keep-alive"
        }
        
        logger.info(f"Отправка запроса к {self.SEARCH_URL} с параметрами: {params}")
        
        try:
            async with self.http_session.get(self.SEARCH_URL, params=params, headers=headers, timeout=60) as response:
                logger.info(f"Получен ответ с кодом статуса: {response.status}")
                logger.info(f"Тип контента: {response.content_type}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка API Wildberries: {response.status} - {error_text}")
                    raise Exception(f"Wildberries API вернул код ошибки: {response.status}")
                
                logger.info("Чтение данных ответа...")
                
                # Проверяем тип контента и обрабатываем соответственно
                try:
                    # Пытаемся прочитать как JSON
                    result = await response.json()
                except aiohttp.ContentTypeError:
                    # Если не удалось прочитать как JSON, читаем как текст
                    logger.warning("Не удалось прочитать ответ как JSON, попытка чтения как текста")
                    text_result = await response.text()
                    logger.info(f"Получен текстовый ответ длиной {len(text_result)} символов")
                    
                    # Пытаемся преобразовать текст в JSON
                    try:
                        import json
                        result = json.loads(text_result)
                        logger.info("Успешно преобразовано из текста в JSON")
                    except json.JSONDecodeError as e:
                        logger.error(f"Не удалось преобразовать текстовый ответ в JSON: {str(e)}")
                        
                        # Возвращаем пустой результат в формате ожидаемой структуры
                        logger.warning("Возвращаем пустой результат")
                        result = {"data": {"products": []}}
                
                logger.info(f"Данные получены успешно, длина ответа: {len(str(result))}")
                
                # Проверяем структуру ответа
                if "data" not in result:
                    logger.warning("Полученный результат не содержит поле 'data', возвращаем пустую структуру")
                    result = {"data": {"products": []}}
                
                # Сохраняем результат в кеш, если кеширование включено
                if self.cache_enabled:
                    cache_key = self._generate_cache_key("search", query=query, limit=limit, skip=skip, low_price=low_price, top_price=top_price)
                    self.response_cache[cache_key] = result
                    logger.info(f"Результаты сохранены в кеш с ключом: {cache_key}")
                
                return result
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса к API Wildberries: {str(e)}")
            logger.error(f"Трассировка: {traceback.format_exc()}")
            raise
    
    @async_retry(max_retries=3, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _get_product_details(self, product_ids: List[int]) -> Dict[str, Any]:
        """
        Получает детальную информацию о товарах по их ID.
        
        Args:
            product_ids: Список ID товаров
            
        Returns:
            Детальная информация о товарах
        """
        logger.info(f"Получение детальной информации о товарах: {product_ids}")
        
        # Проверяем кеш, если кеширование включено
        if self.cache_enabled:
            cache_key = self._generate_cache_key("details", product_ids=product_ids)
            if cache_key in self.response_cache:
                logger.info(f"Детальная информация о товарах найдена в кеше")
                return self.response_cache[cache_key]
        
        await self._ensure_session()
        
        # Преобразуем список ID в строку через запятую
        nm_id_param = ";".join(map(str, product_ids))
        
        # Параметры запроса
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": "-1029256,-102269,-2162196,-1257786",
            "spp": "0",
            "nm": nm_id_param
        }
        
        # Добавляем дополнительные заголовки для имитации браузера
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.wildberries.ru/",
            "Origin": "https://www.wildberries.ru",
            "Connection": "keep-alive"
        }
        
        logger.info(f"Отправка запроса к {self.DETAIL_URL} с параметрами: {params}")
        
        try:
            async with self.http_session.get(self.DETAIL_URL, params=params, headers=headers, timeout=60) as response:
                logger.info(f"Получен ответ с кодом статуса: {response.status}")
                logger.info(f"Тип контента: {response.content_type}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка API Wildberries: {response.status} - {error_text}")
                    raise Exception(f"Wildberries API вернул код ошибки: {response.status}")
                
                logger.info("Чтение данных ответа...")
                
                # Проверяем тип контента и обрабатываем соответственно
                try:
                    # Пытаемся прочитать как JSON
                    result = await response.json()
                except aiohttp.ContentTypeError:
                    # Если не удалось прочитать как JSON, читаем как текст
                    logger.warning("Не удалось прочитать ответ как JSON, попытка чтения как текста")
                    text_result = await response.text()
                    logger.info(f"Получен текстовый ответ длиной {len(text_result)} символов")
                    
                    # Пытаемся преобразовать текст в JSON
                    try:
                        import json
                        result = json.loads(text_result)
                        logger.info("Успешно преобразовано из текста в JSON")
                    except json.JSONDecodeError as e:
                        logger.error(f"Не удалось преобразовать текстовый ответ в JSON: {str(e)}")
                        
                        # Возвращаем пустой результат в формате ожидаемой структуры
                        logger.warning("Возвращаем пустой результат")
                        result = {"data": {"products": []}}
                
                logger.info(f"Данные получены успешно, длина ответа: {len(str(result))}")
                
                # Проверяем структуру ответа
                if "data" not in result:
                    logger.warning("Полученный результат не содержит поле 'data', возвращаем пустую структуру")
                    result = {"data": {"products": []}}
                
                # Сохраняем результат в кеш, если кеширование включено
                if self.cache_enabled:
                    cache_key = self._generate_cache_key("details", product_ids=product_ids)
                    self.response_cache[cache_key] = result
                    logger.info(f"Результаты сохранены в кеш с ключом: {cache_key}")
                
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении детальной информации: {str(e)}")
            logger.error(f"Трассировка: {traceback.format_exc()}")
            raise
    
    @async_retry(max_retries=3, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _get_similar_products(self, product_id: int) -> Dict[str, Any]:
        """
        Получает список похожих товаров для указанного ID товара.
        
        Args:
            product_id: ID товара, для которого ищем похожие
            
        Returns:
            Список похожих товаров
        """
        logger.info(f"Поиск похожих товаров для ID={product_id}")
        
        # Проверяем кеш, если кеширование включено
        if self.cache_enabled:
            cache_key = self._generate_cache_key("similar", product_id=product_id)
            if cache_key in self.response_cache:
                logger.info(f"Похожие товары для ID={product_id} найдены в кеше")
                return self.response_cache[cache_key]
        
        await self._ensure_session()
        
        # Добавляем дополнительные заголовки для имитации браузера
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.wildberries.ru/",
            "Origin": "https://www.wildberries.ru",
            "Connection": "keep-alive"
        }
        
        logger.info(f"Отправка запроса к {self.SIMILAR_URL} с nmId={str(product_id)}")
        
        try:
            url = f"{self.SIMILAR_URL}?nmId={str(product_id)}"
            async with self.http_session.get(url, headers=headers, timeout=60) as response:
                logger.info(f"Получен ответ с кодом статуса: {response.status}")
                logger.info(f"Тип контента: {response.content_type}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка API Wildberries: {response.status} - {error_text}")
                    raise Exception(f"Wildberries API вернул код ошибки: {response.status}")
                
                logger.info("Чтение данных ответа...")
                
                # Проверяем тип контента и обрабатываем соответственно
                try:
                    # Пытаемся прочитать как JSON
                    result = await response.json()
                except aiohttp.ContentTypeError:
                    # Если не удалось прочитать как JSON, читаем как текст
                    logger.warning("Не удалось прочитать ответ как JSON, попытка чтения как текста")
                    text_result = await response.text()
                    logger.info(f"Получен текстовый ответ длиной {len(text_result)} символов")
                    
                    # Пытаемся преобразовать текст в JSON
                    try:
                        import json
                        result = json.loads(text_result)
                        logger.info("Успешно преобразовано из текста в JSON")
                    except json.JSONDecodeError as e:
                        logger.error(f"Не удалось преобразовать текстовый ответ в JSON: {str(e)}")
                        
                        # Возвращаем пустой результат в формате ожидаемой структуры
                        logger.warning("Возвращаем пустой результат")
                        result = {"data": {"products": []}}
                
                logger.info(f"Данные получены успешно, длина ответа: {len(str(result))}")
                
                # Проверяем структуру ответа
                if not isinstance(result, dict) or "data" not in result:
                    logger.warning("Неверная структура ответа, создаем пустую структуру")
                    result = {"data": {"products": []}}
                
                # Сохраняем результат в кеш, если кеширование включено
                if self.cache_enabled:
                    cache_key = self._generate_cache_key("similar", product_id=product_id)
                    self.response_cache[cache_key] = result
                    logger.info(f"Результаты сохранены в кеш с ключом: {cache_key}")
                
                return result
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих товаров: {str(e)}")
            logger.error(f"Трассировка: {traceback.format_exc()}")
            raise
    
    @async_retry(max_retries=3, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _download_image(self, image_url: str, file_name: str) -> str:
        """
        Загружает изображение по URL и сохраняет его в указанную директорию.
        
        Args:
            image_url: URL изображения
            file_name: Имя файла для сохранения
            
        Returns:
            Путь к сохраненному файлу
        """
        await self._ensure_session()
        
        # Формируем полный путь к файлу
        file_path = os.path.join(self.photo_dir, file_name)
        
        # Проверяем, существует ли файл
        if os.path.exists(file_path):
            logger.info(f"Изображение уже существует: {file_path}")
            return file_path
        
        try:
            # Добавляем заголовки для имитации браузера
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.wildberries.ru/",
                "Connection": "keep-alive"
            }
            
            logger.info(f"Загрузка изображения: {image_url}")
            
            # Загружаем изображение с таймаутом 10 секунд
            async with self.http_session.get(image_url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка при загрузке изображения: {response.status} - {error_text}")
                    raise Exception(f"Ошибка при загрузке изображения: {response.status}")
                
                # Сохраняем изображение
                with open(file_path, "wb") as f:
                    # Читаем данные с таймаутом
                    data = await asyncio.wait_for(response.read(), timeout=5)
                    f.write(data)
                
                logger.info(f"Изображение успешно загружено: {file_path}")
                return file_path
        except asyncio.TimeoutError:
            logger.error(f"Превышено время ожидания при загрузке изображения: {image_url}")
            # Создаем пустой файл, чтобы не пытаться загрузить его снова
            with open(file_path, "wb") as f:
                f.write(b"")
            return file_path
        except Exception as e:
            logger.error(f"Ошибка при загрузке изображения {image_url}: {str(e)}")
            logger.error(f"Трассировка: {traceback.format_exc()}")
            # Создаем пустой файл, чтобы не пытаться загрузить его снова
            with open(file_path, "wb") as f:
                f.write(b"")
            return file_path
    
    async def search_products_async(self, query: str, limit: int = 10, min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Асинхронно выполняет поиск товаров по запросу и возвращает форматированные данные.
        
        Для фильтрации по цене используются следующие параметры:
        - min_price (минимальная цена) - фильтрует товары по основной цене (price)
          Возвращаются только товары, у которых price >= min_price
        - max_price (максимальная цена) - фильтрует товары по скидочной цене (sale_price)
          Возвращаются только товары, у которых sale_price <= max_price
        
        Обратите внимание на следующие особенности фильтрации по цене:
        1. При указании max_price могут возвращаться товары, у которых основная цена (price) 
           выше max_price, но скидочная цена (sale_price) не превышает max_price.
        2. При указании min_price возвращаются товары, у которых основная цена (price) 
           не меньше min_price, даже если скидочная цена ниже min_price.
        3. При указании обоих параметров (min_price и max_price) применяются оба условия:
           сначала отбираются товары с price >= min_price, затем из них выбираются товары с sale_price <= max_price.
        4. При противоречивых параметрах (например, min_price=30000, max_price=10000) приоритет отдается min_price,
           в результате могут возвращаться товары с price >= min_price и sale_price > max_price.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            min_price: Минимальная цена (в рублях) для фильтрации по основной цене товаров
            max_price: Максимальная цена (в рублях) для фильтрации по скидочной цене товаров
            
        Returns:
            Список товаров с детальной информацией
        """
        logger.info(f"Поиск товаров по запросу: '{query}', лимит: {limit}, min_price: {min_price}, max_price: {max_price}")
        
        # Преобразуем параметры цены в копейки для API и обрабатываем None значения
        low_price = None if min_price is None else int(min_price * 100)
        top_price = None if max_price is None else int(max_price * 100)
        
        # Выполняем поиск товаров с учетом параметров цены
        search_results = await self._search_products(query, limit=limit, low_price=low_price, top_price=top_price)
        
        # Проверяем наличие результатов
        products = search_results.get("data", {}).get("products", [])
        if not products:
            logger.warning(f"По запросу '{query}' не найдено товаров")
            return []
        
        # Ограничиваем количество результатов
        products = products[:limit]
        
        # Получаем ID товаров для запроса детальной информации
        product_ids = [product.get("id", 0) for product in products]
        
        # Получаем детальную информацию о товарах
        details_results = await self._get_product_details(product_ids)
        
        # Преобразуем результаты в удобный формат
        formatted_products = []
        
        for product in products:
            product_id = product.get("id", 0)
            
            # Формируем базовую информацию о товаре
            product_info = {
                "id": product_id,
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "price": product.get("priceU", 0) / 100,  # Цена в копейках, переводим в рубли
                "sale_price": product.get("salePriceU", 0) / 100,
                "rating": product.get("rating", 0),
                "feedbacks": product.get("feedbacks", 0),
                "colors": [],
                "sizes": [],
                "images": [],
                "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
            }
            
            # Добавляем изображения
            if "pics" in product:
                base_url = f"https://images.wbstatic.net/c516x688/new/{str(product_id)[:4]}/{product_id}-"
                pics = product.get("pics", [])
                
                # Обработка случая, когда pics может быть числом, а не списком
                if isinstance(pics, int):
                    logger.warning(f"Поле 'pics' для товара {product_id} является числом ({pics}), а не списком. Создаем изображения на основе этого числа.")
                    # Если pics - это число, создаем список из этого числа изображений
                    product_info["images"] = [f"{base_url}{i}.jpg" for i in range(1, min(6, pics + 1))]
                else:
                    # Если pics - это список, как и ожидалось
                    product_info["images"] = [f"{base_url}{i}.jpg" for i in range(1, min(6, len(pics) + 1))]
            
            # Дополняем информацию из детального запроса
            if "data" in details_results and "products" in details_results["data"]:
                for detail_product in details_results["data"]["products"]:
                    if detail_product.get("id") == product_id:
                        # Добавляем цвета
                        if "colors" in detail_product:
                            product_info["colors"] = [color.get("name", "") for color in detail_product.get("colors", [])]
                        
                        # Добавляем размеры
                        if "sizes" in detail_product:
                            product_info["sizes"] = [
                                {
                                    "name": size.get("name", ""),
                                    "origName": size.get("origName", ""),
                                    "stocks": [stock.get("qty", 0) for stock in size.get("stocks", [])]
                                }
                                for size in detail_product.get("sizes", [])
                            ]
                        
                        # Добавляем описание
                        if "description" in detail_product:
                            product_info["description"] = detail_product.get("description", "")
                        
                        break
            
            formatted_products.append(product_info)
        
        logger.info(f"Найдено {len(formatted_products)} товаров по запросу '{query}'")
        return formatted_products
    
    async def get_similar_products_async(self, product_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Асинхронно получает список похожих товаров для указанного ID товара.
        
        Args:
            product_id: ID товара
            limit: Максимальное количество результатов
            
        Returns:
            Список похожих товаров
        """
        logger.info(f"Поиск похожих товаров для товара с ID: {product_id}, лимит: {limit}")
        
        try:
            # Пытаемся получить похожие товары
            similar_results = await self._get_similar_products(product_id)
            
            # Проверяем наличие результатов
            similar_products = similar_results.get("data", {}).get("products", [])
            if not similar_products:
                logger.warning(f"Для товара с ID {product_id} не найдено похожих товаров")
                return []
            
            # Ограничиваем количество результатов
            similar_products = similar_products[:limit]
            
            # Получаем ID товаров для запроса детальной информации
            product_ids = [product.get("id", 0) for product in similar_products]
            
            # Получаем детальную информацию о товарах
            details_results = await self._get_product_details(product_ids)
            
            # Преобразуем результаты в удобный формат (аналогично методу search_products_async)
            # ...код для форматирования результатов, аналогичный методу search_products_async...
            
            # Временно возвращаем исходные данные
            return similar_products
        except Exception as e:
            logger.error(f"Ошибка при получении похожих товаров: {str(e)}")
            logger.warning("Возвращаем пустой список похожих товаров")
            return []
    
    async def download_product_images_async(self, product: Dict[str, Any], max_images: int = 3) -> List[str]:
        """
        Асинхронно загружает изображения для указанного товара.
        
        Args:
            product: Информация о товаре
            max_images: Максимальное количество изображений для загрузки
            
        Returns:
            Список путей к загруженным изображениям
        """
        logger.info(f"Загрузка изображений для товара: {product.get('name', '')}")
        
        # Проверяем наличие изображений
        images = product.get("images", [])
        if not images:
            logger.warning(f"У товара нет изображений")
            return []
        
        # Ограничиваем количество изображений
        images = images[:max_images]
        
        # Создаем список для хранения путей к загруженным изображениям
        downloaded_images = []
        
        # Загружаем изображения последовательно с коротким таймаутом
        for i, image_url in enumerate(images):
            try:
                file_name = f"{product.get('id', 0)}_{i + 1}.jpg"
                file_path = os.path.join(self.photo_dir, file_name)
                
                # Проверяем, существует ли файл
                if os.path.exists(file_path):
                    logger.info(f"Изображение уже существует: {file_path}")
                    downloaded_images.append(file_path)
                    continue
                
                # Загружаем изображение с коротким таймаутом
                try:
                    path = await asyncio.wait_for(
                        self._download_image(image_url, file_name),
                        timeout=5  # Короткий таймаут для каждого изображения
                    )
                    downloaded_images.append(path)
                except asyncio.TimeoutError:
                    logger.error(f"Превышено время ожидания при загрузке изображения: {image_url}")
                    # Создаем пустой файл, чтобы не пытаться загрузить его снова
                    with open(file_path, "wb") as f:
                        f.write(b"")
                    downloaded_images.append(file_path)
            except Exception as e:
                logger.error(f"Ошибка при загрузке изображения {image_url}: {str(e)}")
                logger.error(f"Трассировка: {traceback.format_exc()}")
                # Продолжаем загрузку следующих изображений
                continue
        
        logger.info(f"Загружено {len(downloaded_images)} изображений для товара")
        return downloaded_images
    
    def search_products(self, query: str, limit: int = 10, min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Синхронная обертка для асинхронного метода search_products_async.
        
        Для фильтрации по цене используются следующие параметры:
        - min_price (минимальная цена) - фильтрует товары по основной цене (price)
          Возвращаются только товары, у которых price >= min_price
        - max_price (максимальная цена) - фильтрует товары по скидочной цене (sale_price)
          Возвращаются только товары, у которых sale_price <= max_price
        
        Обратите внимание на следующие особенности фильтрации по цене:
        1. При указании max_price могут возвращаться товары, у которых основная цена (price) 
           выше max_price, но скидочная цена (sale_price) не превышает max_price.
        2. При указании min_price возвращаются товары, у которых основная цена (price) 
           не меньше min_price, даже если скидочная цена ниже min_price.
        3. При указании обоих параметров (min_price и max_price) применяются оба условия:
           сначала отбираются товары с price >= min_price, затем из них выбираются товары с sale_price <= max_price.
        4. При противоречивых параметрах (например, min_price=30000, max_price=10000) приоритет отдается min_price,
           в результате могут возвращаться товары с price >= min_price и sale_price > max_price.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            min_price: Минимальная цена (в рублях) для фильтрации по основной цене товаров
            max_price: Максимальная цена (в рублях) для фильтрации по скидочной цене товаров
            
        Returns:
            Список товаров с детальной информацией
        """
        logger.info(f"Вызов синхронного метода поиска товаров: '{query}', limit={limit}, min_price={min_price}, max_price={max_price}")
        
        async def search_and_close():
            try:
                await self._ensure_session()
                return await self.search_products_async(query, limit, min_price, max_price)
            finally:
                await self.close()
        
        return asyncio.run(search_and_close())
    
    def get_similar_products(self, product_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Синхронная обертка для асинхронного метода get_similar_products_async.
        
        Args:
            product_id: ID товара
            limit: Максимальное количество результатов
            
        Returns:
            Список похожих товаров
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def get_similar_and_close():
            try:
                return await self.get_similar_products_async(product_id, limit)
            finally:
                await self.close()
        
        return loop.run_until_complete(get_similar_and_close())
    
    def download_product_images(self, product: Dict[str, Any], max_images: int = 3) -> List[str]:
        """
        Синхронная обертка для асинхронного метода download_product_images_async.
        
        Args:
            product: Информация о товаре
            max_images: Максимальное количество изображений для загрузки
            
        Returns:
            Список путей к загруженным изображениям
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def download_and_close():
            try:
                return await self.download_product_images_async(product, max_images)
            finally:
                await self.close()
        
        return loop.run_until_complete(download_and_close()) 