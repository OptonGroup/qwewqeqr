"""
Модуль для работы с API Wildberries через сервисный слой.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import aiohttp
import math
import os
import random
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Импортируем существующий класс WildberriesAPI
from wildberries import WildberriesAPI, ProductInfo

# Импортируем клиент GigaChat (если он установлен)
try:
    from gigachat import GigaChat
    from gigachat.models import Chat, Messages, MessagesRole
    GIGACHAT_AVAILABLE = True
except ImportError:
    GIGACHAT_AVAILABLE = False

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
        self._bucket_cache = {}  # Кэш для хранения проверенных номеров корзин
        self._session = None
        
        # Инициализация клиента GigaChat
        self.gigachat = None
        if GIGACHAT_AVAILABLE:
            try:
                gigachat_api_key = os.getenv("GIGACHAT_API_KEY")
                if gigachat_api_key:
                    self.gigachat = GigaChat(credentials=gigachat_api_key, verify_ssl_certs=False)
                    logger.info("GigaChat инициализирован успешно")
                else:
                    logger.warning("GIGACHAT_API_KEY не найден в переменных окружения. Генерация рекомендаций будет ограничена.")
            except Exception as e:
                logger.error(f"Ошибка при инициализации GigaChat: {str(e)}")
        else:
            logger.warning("Библиотека GigaChat не установлена. Используем шаблонные рекомендации.")
        
        logger.info("WildberriesService инициализирован")
    
    async def _get_session(self):
        """
        Получение или создание HTTP-сессии для запросов.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        return self._session
    
    async def _check_image_exists(self, url: str) -> bool:
        """
        Проверка существования изображения по URL.
        
        Args:
            url: URL изображения для проверки
            
        Returns:
            True если изображение существует, False в противном случае
        """
        try:
            session = await self._get_session()
            async with session.head(url, timeout=1) as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False
    
    async def _find_correct_bucket(self, product_id: int) -> int:
        """
        Поиск правильного номера корзины для изображения товара.
        
        Алгоритм:
        1. Проверяем кэш
        2. Проверяем известные соответствия
        3. Вычисляем начальное значение через деление на 16 миллионов
        4. Проверяем соседние значения (0-20)
        5. Если ничего не подходит, используем хеш-функцию
        
        Args:
            product_id: ID товара
            
        Returns:
            Номер корзины (1-20)
        """
        # Проверяем кэш
        if product_id in self._bucket_cache:
            return self._bucket_cache[product_id]
        
        # Известные соответствия ID и bucket
        known_buckets = {
            302159505: 18,
            156349471: 10,
            245733463: 16,
            260932681: 16,
            18676447: 2,
            8700187: 1,
            255115886: 16,
        }
        
        # Если ID есть в карте известных bucket, используем его
        if product_id in known_buckets:
            self._bucket_cache[product_id] = known_buckets[product_id]
            return known_buckets[product_id]
        
        # Получаем vol и part для формирования URL
        vol = str(product_id)[:4]  # Первые 4 цифры
        part = str(product_id)[:6]  # Первые 6 цифр
        
        # Вычисляем примерное значение bucket через деление на 16 миллионов
        # Получаем число от 0 до 15
        base_bucket = (product_id % 16000000) % 16 + 1
        
        # Проверяем соседние значения
        buckets_to_check = list(range(1, 21))
        
        # Сначала проверяем наиболее вероятные значения
        buckets_to_check.remove(base_bucket)
        buckets_to_check = [base_bucket] + buckets_to_check
        
        for bucket in buckets_to_check:
            test_url = f"https://basket-{bucket:02d}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/c516x688/1.webp"
            if await self._check_image_exists(test_url):
                # Сохраняем результат в кэш
                self._bucket_cache[product_id] = bucket
                return bucket
        
        # Если не удалось найти подходящий bucket, используем хеш-функцию
        fallback_bucket = (abs(hash(str(product_id))) % 20) + 1
        self._bucket_cache[product_id] = fallback_bucket
        return fallback_bucket
    
    async def _generate_recommendations_with_gigachat(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует рекомендации по уходу за кожей с использованием GigaChat.
        
        Args:
            product: Данные о товаре
            
        Returns:
            Словарь с рекомендациями
        """
        product_name = product.get('name', '')
        product_brand = product.get('brand', '')
        product_description = product.get('description', '')
        
        try:
            # Кэш для рекомендаций, чтобы снизить количество запросов к API
            cache_key = f"{product_name}_{product_brand}"
            cache_file = self._cache_dir / f"recommendations_{hash(cache_key)}.json"
            
            # Проверяем наличие кэша
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    logger.info(f"Рекомендации для '{product_name}' загружены из кэша")
                    return cached_data
                    
            # Если нет GigaChat, используем шаблонные рекомендации с небольшими вариациями
            if not self.gigachat:
                return await self._generate_recommendations_with_templates(product)
            
            # Формируем запрос к GigaChat
            prompt = f"""
            Ты эксперт в области ухода за кожей. Сгенерируй структурированные рекомендации по применению и уходу для косметического продукта:
            
            Название продукта: {product_name}
            Бренд: {product_brand}
            Описание: {product_description}
            
            Пожалуйста, создай подробные рекомендации в следующем формате:
            
            1. Ежедневный уход - как использовать продукт каждый день
            2. Еженедельный уход - как использовать продукт в течение недели
            3. Общие рекомендации по использованию
            4. Подробный утренний уход - пошаговый список процедур:
               - Очищение: конкретный тип продукта
               - Тонизирование: конкретный тип продукта
               - Сыворотка: конкретный тип продукта
               - Увлажнение: конкретный тип продукта
               - Защита: конкретный тип продукта
            5. Подробный вечерний уход - пошаговый список процедур:
               - Очищение: конкретный тип продукта
               - Тонизирование: конкретный тип продукта
               - Сыворотка: конкретный тип продукта
               - Увлажнение: конкретный тип продукта
               - Дополнительный уход: конкретный тип продукта
            6. Полезные ингредиенты и их свойства
            7. Рекомендации по образу жизни для поддержания красоты кожи
            
            В рекомендациях учитывай тип продукта и его особенности. Для кремов дай одни рекомендации, для тоников другие и т.д.
            Рекомендуй реальные типы продуктов для комплексного ухода, которые дополняют данный товар.
            """
            
            # Вызываем API GigaChat для генерации рекомендаций
            messages = [
                {"role": "system", "content": "Ты косметолог-эксперт, который дает профессиональные рекомендации по уходу за кожей."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.gigachat.chat(messages)
            ai_recommendations = response.choices[0].message.content.strip()
            
            # Парсим рекомендации и преобразуем в структурированный формат
            sections = ai_recommendations.split('\n\n')
            daily_care = ""
            weekly_care = ""
            recommendations = ""
            morning_steps = []
            evening_steps = []
            beneficial_ingredients = ""
            lifestyle_recommendations = ""
            
            for section in sections:
                if "Ежедневный уход" in section:
                    daily_care = section.split("Ежедневный уход - ", 1)[-1].strip()
                elif "Еженедельный уход" in section:
                    weekly_care = section.split("Еженедельный уход - ", 1)[-1].strip()
                elif "Общие рекомендации" in section:
                    recommendations = section.split("Общие рекомендации", 1)[-1].strip()
                elif "Утренний уход" in section:
                    # Парсим шаги утреннего ухода
                    lines = section.split('\n')
                    for line in lines:
                        if ':' in line and '-' in line:
                            step_type = line.split('-')[1].split(':')[0].strip()
                            product_type = line.split(':', 1)[1].strip()
                            morning_steps.append({"step": step_type, "product": product_type})
                elif "Вечерний уход" in section:
                    # Парсим шаги вечернего ухода
                    lines = section.split('\n')
                    for line in lines:
                        if ':' in line and '-' in line:
                            step_type = line.split('-')[1].split(':')[0].strip()
                            product_type = line.split(':', 1)[1].strip()
                            evening_steps.append({"step": step_type, "product": product_type})
                elif "Полезные ингредиенты" in section:
                    beneficial_ingredients = section.split("Полезные ингредиенты", 1)[-1].strip()
                elif "Рекомендации по образу жизни" in section:
                    lifestyle_recommendations = section.split("Рекомендации по образу жизни", 1)[-1].strip()
            
            # Если не удалось извлечь данные из ответа, используем значения по умолчанию
            if not morning_steps:
                morning_steps = [
                    {"step": "Очищение", "product": "Очищающий гель для умывания"},
                    {"step": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                    {"step": "Сыворотка", "product": "Сыворотка с гиалуроновой кислотой"},
                    {"step": "Увлажнение", "product": "Увлажняющий крем для лица"},
                    {"step": "Защита", "product": "Солнцезащитный крем SPF 30+"}
                ]
            
            if not evening_steps:
                evening_steps = [
                    {"step": "Очищение", "product": "Очищающий гель для умывания"},
                    {"step": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                    {"step": "Сыворотка", "product": "Ночная восстанавливающая сыворотка"},
                    {"step": "Увлажнение", "product": "Ночной питательный крем"},
                    {"step": "Крем для глаз", "product": "Увлажняющий крем для области вокруг глаз"}
                ]
            
            if not daily_care:
                daily_care = "Используйте продукт ежедневно на очищенную кожу в соответствии с инструкцией."
                
            if not weekly_care:
                weekly_care = "1-2 раза в неделю используйте продукт для более интенсивного ухода."
                
            if not recommendations:
                recommendations = "Для усиления эффекта используйте в комплексе с другими продуктами той же линейки."
                
            if not beneficial_ingredients:
                beneficial_ingredients = "Ищите в составе увлажняющие компоненты, антиоксиданты и активные ингредиенты для вашего типа кожи."
                
            if not lifestyle_recommendations:
                lifestyle_recommendations = "Пейте достаточно воды, защищайте кожу от солнца и соблюдайте здоровое питание для поддержания красоты кожи."
            
            # Формируем структурированный результат
            result = {
                "care_recommendations": {
                    "daily_weekly_recommendations": {
                        "daily_care": daily_care,
                        "weekly_care": weekly_care,
                        "recommendations": recommendations,
                    },
                    "day_night_recommendations": {
                        "morning_care": {
                            "title": "Утренний уход",
                            "steps": morning_steps
                        },
                        "evening_care": {
                            "title": "Вечерний уход",
                            "steps": evening_steps
                        }
                    },
                    "additional_recommendations": {
                        "weekly_care": weekly_care,
                        "additional_care": "Для достижения максимального эффекта дополните уход масками и сыворотками.",
                    },
                    "lifestyle_ingredients": {
                        "lifestyle_recommendations": lifestyle_recommendations,
                        "beneficial_ingredients": beneficial_ingredients,
                    }
                }
            }
            
            # Сохраняем в кэш
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Рекомендации для '{product_name}' сгенерированы с помощью GigaChat и сохранены в кэш")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при генерации рекомендаций с помощью GigaChat: {str(e)}")
            # В случае ошибки возвращаем результат метода с шаблонными рекомендациями
            return await self._generate_recommendations_with_templates(product)
    
    async def _generate_recommendations_with_templates(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует рекомендации по уходу с помощью шаблонов с элементами случайности.
        
        Args:
            product: Данные о товаре
            
        Returns:
            Словарь с рекомендациями
        """
        product_name = product.get('name', '').lower()
        product_brand = product.get('brand', '').lower()
        
        # Базовые варианты для ежедневного ухода
        daily_care_variants = [
            "Используйте продукт ежедневно для лучшего результата. Наносите на очищенную кожу.",
            "Для достижения максимального эффекта применяйте средство ежедневно утром и вечером.",
            "Включите продукт в свой ежедневный уход за кожей, наносите после очищения и тонизирования.",
            "Рекомендуется ежедневное использование для достижения видимых результатов, применяйте на очищенную кожу.",
            "Наносите средство на чистую кожу каждый день для поддержания её здорового состояния."
        ]
        
        # Для еженедельного ухода
        weekly_care_variants = [
            "1-2 раза в неделю используйте продукт для более интенсивного ухода.",
            "Дополнительно 1-2 раза в неделю усиливайте действие продукта, сочетая с другими средствами.",
            "Раз в неделю делайте интенсивный уход с этим средством для достижения лучших результатов.",
            "Еженедельно выделяйте время для более тщательного ухода, чтобы усилить эффект от ежедневного применения.",
            "Для достижения профессионального результата выделите 1-2 дня в неделю для особенно тщательного ухода."
        ]
        
        # Для общих рекомендаций
        recommendations_variants = [
            "Для усиления эффекта используйте в комплексе с другими продуктами той же линейки.",
            "Лучшие результаты достигаются при комплексном подходе к уходу за кожей.",
            "Сочетайте продукт с другими средствами бренда для синергетического эффекта.",
            "Обратите внимание на всю линейку продуктов, они разработаны для совместного применения.",
            "Максимальная эффективность достигается при использовании полной системы ухода."
        ]
        
        # Инициализируем переменную recommendations значением по умолчанию
        recommendations = {
            "daily_care": random.choice(daily_care_variants),
            "weekly_care": random.choice(weekly_care_variants),
            "recommendations": random.choice(recommendations_variants),
            "morning_steps": [
                {"step": "Очищение", "product": "Очищающий гель для умывания"},
                {"step": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                {"step": "Сыворотка", "product": "Сыворотка с гиалуроновой кислотой"},
                {"step": "Увлажнение", "product": "Увлажняющий крем для лица"},
                {"step": "Защита", "product": "Солнцезащитный крем SPF 30+"}
            ],
            "evening_steps": [
                {"step": "Очищение", "product": "Очищающий гель для умывания"},
                {"step": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                {"step": "Сыворотка", "product": "Ночная восстанавливающая сыворотка"},
                {"step": "Увлажнение", "product": "Ночной питательный крем"},
                {"step": "Крем для глаз", "product": "Увлажняющий крем для области вокруг глаз"}
            ],
            "beneficial_ingredients": "Ищите в составе увлажняющие компоненты, антиоксиданты и активные ингредиенты для вашего типа кожи.",
            "lifestyle_recommendations": "Пейте достаточно воды, защищайте кожу от УФ-излучения и следите за питанием для здоровья кожи."
        }
        
        # Данные для утреннего и вечернего ухода зависят от типа продукта
        if 'пудра' in product_name or 'тональн' in product_name:
            # Шаблон для макияжа
            recommendations = {
                "daily_care": random.choice(daily_care_variants),
                "weekly_care": "Раз в неделю делайте день без макияжа, чтобы кожа отдохнула.",
                "recommendations": random.choice(recommendations_variants),
                "morning_steps": [
                    {"step": "Очищение", "product": "Мягкое очищающее средство"},
                    {"step": "Тонизирование", "product": "Тоник для лица"},
                    {"step": "Увлажнение", "product": "Легкий дневной крем"},
                    {"step": "Праймер", "product": "Матирующий праймер"},
                    {"step": "Тональная основа", "product": f"{product.get('brand', 'Качественная')} тональная основа"},
                    {"step": "Фиксация", "product": "Прозрачная пудра"}
                ],
                "evening_steps": [
                    {"step": "Снятие макияжа", "product": "Гидрофильное масло или мицеллярная вода"},
                    {"step": "Очищение", "product": "Пенка для умывания"},
                    {"step": "Тонизирование", "product": "Увлажняющий тоник"},
                    {"step": "Сыворотка", "product": "Восстанавливающая сыворотка"},
                    {"step": "Увлажнение", "product": "Ночной крем для лица"}
                ],
                "beneficial_ingredients": "Ищите в составе увлажняющие компоненты и защиту от солнца SPF.",
                "lifestyle_recommendations": "Пейте достаточно воды, защищайте кожу от УФ-излучения и следите за питанием для здоровья кожи."
            }
        # Добавляем все остальные условия и типы продуктов, которые уже есть в вашем коде
        # ...
        
        # В зависимости от продукта, используем соответствующий шаблон из оригинального метода
        # Для полной имитации генеративного подхода добавляем немного случайности
        
        # Формируем структурированный результат
        result = {
            "care_recommendations": {
                "daily_weekly_recommendations": {
                    "daily_care": recommendations.get("daily_care", random.choice(daily_care_variants)),
                    "weekly_care": recommendations.get("weekly_care", random.choice(weekly_care_variants)),
                    "recommendations": recommendations.get("recommendations", random.choice(recommendations_variants)),
                },
                "day_night_recommendations": {
                    "morning_care": {
                        "title": "Утренний уход",
                        "steps": recommendations.get("morning_steps", [
                            {"step": "Очищение", "product": "Очищающий гель для умывания"},
                            {"step": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                            {"step": "Сыворотка", "product": "Сыворотка с гиалуроновой кислотой"},
                            {"step": "Увлажнение", "product": "Увлажняющий крем для лица"},
                            {"step": "Защита", "product": "Солнцезащитный крем SPF 30+"}
                        ])
                    },
                    "evening_care": {
                        "title": "Вечерний уход",
                        "steps": recommendations.get("evening_steps", [
                            {"step": "Очищение", "product": "Очищающий гель для умывания"},
                            {"step": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                            {"step": "Сыворотка", "product": "Ночная восстанавливающая сыворотка"},
                            {"step": "Увлажнение", "product": "Ночной питательный крем"},
                            {"step": "Крем для глаз", "product": "Увлажняющий крем для области вокруг глаз"}
                        ])
                    }
                },
                "additional_recommendations": {
                    "weekly_care": recommendations.get("weekly_care", random.choice(weekly_care_variants)),
                    "additional_care": "Для достижения максимального эффекта дополните уход масками и сыворотками.",
                },
                "lifestyle_ingredients": {
                    "lifestyle_recommendations": recommendations.get("lifestyle_recommendations", 
                        "Пейте достаточно воды и защищайте кожу от УФ-излучения для поддержания здоровья кожи."),
                    "beneficial_ingredients": recommendations.get("beneficial_ingredients", 
                        "В составе продукта содержатся компоненты, которые увлажняют и питают кожу."),
                }
            }
        }
        
        # Для добавления "интеллектуальности" вставляем бренд продукта в рекомендации
        if product_brand:
            # Случайным образом добавляем упоминание бренда в рекомендации
            mentions = [
                f"Продукты {product_brand} отлично сочетаются между собой в комплексном уходе.",
                f"Для усиления эффекта рекомендуем использовать с другими продуктами {product_brand}.",
                f"Данное средство от {product_brand} демонстрирует лучшие результаты при регулярном применении.",
                f"Бренд {product_brand} разработал эффективную систему ухода, которую стоит использовать полностью."
            ]
            
            result["care_recommendations"]["daily_weekly_recommendations"]["recommendations"] = random.choice(mentions)
        
        return result
    
    async def _generate_skincare_recommendations(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует рекомендации по уходу за кожей.
        Сначала пытается использовать GigaChat, в случае ошибки использует шаблоны с элементами случайности.
        
        Args:
            product: Данные о товаре
            
        Returns:
            Словарь с рекомендациями
        """
        # Пытаемся сгенерировать рекомендации с помощью GigaChat
        if hasattr(self, 'gigachat') and self.gigachat:
            try:
                return await self._generate_recommendations_with_gigachat(product)
            except Exception as e:
                logger.warning(f"Не удалось сгенерировать рекомендации с помощью GigaChat: {str(e)}. Используем шаблонные рекомендации.")
        
        # Если не удалось использовать GigaChat или произошла ошибка, используем шаблоны с элементами случайности
        return await self._generate_recommendations_with_templates(product)

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
        
        # Вызываем метод поиска из WildberriesAPI с await
        try:
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
                    try:
                        product_id = int(product["id"]) if isinstance(product["id"], str) else product["id"]
                        vol = str(product_id)[:4]  # Первые 4 цифры
                        part = str(product_id)[:6]  # Первые 6 цифр
                        
                        # Определяем номер корзины с проверкой существования изображения
                        bucket = await self._find_correct_bucket(product_id)
                        
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Не удалось преобразовать ID товара '{product.get('id')}' в число: {str(e)}")
                        # Используем значения по умолчанию, чтобы не прерывать обработку
                        product_id = 0
                        vol = "0"
                        part = "0"
                        bucket = 1
                    
                    # Формируем URL изображения
                    image_urls = []
                    for i in range(1, 5):  # Получаем первые 4 изображения
                        image_url = f"https://basket-{bucket:02d}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/c516x688/{i}.webp"
                        image_urls.append(image_url)
                    
                    # Генерируем рекомендации по уходу
                    care_recommendations = await self._generate_skincare_recommendations(product)
                    
                    # Строим JSON для товара
                    processed_product = {
                        "id": str(product_id),
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
                        "url": product.get("url", f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"),
                        "description": product.get("description", ""),
                        "gender": gender or "унисекс",
                        "available": product.get("available", True),
                        "care_recommendations": care_recommendations["care_recommendations"]
                    }
                    
                    logger.debug(f"Обработан товар: {processed_product['name']} - Цена: {price}, Скидка: {sale_price}, Процент: {discount}%")
                    products.append(processed_product)
                except Exception as e:
                    logger.error(f"Ошибка при обработке товара {product.get('id')}: {str(e)}")
                    logger.debug(f"Данные товара с ошибкой: {json.dumps(product, ensure_ascii=False, default=str)}")
                    continue
            
            logger.info(f"Найдено {len(products)} товаров по запросу '{query}'")
            return products
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {str(e)}")
            return []
    
    async def search_products(
        self, 
        query: str, 
        limit: int = 10,
        min_price: Optional[float] = None, 
        max_price: Optional[float] = None,
        gender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск товаров по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество товаров в результате
            min_price: Минимальная цена (если указана)
            max_price: Максимальная цена (если указана)
            gender: Пол (мужской, женский, унисекс)
            
        Returns:
            Список товаров, соответствующих запросу
        """
        try:
            logger.info(f"Поиск товаров: '{query}', лимит: {limit}, мин. цена: {min_price}, макс. цена: {max_price}, пол: {gender}")
            
            # Преобразуем параметры для совместимости с API
            low_price = int(min_price) if min_price is not None else None
            top_price = int(max_price) if max_price is not None else None
            
            # Вызываем метод поиска из WildberriesAPI с await
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
                    
                    # Преобразуем id в число для корректного формирования URL
                    try:
                        product_id = int(product.get('id')) if isinstance(product.get('id'), str) else product.get('id')
                        vol = str(product_id)[:4]  # Первые 4 цифры
                        part = str(product_id)[:6]  # Первые 6 цифр
                        
                        # Определяем номер корзины с проверкой существования изображения
                        bucket = await self._find_correct_bucket(product_id)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Не удалось преобразовать ID товара '{product.get('id')}' в число: {str(e)}")
                        # Используем исходное значение
                        product_id = product.get('id', 0)
                        vol = "0"
                        part = "0"
                        bucket = 1
                    
                    # Формируем URL изображения
                    image_urls = []
                    for i in range(1, 5):  # Получаем первые 4 изображения
                        image_url = f"https://basket-{bucket:02d}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/c516x688/{i}.webp"
                        image_urls.append(image_url)
                    
                    # Генерируем рекомендации по уходу
                    care_recommendations = await self._generate_skincare_recommendations(product)
                    
                    processed_product = {
                        'id': product_id,
                        'name': product.get('name'),
                        'brand': product.get('brand'),
                        'price': price,
                        'sale_price': sale_price,
                        'discount': discount,
                        'rating': product.get('rating', 0),
                        'image_url': image_urls[0] if image_urls else None,
                        'image_urls': image_urls,
                        'product_url': f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                        'gender': gender or "унисекс",
                        'care_recommendations': care_recommendations["care_recommendations"]
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
        if self._session and not self._session.closed:
            await self._session.close()
            
        if hasattr(self.api, 'close'):
            try:
                await self.api.close()
            except Exception as e:
                logger.error(f"Ошибка при закрытии API клиента: {str(e)}") 