"""
Модуль для работы с API Wildberries.
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
import json
from pathlib import Path
import os
from pydantic import BaseModel, Field
from retry import retry
import random
import time
import urllib.parse
from bs4 import BeautifulSoup

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wildberries.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ProductInfo(BaseModel):
    """Модель для хранения информации о товаре."""
    id: int
    name: str
    brand: str
    price: float
    sale_price: Optional[float] = None
    category: str
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    images: List[str] = Field(default_factory=list)
    url: str
    description: Optional[str] = None
    composition: Optional[Dict[str, str]] = None
    available: bool = True
    last_updated: datetime = Field(default_factory=datetime.now)

class WildberriesAPI:
    """Класс для работы с API Wildberries."""
    
    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        dest: str = "-1257786",
        locale: str = "ru",
        currency: str = "rub"
    ):
        """
        Инициализация клиента API Wildberries.
        
        Args:
            user_agent: User-Agent для запросов
            dest: ID региона доставки
            locale: Локаль (язык)
            currency: Валюта цен
        """
        self._session: Optional[aiohttp.ClientSession] = None
        self.headers = {"User-Agent": user_agent}
        self.dest = dest
        self.locale = locale
        self.currency = currency
        self._cache_dir = Path("wildberries_cache")
        self._cache_dir.mkdir(exist_ok=True)
        
        # Загружаем кеш
        self._load_cache()
        logger.info("Wildberries API клиент инициализирован")
    
    async def _init_session(self):
        """Инициализация HTTP сессии."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
    
    @retry(tries=5, delay=2, backoff=2)
    async def search_products(
        self, 
        query: str, 
        limit: int = 10,
        low_price: Optional[int] = None, 
        top_price: Optional[int] = None, 
        discount: Optional[int] = None
    ) -> List[Dict]:
        """
        Поиск товаров по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            low_price: Минимальная цена. Фильтрует товары по основной цене (price).
                       Если None, будет использовано значение 1.
            top_price: Максимальная цена. Фильтрует товары по скидочной цене (sale_price).
                       Если None, будет использовано значение 1000000.
            discount: Минимальная скидка в процентах
            
        Returns:
            Список найденных товаров
            
        Примечание:
            Особенности фильтрации по цене в API Wildberries:
            - Параметр low_price (min_price) фильтрует товары по основной цене (price), т.е. возвращаются товары с price ≥ low_price
            - Параметр top_price (max_price) фильтрует товары по скидочной цене (sale_price), т.е. возвращаются товары с sale_price ≤ top_price
            - При установке top_price=5000 могут возвращаться товары с основной ценой выше 5000 руб.,
              если их скидочная цена (sale_price) не превышает 5000 руб.
            - При установке обоих параметров (low_price и top_price) применяются оба фильтра последовательно:
              сначала отбираются товары с price ≥ low_price, затем из них выбираются товары с sale_price ≤ top_price
            - При противоречивых параметрах (например, low_price=30000, top_price=10000) приоритет отдается low_price,
              что может привести к пустому результату, если нет товаров, удовлетворяющих обоим условиям
        """
        try:
            await self._init_session()
            
            # Безопасное преобразование и валидация параметров цены
            try:
                # Преобразуем None или строковые значения в целые числа
                safe_low_price = 1 if low_price is None else int(low_price)
                safe_top_price = 1000000 if top_price is None else int(top_price)
                
                # Проверяем, что цены имеют корректные значения
                if safe_low_price < 1:
                    safe_low_price = 1
                    logger.warning(f"Минимальная цена скорректирована до {safe_low_price}")
                
                if safe_top_price < safe_low_price:
                    logger.warning(f"Противоречивые параметры цены: low_price ({safe_low_price}) > top_price ({safe_top_price}). Это может привести к пустому результату.")
            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка при обработке параметров цены: {e}. Используются значения по умолчанию.")
                safe_low_price = 1
                safe_top_price = 1000000
            
            # Логирование параметров запроса
            logger.info(f"Поиск товаров по запросу '{query}' с параметрами: limit={limit}, low_price={safe_low_price}, top_price={safe_top_price}, discount={discount}")
            
            # Формируем URL для поиска
            url = (
                'https://search.wb.ru/exactmatch/ru/common/v4/search'
                '?appType=1'
                f'&curr={self.currency}'
                f'&dest={self.dest}'
                f'&locale={self.locale}'
                '&page=1'
                f'&priceU={safe_low_price * 100};{safe_top_price * 100}'
                f'&query={urllib.parse.quote(query)}'
                '&resultset=catalog'
                '&sort=popular'
                '&spp=0'
                '&suppressSpellcheck=false'
            )
            
            if discount is not None:
                url += f'&discount={discount}'
            
            logger.info(f"Поиск товаров по URL: {url}")
            
            # Добавляем необходимые заголовки
            headers = {
                **self.headers,
                'Accept': 'application/json',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Origin': 'https://www.wildberries.ru',
                'Pragma': 'no-cache',
                'Referer': 'https://www.wildberries.ru/',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            # Добавляем случайную задержку для имитации поведения пользователя
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            async with self._session.get(url, headers=headers, timeout=30) as response:
                if response.status == 429:
                    logger.warning("Получен статус 429 (слишком много запросов), ждем 10 секунд")
                    await asyncio.sleep(10)
                    raise Exception("Rate limit exceeded")
                
                if response.status != 200:
                    logger.error(f"Ошибка при поиске товаров: HTTP {response.status}")
                    return []
                
                # Сначала получаем текст ответа для отладки
                text = await response.text()
                logger.debug(f"Получен ответ: {text[:200]}...")  # Логируем первые 200 символов
                
                try:
                    data = json.loads(text)
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка декодирования JSON: {e}. Текст ответа: {text[:200]}...")
                    return []
                
                if 'data' not in data or 'products' not in data['data']:
                    logger.warning(f"Некорректный формат ответа API: {text[:200]}...")
                    return []
                
                products = []
                for item in data['data']['products'][:limit]:
                    try:
                        # Безопасное получение значений с проверкой типов
                        product_id = str(item.get('id', ''))
                        name = item.get('name', 'Без названия')
                        brand = item.get('brand', '')
                        
                        # Безопасное преобразование цен
                        try:
                            price = int(item.get('priceU', 0) / 100)
                        except (ValueError, TypeError):
                            price = 0
                            
                        try:
                            sale_price = int(item.get('salePriceU', 0) / 100)
                        except (ValueError, TypeError):
                            sale_price = price
                        
                        # Если sale_price равен 0, используем price
                        if sale_price == 0:
                            sale_price = price
                        
                        # Расчет скидки
                        discount_percent = 0
                        if price > 0 and sale_price < price:
                            discount_percent = round(100 - (sale_price / price * 100))
                        
                        # Создаем объект товара
                        product = {
                            'id': product_id,
                            'name': name,
                            'brand': brand,
                            'price': price,
                            'sale_price': sale_price,
                            'discount': discount_percent,
                            'rating': item.get('rating', 0),
                            'url': f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                            'image_url': f"https://images.wbstatic.net/c516x688/new/{product_id[:4] if len(product_id) >= 4 else product_id}/{product_id}/images/big/1.jpg"
                        }
                        
                        products.append(product)
                        logger.info(f"Добавлен товар: {name} (Цена: {price} руб., Скидочная цена: {sale_price} руб., Скидка: {discount_percent}%)")
                        
                    except Exception as e:
                        logger.error(f"Ошибка при обработке товара: {e}")
                        continue
                        
                if products:
                    logger.info(f"Успешно найдено {len(products)} товаров")
                else:
                    logger.warning(f"Не найдены товары для запроса '{query}'")
                
                return products
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {e}")
            return []
        finally:
            # Не закрываем сессию здесь, она может понадобиться для следующих запросов
            pass
    
    def _load_cache(self) -> None:
        """Загружает кеш из файла."""
        try:
            cache_file = self._cache_dir / "products_cache.json"
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Загружен кеш с {len(self._cache)} товарами")
            else:
                self._cache = {}
                logger.info("Создан новый кеш")
        except Exception as e:
            logger.error(f"Ошибка при загрузке кеша: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Сохраняет кеш в файл."""
        try:
            cache_file = self._cache_dir / "products_cache.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.info("Кеш сохранен")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кеша: {e}")
    
    @retry(tries=3, delay=1, backoff=2)
    async def get_product_details(self, product_id: Union[int, str]) -> Optional[ProductInfo]:
        """
        Получает детальную информацию о товаре.
        
        Args:
            product_id: ID товара
            
        Returns:
            Информация о товаре или None, если товар не найден
        """
        # Проверяем кеш
        cache_key = str(product_id)
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            # Проверяем актуальность кеша (24 часа)
            if (datetime.now() - datetime.fromisoformat(cached_data["last_updated"])).total_seconds() < 86400:
                logger.info(f"Данные о товаре {product_id} получены из кеша")
                return ProductInfo(**cached_data)
        
        try:
            session = await self._init_session()
            
            async with session.get(f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx") as response:
                if response.status == 404:
                    logger.warning(f"Товар {product_id} не найден")
                    return None
                    
                response.raise_for_status()
                data = await response.json()
                
                if not data.get("data"):
                    logger.warning(f"Нет данных для товара {product_id}")
                return None
                
                product_data = data["data"]
                product = ProductInfo(
                    id=product_id,
                    name=product_data["name"],
                    brand=product_data.get("brand", ""),
                    price=product_data["priceU"] / 100,
                    sale_price=product_data.get("salePriceU", 0) / 100 if product_data.get("salePriceU") else None,
                    category=product_data.get("category", ""),
                    colors=product_data.get("colors", []),
                    sizes=product_data.get("sizes", []),
                    rating=product_data.get("rating"),
                    reviews_count=product_data.get("feedbacks"),
                    images=product_data.get("pics", []),
                    url=f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                    description=product_data.get("description"),
                    composition=product_data.get("composition"),
                    available=product_data.get("available", True)
                )
                
                # Обновляем кеш
                self._cache[cache_key] = {
                    "id": product.id,
                    "name": product.name,
                    "brand": product.brand,
                    "price": product.price,
                    "sale_price": product.sale_price,
                    "category": product.category,
                    "colors": product.colors,
                    "sizes": product.sizes,
                    "rating": product.rating,
                    "reviews_count": product.reviews_count,
                    "images": product.images,
                    "url": product.url,
                    "description": product.description,
                    "composition": product.composition,
                    "available": product.available,
                    "last_updated": datetime.now().isoformat()
                }
                self._save_cache()
                
                logger.info(f"Получена информация о товаре {product_id}")
                return product
                
        except Exception as e:
            logger.error(f"Ошибка при получении информации о товаре {product_id}: {e}")
            return None
    
    async def close(self) -> None:
        """Закрывает все открытые соединения."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Сессия закрыта")


class Wildberries:
    """Обертка для работы с WildberriesAPI."""
    
    def __init__(self, photo_dir: str = "photo"):
        """
        Инициализация клиента Wildberries.
        
        Args:
            photo_dir: Директория для сохранения фотографий
        """
        self.api = WildberriesAPI()
        self.photo_dir = photo_dir
        
        # Создаем директорию, если её нет
        os.makedirs(photo_dir, exist_ok=True)
    
    async def search_products(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: str = "popular"
    ) -> List[Dict[str, Any]]:
        """
        Поиск товаров по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            category: Категория товаров (опционально)
            min_price: Минимальная цена (опционально). Фильтрует товары по основной цене (price).
                       Если None, будет использовано значение 1.
            max_price: Максимальная цена (опционально). Фильтрует товары по скидочной цене (sale_price).
                       Если None, будет использовано значение 1000000.
            sort: Способ сортировки (popular, price_asc, price_desc, rating)
            
        Returns:
            Список найденных товаров
            
        Примечание:
            Особенности фильтрации по цене в API Wildberries:
            - Параметр min_price фильтрует товары по основной цене (price), т.е. возвращаются товары с price ≥ min_price
            - Параметр max_price фильтрует товары по скидочной цене (sale_price), т.е. возвращаются товары с sale_price ≤ max_price
            - При установке max_price=5000 могут возвращаться товары с основной ценой выше 5000 руб.,
              если их скидочная цена (sale_price) не превышает 5000 руб.
            - При установке обоих параметров применяются оба фильтра последовательно:
              сначала отбираются товары с price ≥ min_price, затем из них выбираются товары с sale_price ≤ max_price
            - При противоречивых параметрах (например, min_price=30000, max_price=10000) приоритет отдается min_price,
              что может привести к пустому результату, если нет товаров, удовлетворяющих обоим условиям
        """
        try:
            # Логирование параметров запроса
            logger.info(f"Поиск товаров с параметрами: query={query}, limit={limit}, min_price={min_price}, max_price={max_price}")
            
            # Передаем параметры в API напрямую, без предварительной обработки
            # Обработка параметров будет выполнена внутри метода search_products класса WildberriesAPI
            products = await self.api.search_products(
                query=query,
                limit=limit,
                low_price=min_price,
                top_price=max_price
            )
            
            # Дополнительная обработка результатов, если необходимо
            # Например, фильтрация по категории, если она указана
            if category and products:
                filtered_products = [p for p in products if category.lower() in p.get('name', '').lower() or 
                                    category.lower() in p.get('brand', '').lower()]
                if filtered_products:
                    logger.info(f"Отфильтровано по категории '{category}': {len(filtered_products)} из {len(products)} товаров")
                    products = filtered_products
                else:
                    logger.warning(f"После фильтрации по категории '{category}' не осталось товаров")
            
            # Сортировка результатов, если указан способ сортировки
            if sort and products:
                if sort == "price_asc":
                    products.sort(key=lambda p: p.get('sale_price', p.get('price', 0)))
                    logger.info("Результаты отсортированы по возрастанию цены")
                elif sort == "price_desc":
                    products.sort(key=lambda p: p.get('sale_price', p.get('price', 0)), reverse=True)
                    logger.info("Результаты отсортированы по убыванию цены")
                elif sort == "rating":
                    products.sort(key=lambda p: p.get('rating', 0), reverse=True)
                    logger.info("Результаты отсортированы по рейтингу")
            
            return products
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {e}")
            raise
    
    async def close(self):
        """Закрывает соединения."""
        await self.api.close()


# Пример использования класса
if __name__ == "__main__":
    wb = WildberriesAPI()
    
    # Поиск товаров
    query = input("Введите поисковый запрос: ")
    products = wb.search_products(
        query=query,
        low_price=1000,
        top_price=5000,
        with_details=True,
        limit=5
    )
    
    # Вывод результатов
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product['name']} (ID: {product['id']})")
        price_sale = product.get('salePriceU', 0)
        price_original = product.get('priceU', 0)
        
        if isinstance(price_sale, int):
            price_sale = price_sale / 100
        
        if isinstance(price_original, int):
            price_original = price_original / 100
            
        print(f"   Цена: {price_sale} руб. (до скидки: {price_original} руб.)")
        print(f"   Бренд: {product.get('brand', '')}, Рейтинг: {product.get('rating', 0)}")
        print(f"   Ссылка: {product.get('link', '')}")
        
        if 'description' in product and product['description']:
            desc = product['description']
            if len(desc) > 200:
                desc = desc[:200] + "..."
            print(f"   Описание: {desc}") 


                