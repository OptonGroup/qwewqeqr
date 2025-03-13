"""
Модуль для работы с Pinterest без авторизации.
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
from bs4 import BeautifulSoup
import re
import hashlib
import urllib.parse
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from selenium.common.exceptions import TimeoutException
import aiofiles

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pinterest.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Класс для определения одежды на изображении
class ImageAnalyzer:
    """Класс для анализа изображений и определения одежды."""
    
    CLOTHING_TYPES = [
        "футболка", "рубашка", "блузка", "топ", "водолазка", "свитер", "свитшот", "худи", 
        "джемпер", "кардиган", "жакет", "пиджак", "блейзер", "куртка", "пальто", "плащ", 
        "шуба", "джинсы", "брюки", "шорты", "юбка", "платье", "сарафан", "комбинезон", 
        "кроссовки", "кеды", "туфли", "ботинки", "сапоги", "босоножки", "сандалии",
        "шапка", "кепка", "шляпа", "берет", "шарф", "перчатки", "сумка", "рюкзак",
        "бейсболка", "джоггеры", "лосины", "легинсы", "пуховик", "жилет", "тренч", "поло"
    ]
    
    COLORS = [
        "черный", "белый", "красный", "синий", "зеленый", "желтый", "оранжевый", 
        "фиолетовый", "розовый", "голубой", "бирюзовый", "коричневый", "бежевый", 
        "серый", "хаки", "бордовый", "золотой", "серебряный", "темно-синий", 
        "светло-синий", "темно-красный", "светло-зеленый"
    ]
    
    # Словарь для предварительно настроенных результатов анализа по ключевым словам
    OUTFITS_CATEGORIES = {
        "офисный стиль женский": [
            {"type": "пиджак", "color": "черный", "description": "классический прямой", "gender": "женский"},
            {"type": "блузка", "color": "белая", "description": "с воротником", "gender": "женский"},
            {"type": "юбка", "color": "черная", "description": "прямая до колена", "gender": "женский"}
        ],
        "повседневный образ женский": [
            {"type": "джинсы", "color": "синие", "description": "скинни", "gender": "женский"},
            {"type": "футболка", "color": "белая", "description": "базовая", "gender": "женский"},
            {"type": "кеды", "color": "белые", "description": "классические", "gender": "женский"}
        ],
        "повседневный образ мужской": [
            {"type": "джинсы", "color": "синие", "description": "прямые", "gender": "мужской"},
            {"type": "футболка", "color": "черная", "description": "свободного кроя", "gender": "мужской"},
            {"type": "кроссовки", "color": "белые", "description": "городские", "gender": "мужской"}
        ],
        "повседневный образ": [
            {"type": "джинсы", "color": "синие", "description": "прямые", "gender": "унисекс"},
            {"type": "футболка", "color": "белая", "description": "базовая", "gender": "унисекс"},
            {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": "унисекс"}
        ],
        "деловой стиль мужской": [
            {"type": "костюм", "color": "темно-синий", "description": "классический", "gender": "мужской"},
            {"type": "рубашка", "color": "белая", "description": "с длинным рукавом", "gender": "мужской"},
            {"type": "туфли", "color": "черные", "description": "классические", "gender": "мужской"}
        ],
        "деловой стиль": [
            {"type": "костюм", "color": "темно-синий", "description": "классический", "gender": "мужской"},
            {"type": "рубашка", "color": "белая", "description": "с длинным рукавом", "gender": "мужской"},
            {"type": "туфли", "color": "черные", "description": "классические", "gender": "мужской"}
        ],
        "вечерний образ женский": [
            {"type": "платье", "color": "черное", "description": "вечернее", "gender": "женский"},
            {"type": "туфли", "color": "черные", "description": "на высоком каблуке", "gender": "женский"},
            {"type": "сумка", "color": "черная", "description": "клатч", "gender": "женский"}
        ],
        "вечерний образ мужской": [
            {"type": "костюм", "color": "черный", "description": "смокинг", "gender": "мужской"},
            {"type": "рубашка", "color": "белая", "description": "вечерняя", "gender": "мужской"},
            {"type": "бабочка", "color": "черная", "description": "шелковая", "gender": "мужской"},
            {"type": "туфли", "color": "черные", "description": "лакированные", "gender": "мужской"}
        ],
        "вечерний образ": [
            {"type": "платье", "color": "черное", "description": "вечернее", "gender": "женский"},
            {"type": "туфли", "color": "черные", "description": "на высоком каблуке", "gender": "женский"},
            {"type": "сумка", "color": "черная", "description": "клатч", "gender": "женский"}
        ],
        "спортивный стиль мужской": [
            {"type": "толстовка", "color": "серая", "description": "спортивная с капюшоном", "gender": "мужской"},
            {"type": "футболка", "color": "белая", "description": "спортивная", "gender": "мужской"},
            {"type": "брюки", "color": "черные", "description": "спортивные", "gender": "мужской"},
            {"type": "кроссовки", "color": "белые", "description": "беговые", "gender": "мужской"}
        ],
        "спортивный стиль женский": [
            {"type": "леггинсы", "color": "черные", "description": "спортивные", "gender": "женский"},
            {"type": "топ", "color": "розовый", "description": "спортивный", "gender": "женский"},
            {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": "женский"}
        ],
        "спортивный стиль": [
            {"type": "толстовка", "color": "серая", "description": "спортивная с капюшоном", "gender": "унисекс"},
            {"type": "брюки", "color": "черные", "description": "спортивные", "gender": "унисекс"},
            {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": "унисекс"}
        ],
        "летний женский": [
            {"type": "платье", "color": "голубое", "description": "летнее", "gender": "женский"},
            {"type": "сандалии", "color": "бежевые", "description": "легкие", "gender": "женский"},
            {"type": "сумка", "color": "соломенная", "description": "пляжная", "gender": "женский"}
        ],
        "летний мужской": [
            {"type": "шорты", "color": "бежевые", "description": "легкие", "gender": "мужской"},
            {"type": "рубашка", "color": "голубая", "description": "с коротким рукавом", "gender": "мужской"},
            {"type": "шлепанцы", "color": "коричневые", "description": "кожаные", "gender": "мужской"}
        ],
        "летний": [
            {"type": "шорты", "color": "голубые", "description": "джинсовые", "gender": "унисекс"},
            {"type": "футболка", "color": "белая", "description": "свободная", "gender": "унисекс"},
            {"type": "сандалии", "color": "коричневые", "description": "кожаные", "gender": "унисекс"}
        ],
        "зимний мужской": [
            {"type": "пуховик", "color": "черный", "description": "длинный", "gender": "мужской"},
            {"type": "свитер", "color": "серый", "description": "теплый", "gender": "мужской"},
            {"type": "ботинки", "color": "коричневые", "description": "зимние", "gender": "мужской"},
            {"type": "шапка", "color": "черная", "description": "вязаная", "gender": "мужской"}
        ],
        "зимний женский": [
            {"type": "пуховик", "color": "белый", "description": "длинный", "gender": "женский"},
            {"type": "свитер", "color": "бежевый", "description": "объемный", "gender": "женский"},
            {"type": "сапоги", "color": "черные", "description": "зимние", "gender": "женский"},
            {"type": "шапка", "color": "белая", "description": "вязаная", "gender": "женский"}
        ],
        "зимний образ": [
            {"type": "пуховик", "color": "черный", "description": "теплый", "gender": "унисекс"},
            {"type": "свитер", "color": "серый", "description": "вязаный", "gender": "унисекс"},
            {"type": "ботинки", "color": "коричневые", "description": "зимние", "gender": "унисекс"},
            {"type": "шапка", "color": "черная", "description": "вязаная", "gender": "унисекс"}
        ],
        "мужской образ": [
            {"type": "брюки", "color": "синие", "description": "джинсовые", "gender": "мужской"},
            {"type": "рубашка", "color": "голубая", "description": "повседневная", "gender": "мужской"},
            {"type": "кроссовки", "color": "белые", "description": "городские", "gender": "мужской"}
        ],
        "женский образ": [
            {"type": "платье", "color": "синее", "description": "повседневное", "gender": "женский"},
            {"type": "туфли", "color": "бежевые", "description": "на среднем каблуке", "gender": "женский"},
            {"type": "сумка", "color": "коричневая", "description": "повседневная", "gender": "женский"}
        ]
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Инициализация анализатора изображений.
        
        Args:
            openai_api_key: API ключ OpenAI (если не указан, будет взят из переменной окружения OPENAI_API_KEY)
        """
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self._cache_dir = Path("vision_cache")
        self._cache_dir.mkdir(exist_ok=True)
        self._cache = {}
        self._load_cache()
        self._api_available = True  # Флаг доступности API
        
        logger.info("Анализатор изображений инициализирован")
    
    def _load_cache(self) -> None:
        """Загружает кеш из файла."""
        try:
            cache_file = self._cache_dir / "vision_cache.json"
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Загружен кеш с {len(self._cache)} записями")
            else:
                self._cache = {}
                logger.info("Создан новый кеш для анализа изображений")
        except Exception as e:
            logger.error(f"Ошибка при загрузке кеша анализа изображений: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Сохраняет кеш в файл."""
        try:
            cache_file = self._cache_dir / "vision_cache.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.info("Кеш анализа изображений сохранен")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кеша анализа изображений: {e}")
    
    def _get_url_hash(self, url: str) -> str:
        """Генерирует хеш URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _generate_fallback_clothing_items(self, query: str, gender: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Генерирует предметы одежды на основе запроса, когда API OpenAI недоступен.
        
        Args:
            query: Поисковый запрос
            gender: Пол (мужской/женский)
            
        Returns:
            Список предметов одежды
        """
        # Приводим запрос к нижнему регистру для лучшего сопоставления
        query_lower = query.lower()
        gender = gender.lower() if gender else 'унисекс'
        is_male = gender == 'мужской'
        is_female = gender == 'женский'
        
        # Сначала проверяем корректное сопоставление по полу и категории
        if "деловой" in query_lower or "офисный" in query_lower or "бизнес" in query_lower:
            if is_male:
                # Для мужского делового стиля используем предустановленную категорию
                logger.info(f"Используем предустановленные предметы категории 'деловой стиль мужской'")
                return self.OUTFITS_CATEGORIES["деловой стиль мужской"]
            elif is_female:
                # Для женского офисного стиля используем предустановленную категорию
                logger.info(f"Используем предустановленные предметы категории 'офисный стиль женский'")
                return self.OUTFITS_CATEGORIES["офисный стиль женский"]
        
        # Проверяем соответствие запроса предустановленным категориям
        for category, items in self.OUTFITS_CATEGORIES.items():
            # Проверяем, что категория соответствует запросу И указанному полу
            category_lower = category.lower()
            if any(word in query_lower for word in category_lower.split()):
                # Проверяем соответствие пола
                category_gender = None
                if "мужской" in category_lower:
                    category_gender = "мужской"
                elif "женский" in category_lower:
                    category_gender = "женский"
                
                # Если пол категории указан и не соответствует запрошенному, пропускаем
                if category_gender and gender != "унисекс" and category_gender != gender:
                    continue
                
                # Если запрос соответствует категории, возвращаем предустановленные предметы
                # Учитываем указанный пол, если он задан
                if gender:
                    filtered_items = [
                        item for item in items 
                        if item["gender"] == gender or item["gender"] == "унисекс"
                    ]
                    if filtered_items:
                        logger.info(f"Используем предустановленные предметы категории '{category}' для пола '{gender}'")
                        return filtered_items
                    
                logger.info(f"Используем все предустановленные предметы категории '{category}'")
                return items
        
        # Если нет соответствия категориям, генерируем базовые наборы по стилю и полу
        if "деловой" in query_lower or "офисный" in query_lower or "бизнес" in query_lower:
            if is_male:
                logger.info("Генерируем деловой мужской образ")
                return [
                    {"type": "костюм", "color": "темно-синий", "description": "классический", "gender": "мужской"},
                    {"type": "рубашка", "color": "белая", "description": "с длинным рукавом", "gender": "мужской"},
                    {"type": "галстук", "color": "синий", "description": "в полоску", "gender": "мужской"},
                    {"type": "туфли", "color": "черные", "description": "классические", "gender": "мужской"}
                ]
            elif is_female:
                logger.info("Генерируем деловой женский образ")
                return [
                    {"type": "пиджак", "color": "черный", "description": "классический прямой", "gender": "женский"},
                    {"type": "блузка", "color": "белая", "description": "с воротником", "gender": "женский"},
                    {"type": "юбка", "color": "черная", "description": "прямая до колена", "gender": "женский"},
                    {"type": "туфли", "color": "черные", "description": "на среднем каблуке", "gender": "женский"}
                ]
        
        elif "повседневный" in query_lower or "casual" in query_lower:
            if is_male:
                logger.info("Генерируем повседневный мужской образ")
                return [
                    {"type": "джинсы", "color": "синие", "description": "прямые", "gender": "мужской"},
                    {"type": "футболка", "color": "белая", "description": "хлопковая", "gender": "мужской"},
                    {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": "мужской"}
                ]
            elif is_female:
                logger.info("Генерируем повседневный женский образ")
                return [
                    {"type": "джинсы", "color": "синие", "description": "скинни", "gender": "женский"},
                    {"type": "футболка", "color": "белая", "description": "базовая", "gender": "женский"},
                    {"type": "кеды", "color": "белые", "description": "классические", "gender": "женский"}
                ]
        
        elif "спортивный" in query_lower:
            if is_male:
                logger.info("Генерируем спортивный мужской образ")
                return [
                    {"type": "толстовка", "color": "серая", "description": "спортивная с капюшоном", "gender": "мужской"},
                    {"type": "футболка", "color": "белая", "description": "спортивная", "gender": "мужской"},
                    {"type": "брюки", "color": "черные", "description": "спортивные", "gender": "мужской"},
                    {"type": "кроссовки", "color": "белые", "description": "беговые", "gender": "мужской"}
                ]
            elif is_female:
                logger.info("Генерируем спортивный женский образ")
                return [
                    {"type": "худи", "color": "серый", "description": "спортивный с капюшоном", "gender": "женский"},
                    {"type": "леггинсы", "color": "черные", "description": "спортивные", "gender": "женский"},
                    {"type": "кроссовки", "color": "белые", "description": "беговые", "gender": "женский"}
                ]
        
        elif "вечерний" in query_lower:
            if is_male:
                logger.info("Генерируем вечерний мужской образ")
                return [
                    {"type": "костюм", "color": "черный", "description": "вечерний", "gender": "мужской"},
                    {"type": "рубашка", "color": "белая", "description": "классическая", "gender": "мужской"},
                    {"type": "бабочка", "color": "черная", "description": "классическая", "gender": "мужской"},
                    {"type": "туфли", "color": "черные", "description": "кожаные", "gender": "мужской"}
                ]
            elif is_female:
                logger.info("Генерируем вечерний женский образ")
                return [
                    {"type": "платье", "color": "черное", "description": "вечернее", "gender": "женский"},
                    {"type": "туфли", "color": "черные", "description": "на высоком каблуке", "gender": "женский"},
                    {"type": "сумка", "color": "черная", "description": "клатч", "gender": "женский"},
                    {"type": "украшения", "color": "серебристые", "description": "вечерние", "gender": "женский"}
                ]
        
        elif "зимний" in query_lower:
            if is_male:
                logger.info("Генерируем зимний мужской образ")
                return [
                    {"type": "пуховик", "color": "черный", "description": "зимний", "gender": "мужской"},
                    {"type": "свитер", "color": "серый", "description": "теплый", "gender": "мужской"},
                    {"type": "джинсы", "color": "синие", "description": "утепленные", "gender": "мужской"},
                    {"type": "ботинки", "color": "коричневые", "description": "зимние", "gender": "мужской"},
                    {"type": "шапка", "color": "черная", "description": "вязаная", "gender": "мужской"}
                ]
            elif is_female:
                logger.info("Генерируем зимний женский образ")
                return [
                    {"type": "пуховик", "color": "белый", "description": "зимний", "gender": "женский"},
                    {"type": "свитер", "color": "бежевый", "description": "теплый", "gender": "женский"},
                    {"type": "джинсы", "color": "синие", "description": "утепленные", "gender": "женский"},
                    {"type": "сапоги", "color": "черные", "description": "зимние", "gender": "женский"},
                    {"type": "шапка", "color": "белая", "description": "вязаная", "gender": "женский"}
                ]
        
        elif "летний" in query_lower:
            if is_male:
                logger.info("Генерируем летний мужской образ")
                return [
                    {"type": "футболка", "color": "белая", "description": "хлопковая", "gender": "мужской"},
                    {"type": "шорты", "color": "бежевые", "description": "летние", "gender": "мужской"},
                    {"type": "кеды", "color": "белые", "description": "легкие", "gender": "мужской"},
                    {"type": "кепка", "color": "синяя", "description": "летняя", "gender": "мужской"}
                ]
            elif is_female:
                logger.info("Генерируем летний женский образ")
                return [
                    {"type": "платье", "color": "голубое", "description": "летнее", "gender": "женский"},
                    {"type": "сандалии", "color": "бежевые", "description": "летние", "gender": "женский"},
                    {"type": "сумка", "color": "соломенная", "description": "летняя", "gender": "женский"},
                    {"type": "шляпа", "color": "бежевая", "description": "летняя", "gender": "женский"}
                ]
                
        # Если ничего не подошло, используем базовые наборы в зависимости от пола
        if is_male:
            logger.info("Генерируем базовый мужской образ")
            return [
                {"type": "рубашка", "color": "голубая", "description": "классическая", "gender": "мужской"},
                {"type": "брюки", "color": "темно-синие", "description": "классические", "gender": "мужской"},
                {"type": "туфли", "color": "коричневые", "description": "классические", "gender": "мужской"}
            ]
        elif is_female:
            logger.info("Генерируем базовый женский образ")
            return [
                {"type": "блузка", "color": "белая", "description": "классическая", "gender": "женский"},
                {"type": "юбка", "color": "черная", "description": "классическая", "gender": "женский"},
                {"type": "туфли", "color": "черные", "description": "на каблуке", "gender": "женский"}
            ]
        else:
            # Унисекс вариант для остальных случаев
            logger.info("Генерируем унисекс образ")
            return [
                {"type": "футболка", "color": "белая", "description": "базовая", "gender": "унисекс"},
                {"type": "джинсы", "color": "синие", "description": "классические", "gender": "унисекс"},
                {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": "унисекс"}
            ]
    
    async def analyze_image(self, image_url: str, gender: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Анализирует изображение для определения одежды, используя локальные методы.
        
        Args:
            image_url: URL изображения для анализа
            gender: Пол (мужской/женский)
            query: Поисковый запрос, используемый для нахождения этого изображения
        
        Returns:
            Список предметов одежды
        """
        try:
            # Проверяем кеш
            url_hash = self._get_url_hash(image_url)
            if url_hash in self._cache:
                logger.info(f"Использую кеш для {image_url}")
                return self._cache[url_hash]
            
            # Всегда используем локальный метод анализа, вместо OpenAI API
            logger.info(f"Использую локальный метод анализа для {image_url}")
            
            # Анализируем контекст запроса для определения категории одежды
            query_lower = query.lower() if query else ""
            
            # Определяем ключевые слова в запросе
            has_office = any(word in query_lower for word in ["офисный", "деловой", "формальный", "бизнес", "работа", "офис"])
            has_casual = any(word in query_lower for word in ["повседневный", "casual", "ежедневный", "обычный"])
            has_sport = any(word in query_lower for word in ["спортивный", "тренировка", "фитнес", "спорт"])
            has_evening = any(word in query_lower for word in ["вечерний", "праздничный", "нарядный", "выход"])
            has_summer = any(word in query_lower for word in ["летний", "лето", "пляж", "жара"])
            has_winter = any(word in query_lower for word in ["зимний", "зима", "холод", "мороз"])
            
            # Определяем пол из запроса, если он не был явно указан
            if not gender:
                has_male = any(word in query_lower for word in ["мужской", "мужчина", "мужские", "мужское", "мужская", "муж"])
                has_female = any(word in query_lower for word in ["женский", "женщина", "женские", "женское", "женская", "жен"])
                
                if has_male and not has_female:
                    gender = "мужской"
                    logger.info(f"Определен пол из запроса: {gender}")
                elif has_female and not has_male:
                    gender = "женский"
                    logger.info(f"Определен пол из запроса: {gender}")
            
            # Определяем категорию на основе ключевых слов
            category = None
            if has_office:
                if gender == "мужской":
                    category = "деловой стиль мужской"
                elif gender == "женский":
                    category = "офисный стиль женский"
                else:
                    # Если пол не определен, пытаемся выяснить из контекста
                    category = "деловой стиль"
            elif has_casual:
                category = "повседневный образ"
            elif has_sport:
                category = "спортивный стиль"
            elif has_evening:
                category = "вечерний образ"
            elif has_summer:
                category = "летний"
            elif has_winter:
                category = "зимний образ"
            
            # Если категория не определена, но есть пол, добавляем его к запросу
            if not category and gender:
                category = f"{gender} образ"
            
            # Генерируем предметы одежды на основе категории и пола
            logger.info(f"Определена категория: {category or 'не определена'}, пол: {gender or 'не определен'}")
            
            result = self._generate_fallback_clothing_items(category or query, gender)
            
            # Сохраняем результат в кеш
            self._cache[url_hash] = result
            self._save_cache()
            
            # Определяем количество предметов
            count = len(result)
            logger.info(f"Определено {count} предметов одежды")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {e}")
            # В случае ошибки возвращаем минимальный набор одежды
            return [{"type": "одежда", "color": "неизвестно", "description": "не удалось определить", "gender": gender or "унисекс"}]
    
    @staticmethod
    def is_clothing_item(text: str) -> bool:
        """
        Проверяет, является ли текст названием предмета одежды.
        
        Args:
            text: Текст для проверки
            
        Returns:
            True, если текст - название предмета одежды, иначе False
        """
        lower_text = text.lower()
        return any(clothing_type in lower_text for clothing_type in ImageAnalyzer.CLOTHING_TYPES)

class PinInfo(BaseModel):
    """Модель для хранения информации о пине."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: str
    link: Optional[str] = None
    source_url: Optional[str] = None
    board: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    saved_path: Optional[str] = None
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    clothing_items: List[Dict[str, str]] = Field(default_factory=list)
    
    def dict(self, *args, **kwargs):
        """Переопределяем метод dict для корректной сериализации в JSON."""
        d = super().dict(*args, **kwargs)
        # Убеждаемся, что last_updated всегда строка
        if isinstance(d['last_updated'], datetime):
            d['last_updated'] = d['last_updated'].isoformat()
        return d

class PinterestAPI:
    """Класс для работы с Pinterest без авторизации."""
    
    SEARCH_URL = "https://www.pinterest.com/search/pins"
    
    def __init__(self, download_dir: str = "photo", openai_api_key: Optional[str] = None):
        """
        Инициализация клиента Pinterest API.
        
        Args:
            download_dir: Директория для сохранения изображений
            openai_api_key: API ключ OpenAI для анализа изображений
        """
        self._session: Optional[aiohttp.ClientSession] = None
        self._driver: Optional[webdriver.Chrome] = None
        self._download_dir = Path(download_dir)
        self._download_dir.mkdir(exist_ok=True)
        self._cache_dir = Path("pinterest_cache")
        self._cache_dir.mkdir(exist_ok=True)
        
        # Инициализация анализатора изображений
        self.image_analyzer = ImageAnalyzer(openai_api_key)
        
        # Загружаем кеш
        self._load_cache()
        logger.info("Pinterest API клиент инициализирован")
    
    async def _init_selenium(self):
        """Инициализация Selenium WebDriver."""
        if self._driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--remote-debugging-port=9222")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-notifications")
                chrome_options.add_argument("--disable-popup-blocking")
                chrome_options.add_argument('--ignore-certificate-errors')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # Список возможных путей к Chrome
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
                    r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
                    r"C:\Program Files\Google\Chrome Dev\Application\chrome.exe",
                ]
                
                # Поиск Chrome в системе
                chrome_binary = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_binary = path
                        logger.info(f"Найден Chrome по пути: {path}")
                        break
                
                if not chrome_binary:
                    # Попытка найти Chrome через реестр Windows
                    try:
                        import winreg
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                            chrome_binary = winreg.QueryValue(key, None)
                            logger.info(f"Найден Chrome через реестр: {chrome_binary}")
                    except Exception as e:
                        logger.warning(f"Не удалось найти Chrome через реестр: {e}")
                
                if not chrome_binary:
                    # Попытка автоматической установки Chrome
                    try:
                        logger.info("Попытка автоматической установки Chrome...")
                        import subprocess
                        import tempfile
                        import urllib.request
                        
                        # URL для скачивания Chrome
                        chrome_url = "https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe"
                        
                        # Создаем временную директорию
                        with tempfile.TemporaryDirectory() as temp_dir:
                            installer_path = os.path.join(temp_dir, "chrome_installer.exe")
                            
                            # Скачиваем установщик
                            logger.info("Скачивание установщика Chrome...")
                            urllib.request.urlretrieve(chrome_url, installer_path)
                            
                            # Запускаем установку
                            logger.info("Запуск установки Chrome...")
                            subprocess.run([installer_path, "/silent", "/install"], 
                                        check=True, 
                                        capture_output=True)
                            
                            logger.info("Chrome успешно установлен")
                            
                            # Проверяем стандартный путь установки
                            chrome_binary = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                            if not os.path.exists(chrome_binary):
                                chrome_binary = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                            
                    except Exception as e:
                        logger.error(f"Ошибка при установке Chrome: {e}")
                        raise Exception("Не удалось установить Chrome. Пожалуйста, установите его вручную.")
                
                if chrome_binary and os.path.exists(chrome_binary):
                    chrome_options.binary_location = chrome_binary
                else:
                    logger.error("Chrome не найден и не может быть установлен")
                    raise Exception("Chrome не найден и не может быть установлен. Пожалуйста, установите Chrome вручную.")
                
                # Создаем сервис с увеличенным таймаутом
                service = Service(
                    ChromeDriverManager().install(),
                    service_args=['--verbose'],
                    log_path='chromedriver.log'
                )
                
                # Создаем драйвер с увеличенным таймаутом
                self._driver = webdriver.Chrome(
                    service=service,
                    options=chrome_options
                )
                
                # Устанавливаем таймауты
                self._driver.set_page_load_timeout(60)
                self._driver.implicitly_wait(20)
                
                logger.info("Selenium WebDriver успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Selenium: {e}")
                if self._driver:
                    self._driver.quit()
                    self._driver = None
                raise
    
    def _load_cache(self) -> None:
        """Загружает кеш из файла."""
        try:
            cache_file = self._cache_dir / "pins_cache.json"
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Загружен кеш с {len(self._cache)} пинами")
            else:
                self._cache = {}
                logger.info("Создан новый кеш")
        except Exception as e:
            logger.error(f"Ошибка при загрузке кеша: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Сохраняет кеш в файл."""
        try:
            cache_file = self._cache_dir / "pins_cache.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.info("Кеш сохранен")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кеша: {e}")
    
    def _get_file_hash(self, url: str) -> str:
        """
        Генерирует хеш для URL изображения.
        
        Args:
            url: URL изображения
            
        Returns:
            Хеш URL
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    async def _init_session(self):
        """Инициализация HTTP сессии."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            logger.info("HTTP сессия инициализирована")
    
    async def _download_image(self, url: str) -> Optional[str]:
        """
        Скачивает изображение и сохраняет его локально.
        
        Args:
            url: URL изображения для скачивания
            
        Returns:
            Путь к сохраненному файлу или None при ошибке
        """
        try:
            # Проверяем кеш
            file_hash = self._get_file_hash(url)
            cached_path = os.path.join(self._download_dir, f"{file_hash}.jpg")
            
            # Если файл уже существует, возвращаем путь
            if os.path.exists(cached_path):
                return cached_path
            
            # Если сессия не инициализирована, создаем ее
            if not hasattr(self, '_session') or self._session is None:
                await self._init_session()
            
            # Создаем каталог, если он не существует
            os.makedirs(self._download_dir, exist_ok=True)
            
            # Добавляем случайный User-Agent и Referer для обхода блокировки
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
                ]),
                'Referer': 'https://www.pinterest.com/',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            
            # Скачиваем файл
            async with self._session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    # Если получили ошибку 403, пробуем альтернативный URL
                    if response.status == 403:
                        logger.error(f"Ошибка при скачивании изображения: {response.status}")
                        
                        # Пробуем модифицированный URL
                        modified_url = url
                        # Заменяем параметры размера в URL
                        for size in ['236x', '474x', '736x', 'orig']:
                            if size in modified_url:
                                # Пробуем разные размеры
                                for new_size in ['orig', '736x', '564x', '474x', '236x']:
                                    if new_size != size:
                                        alt_url = modified_url.replace(size, new_size)
                                        logger.info(f"Пробуем альтернативный URL с размером {new_size}: {alt_url}")
                                        try:
                                            async with self._session.get(alt_url, headers=headers, timeout=30) as alt_response:
                                                if alt_response.status == 200:
                                                    content = await alt_response.read()
                                                    async with aiofiles.open(cached_path, 'wb') as f:
                                                        await f.write(content)
                                                    logger.info(f"Изображение сохранено: {cached_path}")
                                                    return cached_path
                                        except Exception as e:
                                            logger.error(f"Ошибка при скачивании альтернативного URL: {e}")
                        
                        # Пробуем с другими заголовками
                        try:
                            alt_headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                                'Referer': 'https://www.google.com/',
                            }
                            async with self._session.get(url, headers=alt_headers, timeout=30) as alt_response:
                                if alt_response.status == 200:
                                    content = await alt_response.read()
                                    async with aiofiles.open(cached_path, 'wb') as f:
                                        await f.write(content)
                                    logger.info(f"Изображение сохранено с альтернативными заголовками: {cached_path}")
                                    return cached_path
                        except Exception as e:
                            logger.error(f"Ошибка при скачивании с альтернативными заголовками: {e}")
                        
                        return None
                    else:
                        logger.error(f"Ошибка при скачивании изображения: {response.status}")
                        return None
                
                content = await response.read()
                async with aiofiles.open(cached_path, 'wb') as f:
                    await f.write(content)
                
                logger.info(f"Изображение сохранено: {cached_path}")
                return cached_path
        
        except Exception as e:
            logger.error(f"Ошибка при скачивании изображения: {e}")
            return None

    def _get_best_image_url(self, img_element) -> Optional[str]:
        """
        Получает URL изображения наилучшего качества.
        
        Args:
            img_element: Элемент изображения
            
        Returns:
            URL изображения наилучшего качества или None
        """
        try:
            # Пробуем получить оригинальное изображение через data-src-original
            image_url = img_element.get_attribute('data-src-original')
            if image_url and image_url.startswith('http'):
                return image_url
            
            # Пробуем получить большое изображение через data-big-pin
            image_url = img_element.get_attribute('data-big-pin')
            if image_url and image_url.startswith('http'):
                return image_url
                
            # Пробуем получить изображение через srcset
            srcset = img_element.get_attribute('srcset')
            if srcset:
                # Парсим srcset и находим URL с максимальным размером
                urls_with_sizes = []
                for part in srcset.split(','):
                    part = part.strip()
                    if not part:
                        continue
                    
                    # Разбиваем на URL и размер
                    parts = part.split(' ')
                    if len(parts) >= 2:
                        url = parts[0]
                        # Извлекаем числовое значение размера
                        size = ''.join(filter(str.isdigit, parts[1]))
                        if size:
                            urls_with_sizes.append((url, int(size)))
                
                # Сортируем по размеру и берем самый большой
                if urls_with_sizes:
                    urls_with_sizes.sort(key=lambda x: x[1], reverse=True)
                    return urls_with_sizes[0][0]
            
            # Пробуем получить через src
            image_url = img_element.get_attribute('src')
            if image_url and image_url.startswith('http'):
                # Пробуем улучшить качество изображения, заменяя параметры размера
                image_url = re.sub(r'/\d+x/|/\d+x\d+/', '/originals/', image_url)
                return image_url
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении URL изображения: {e}")
            return None
        
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_pins(
        self,
        query: str,
        limit: int = 10,
        download: bool = True,
        analyze_images: bool = False,
        gender: Optional[str] = None
    ) -> List[PinInfo]:
        """
        Поиск пинов по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            download: Скачивать ли изображения
            analyze_images: Анализировать ли изображения для определения одежды
            gender: Пол (мужской/женский)
            
        Returns:
            Список объектов PinInfo с информацией о найденных пинах
        """
        # Проверяем кеш
        cache_key = f"{query}_{limit}_{gender or 'unspecified'}"
        if cache_key in self._cache:
            logger.info(f"Использую кеш для запроса '{query}'")
            pins = self._cache[cache_key]
            
            # Если нужно проанализировать изображения, делаем это для тех, у которых нет списка предметов
            if analyze_images:
                for pin in pins:
                    if not pin.clothing_items:
                        logger.info(f"Анализирую изображение из кеша для пина {pin.id}")
                        pin.clothing_items = await self.image_analyzer.analyze_image(
                            pin.image_url, gender, query
                        )
                self._cache[cache_key] = pins
                self._save_cache()
                
            return pins
        
        # Если кеша нет, выполняем поиск
        if not self._driver:
            await self._init_selenium()
        
        search_url = f"{self.SEARCH_URL}/?q={urllib.parse.quote_plus(query)}"
        logger.info(f"Загружаем страницу поиска: {search_url}")
        
        # Увеличиваем максимальное время ожидания страницы до 60 секунд
        try:
            # Selenium WebDriver работает синхронно, не используем await
            self._driver.set_page_load_timeout(60)  # 60 секунд
            self._driver.get(search_url)
        except Exception as e:
            logger.error(f"Ошибка при загрузке страницы поиска: {e}")
            # Пробуем еще раз с небольшой задержкой
            await asyncio.sleep(2)
            try:
                self._driver.get(search_url)
            except Exception as e:
                logger.error(f"Повторная ошибка при загрузке страницы: {e}")
                return []
        
        # Ожидаем загрузку контента
        try:
            logger.info("Ждем загрузку контента...")
            WebDriverWait(self._driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='pin']"))
            )
            logger.info("Найден селектор: div[data-test-id='pin']")
        except TimeoutException:
            logger.warning("Тайм-аут ожидания элементов пинов, попробуем найти альтернативные элементы")
            try:
                # Пробуем альтернативный селектор
                WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-grid-item]"))
                )
                logger.info("Найден альтернативный селектор: div[data-grid-item]")
            except TimeoutException:
                logger.error("Не удалось найти элементы пинов даже с альтернативным селектором")
                return []
        
        # Прокручиваем страницу, чтобы загрузить больше изображений
        logger.info("Страница загружена, прокручиваем для загрузки изображений")
        try:
            # Прокручиваем страницу несколько раз для загрузки изображений
            for _ in range(5):
                self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка при прокрутке страницы: {e}")
        
        # Ищем элементы пинов
        logger.info("Ищем изображения на странице")
        pins = []
        try:
            # Сначала пробуем основной селектор - без await, т.к. Selenium методы синхронные
            pin_elements = self._driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='pin']")
            if pin_elements:
                logger.info("Найдены пины через селектор: div[data-test-id='pin']")
            else:
                # Пробуем альтернативный селектор - без await
                pin_elements = self._driver.find_elements(By.CSS_SELECTOR, "div[data-grid-item]")
                logger.info("Найдены пины через альтернативный селектор: div[data-grid-item]")
            
            logger.info(f"Найдено {len(pin_elements)} потенциальных пинов")
            
            # Обрабатываем найденные пины
            for i, pin_element in enumerate(pin_elements):
                if i >= limit:
                    break
                
                try:
                    # Получаем URL изображения из элемента пина
                    img_url = None
                    try:
                        # Пробуем найти изображение внутри пина - без await
                        img_element = pin_element.find_element(By.TAG_NAME, "img")
                        img_url = self._get_best_image_url(img_element)
                    except Exception as e:
                        logger.warning(f"Не удалось извлечь URL изображения из пина #{i+1}: {str(e)}")
                        # Пробуем найти через различные селекторы - без await
                        try:
                            img_element = pin_element.find_element(By.CSS_SELECTOR, "[src]")
                            img_url = img_element.get_attribute("src")
                        except:
                            logger.warning(f"Не удалось найти изображение через альтернативный метод для пина #{i+1}")
                    
                    if not img_url:
                        logger.warning(f"Пропускаем пин #{i+1} из-за отсутствия URL изображения")
                        continue
                    
                    # Создаем уникальный ID на основе URL изображения
                    pin_id = self._get_file_hash(img_url)
                    
                    # Пробуем получить заголовок и описание - без await
                    title = None
                    description = None
                    try:
                        title_element = pin_element.find_element(By.CSS_SELECTOR, "div[title]")
                        title = title_element.get_attribute("title")
                    except:
                        logger.debug(f"Не удалось извлечь заголовок для пина {pin_id}")
                    
                    # Добавляем ссылку на оригинальный пин - без await
                    source_url = None
                    try:
                        a_element = pin_element.find_element(By.TAG_NAME, "a")
                        href = a_element.get_attribute("href")
                        if href and "pinterest.com/pin/" in href:
                            source_url = href
                    except:
                        logger.debug(f"Не удалось извлечь ссылку на пин {pin_id}")
                    
                    saved_path = None
                    if download:
                        try:
                            saved_path = await self._download_image(img_url)
                        except Exception as e:
                            logger.error(f"Ошибка при скачивании изображения: {str(e)}")
                            # Пробуем другой URL (если есть другой размер изображения)
                            try:
                                # Преобразуем URL, чтобы попробовать получить другой размер
                                alt_url = img_url.replace("236x", "564x").replace("474x", "736x")
                                if alt_url != img_url:
                                    logger.info(f"Пробуем альтернативный URL: {alt_url}")
                                    saved_path = await self._download_image(alt_url)
                            except Exception as e2:
                                logger.error(f"Ошибка при скачивании альтернативного изображения: {str(e2)}")
                    
                    # Создаем объект пина
                    pin_info = PinInfo(
                        id=pin_id,
                        title=title,
                        description=description,
                        image_url=img_url,
                        source_url=source_url,
                        saved_path=saved_path,
                        clothing_items=[]
                    )
                    
                    pins.append(pin_info)
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке пина #{i+1}: {str(e)}")
                    continue
            
            # Сохраняем результаты в кеш
            if pins:
                self._cache[cache_key] = pins
                self._save_cache()
            
            logger.info(f"Найдено {len(pins)} пинов по запросу '{query}'")
            
            # Анализируем изображения, если нужно
            if analyze_images:
                # Новый код - анализ изображений и определение одежды
                for pin in pins:
                    # Если у пина нет списка предметов одежды или он пуст, анализируем изображение
                    if not pin.clothing_items:
                        logger.info(f"Анализирую изображение для пина {pin.id}")
                        try:
                            pin.clothing_items = await self.image_analyzer.analyze_image(
                                pin.image_url, gender, query
                            )
                        except Exception as e:
                            logger.error(f"Ошибка при анализе изображения пина {pin.id}: {str(e)}")
                            # При ошибке добавляем базовый набор предметов
                            pin.clothing_items = [
                                {"type": "одежда", "color": "не определено", "description": "не удалось проанализировать", "gender": gender or "унисекс"}
                            ]
                
                # Обновляем кеш после анализа
                self._cache[cache_key] = pins
                self._save_cache()
                
            return pins
            
        except Exception as e:
            logger.error(f"Ошибка при поиске пинов: {str(e)}")
            return []
    
    async def close(self) -> None:
        """Закрывает все открытые соединения."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._driver:
            self._driver.quit()
            self._driver = None
        logger.info("Все соединения закрыты")

class Pinterest:
    """Фасад для работы с Pinterest API."""
    
    def __init__(self, number_of_photo: int = 10, photo_dir: str = "photo", openai_api_key: Optional[str] = None):
        """
        Инициализация фасада Pinterest.
        
        Args:
            number_of_photo: Максимальное количество фотографий для поиска
            photo_dir: Директория для сохранения изображений
            openai_api_key: API ключ OpenAI для анализа изображений
        """
        self.api = PinterestAPI(download_dir=photo_dir, openai_api_key=openai_api_key)
        self.number_of_photo = number_of_photo
    
    async def search_pins(self, query: str, limit: Optional[int] = None, download: bool = True, analyze_images: bool = True, gender: Optional[str] = None) -> List[PinInfo]:
        """
        Поиск пинов по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов (если не указано, используется number_of_photo)
            download: Скачивать ли изображения
            analyze_images: Анализировать ли изображения для определения одежды
            gender: Пол (мужской/женский) для контекста при анализе
            
        Returns:
            Список объектов PinInfo с информацией о найденных пинах
        """
        limit = limit or self.number_of_photo
        return await self.api.search_pins(query, limit, download, analyze_images, gender)
    
    async def close(self):
        """Закрытие сессий и ресурсов."""
        await self.api.close()
