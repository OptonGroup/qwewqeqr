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
        
        # Преобразуем данные в нужный формат
        products = []
        for product in raw_products:
            try:
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
                    "price": product["price"],
                    "sale_price": product.get("sale_price"),
                    "category": product["category"],
                    "colors": product.get("colors", []),
                    "sizes": product.get("sizes", []),
                    "rating": product.get("rating"),
                    "reviews_count": product.get("reviews_count"),
                    "imageUrl": image_urls[0] if image_urls else None,
                    "imageUrls": image_urls,
                    "url": product["url"],
                    "description": product.get("description", ""),
                    "gender": gender or "унисекс",
                    "available": product.get("available", True)
                }
                
                products.append(processed_product)
            except Exception as e:
                logger.error(f"Ошибка при обработке товара {product.get('id')}: {str(e)}")
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
            
            # Обрабатываем результаты
            products = []
            for product in raw_products:
                try:
                    # Преобразуем цены в числа
                    price = int(str(product.get('priceU', '0')).replace(' ', '')) // 100
                    sale_price = int(str(product.get('salePriceU', '0')).replace(' ', '')) // 100
                    
                    # Обновляем: Если sale_price равен 0, используем price
                    if sale_price == 0:
                        sale_price = price
                    
                    # Рассчитываем скидку
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