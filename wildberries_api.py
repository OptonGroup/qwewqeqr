"""
Модуль для работы с API Wildberries через сервисный слой.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from datetime import datetime

# Импортируем существующий класс WildberriesAPI
from wildberries import WildberriesAPI, ProductInfo

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wildberries_api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class WildberriesService:
    """
    Сервисный класс для работы с API Wildberries.
    Предоставляет высокоуровневые методы для поиска товаров.
    """
    
    def __init__(self):
        """
        Инициализация сервиса Wildberries.
        """
        self.api = WildberriesAPI()
        self._cache_dir = Path("wildberries_cache")
        self._cache_dir.mkdir(exist_ok=True)
        logger.info("WildberriesService инициализирован")
    
    async def search_products_async(
        self, 
        query: str, 
        limit: int = 10,
        min_price: Optional[float] = None, 
        max_price: Optional[float] = None,
        gender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Асинхронный поиск товаров по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество товаров в результате
            min_price: Минимальная цена (если указана)
            max_price: Максимальная цена (если указана)
            gender: Пол (мужской, женский, унисекс)
            
        Returns:
            Список товаров, соответствующих запросу
        """
        logger.info(f"Поиск товаров: '{query}', лимит: {limit}, мин. цена: {min_price}, макс. цена: {max_price}, пол: {gender}")
        
        # Преобразуем параметры для совместимости с API
        low_price = int(min_price) if min_price is not None else None
        top_price = int(max_price) if max_price is not None else None
        
        # Вызываем метод поиска из WildberriesAPI
        raw_products = await self.api.search_products(
            query=query,
            limit=limit,
            low_price=low_price,
            top_price=top_price,
            gender=gender
        )
        
        # Логируем структуру первого элемента для отладки
        if raw_products and len(raw_products) > 0:
            logger.debug(f"Пример структуры данных товара: {json.dumps(raw_products[0], ensure_ascii=False, default=str)}")
        
        # Преобразуем данные в нужный формат
        products = []
        for product in raw_products:
            try:
                # Получаем и преобразуем цены
                price_raw = product.get('priceU') or product.get('price') or 0
                sale_price_raw = product.get('salePriceU') or product.get('sale_price') or 0
                
                # Преобразуем цены в числа
                if isinstance(price_raw, str):
                    price_raw = price_raw.replace(' ', '')
                # Без деления на 100, так как значения уже в рублях
                price = int(price_raw) if price_raw else 0
                
                if isinstance(sale_price_raw, str):
                    sale_price_raw = sale_price_raw.replace(' ', '')
                # Без деления на 100, так как значения уже в рублях
                sale_price = int(sale_price_raw) if sale_price_raw else 0
                
                # Если скидочная цена равна 0 или больше основной, используем основную цену
                if sale_price == 0 or sale_price >= price:
                    sale_price = price
                
                # Рассчитываем скидку, если есть разница между ценами
                discount = round((1 - sale_price / price) * 100) if price > 0 and sale_price < price else 0
                
                # Построение URL изображения на основе ID продукта
                vol = product["id"] // 100000
                part = product["id"] // 1000
                bucket = (product["id"] % 100) % 20 + 1
                
                # Формируем URL изображения
                image_urls = []
                for i in range(1, 5):  # Получаем первые 4 изображения
                    image_url = f"https://basket-{bucket:02d}.wbbasket.ru/vol{vol}/part{part}/{product['id']}/images/c516x688/{i}.webp"
                    image_urls.append(image_url)
                
                # Строим JSON для товара
                processed_product = {
                    "id": str(product["id"]),
                    "name": product["name"],
                    "brand": product["brand"],
                    "price": price,
                    "sale_price": sale_price,
                    "discount": discount,
                    "category": product.get("category", ""),
                    "colors": product.get("colors", []),
                    "sizes": product.get("sizes", []),
                    "rating": product.get("rating"),
                    "reviews_count": product.get("reviews_count"),
                    "imageUrl": image_urls[0] if image_urls else None,
                    "imageUrls": image_urls,
                    "url": product.get("url", f"https://www.wildberries.ru/catalog/{product['id']}/detail.aspx"),
                    "description": product.get("description", ""),
                    "gender": gender or "унисекс",
                    "available": product.get("available", True)
                }
                
                logger.debug(f"Обработан товар: {processed_product['name']} - Цена: {price}, Скидка: {sale_price}, Процент: {discount}%")
                products.append(processed_product)
            except Exception as e:
                logger.error(f"Ошибка при обработке товара {product.get('id')}: {str(e)}")
                logger.debug(f"Данные товара с ошибкой: {json.dumps(product, ensure_ascii=False, default=str)}")
                continue
        
        logger.info(f"Найдено {len(products)} товаров по запросу '{query}'")
        return products
    
    async def search_products(
        self, 
        query: str, 
        limit: int = 10,
        min_price: Optional[float] = None, 
        max_price: Optional[float] = None,
        gender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск товаров на Wildberries
        """
        try:
            # Получаем сырые результаты поиска
            raw_products = await self.api.search_products(
                query=query,
                limit=limit,
                low_price=min_price,
                top_price=max_price,
                gender=gender
            )
            
            # Логируем структуру первого элемента для отладки
            if raw_products and len(raw_products) > 0:
                logger.debug(f"Структура данных товара: {json.dumps(raw_products[0], ensure_ascii=False, default=str)}")
            
            # Обрабатываем результаты
            products = []
            for product in raw_products:
                try:
                    # Получаем поля с ценами, проверяя разные возможные имена полей
                    price_raw = product.get('priceU') or product.get('price') or 0
                    sale_price_raw = product.get('salePriceU') or product.get('sale_price') or 0
                    
                    # Преобразуем цены в числа
                    if isinstance(price_raw, str):
                        price_raw = price_raw.replace(' ', '')
                    # Без деления на 100, так как значения уже в рублях
                    price = int(price_raw) if price_raw else 0
                    
                    if isinstance(sale_price_raw, str):
                        sale_price_raw = sale_price_raw.replace(' ', '')
                    # Без деления на 100, так как значения уже в рублях
                    sale_price = int(sale_price_raw) if sale_price_raw else 0
                    
                    # Если скидочная цена равна 0 или больше основной, используем основную цену
                    if sale_price == 0 or sale_price >= price:
                        sale_price = price
                    
                    # Рассчитываем скидку только если основная цена больше 0 и скидочная меньше основной
                    discount = round((1 - sale_price / price) * 100) if price > 0 and sale_price < price else 0
                    
                    processed_product = {
                        'id': product.get('id'),
                        'name': product.get('name'),
                        'brand': product.get('brand'),
                        'price': price,
                        'sale_price': sale_price,
                        'discount': discount,
                        'rating': product.get('rating', 0),
                        'image_url': f"https://images.wbstatic.net/c516x688/new/{str(product.get('id'))[0:4]}/{str(product.get('id'))}-1.jpg",
                        'product_url': f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx",
                        'gender': gender or "унисекс"
                    }
                    products.append(processed_product)
                    
                    logger.info(f"Добавлен товар: {processed_product['name']} (Цена: {processed_product['price']} руб., Скидочная цена: {processed_product['sale_price']} руб., Скидка: {processed_product['discount']}%)")
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке товара {product.get('id')}: {str(e)}")
                    logger.debug(f"Данные товара с ошибкой: {json.dumps(product, ensure_ascii=False, default=str)}")
                    continue
                
            logger.info(f"Найдено {len(products)} товаров по запросу '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {str(e)}")
            return []
    
    async def close(self):
        """
        Закрытие соединений.
        """
        if hasattr(self.api, 'close'):
            await self.api.close() 