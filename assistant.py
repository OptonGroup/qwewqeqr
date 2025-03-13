#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ChatAssistant - базовый класс с методами и ролевыми промтами экспертов-ассистентов для шопинга с разными ролями (стилист, косметолог, нутрициолог, дизайнер)
и поддержкой разных моделей (нейр. сети, маркетплейсы, поиск, API сторонних сервисов).
"""

import os
import logging
import json
import asyncio
import base64
from typing import Dict, List, Optional, Any, Literal, Counter, AsyncGenerator, Callable, Generator, Union
from pathlib import Path
import openai
from openai import AsyncOpenAI
import requests
import aiohttp
from dotenv import load_dotenv
import sys
from functools import wraps
import time
from datetime import datetime, timedelta
import re
from pydantic import BaseModel, Field
from retry import retry
import copy
import hashlib
import traceback
import random
import zlib
import platform
import string

# Проверка инициализации OpenRouterClient
try:
    from openrouter_image_client import OpenRouterClient
    HAS_OPENROUTER_CLIENT = True
except ImportError:
    HAS_OPENROUTER_CLIENT = False
    logger = logging.getLogger(__name__)
    logger.warning("Не удалось инициализировать openrouter_image_client. Некоторые функции будут недоступны.")

# Проверка инициализации асинхронного API Wildberries
try:
    from wildberries_async import WildberriesAsyncAPI
    WILDBERRIES_ASYNC_AVAILABLE = True
except ImportError:
    WILDBERRIES_ASYNC_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Не удалось инициализировать wildberries_async. Некоторые функции будут недоступны.")

# Инициализация модуля банковских выписок
try:
    from bank_statement_parser import BankStatementParser
    BANK_STATEMENT_PARSER_AVAILABLE = True
except ImportError:
    BANK_STATEMENT_PARSER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Не удалось инициализировать bank_statement_parser. Анализ банковских выписок будет недоступен.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Вывод отладочных сообщений в stderr
        logging.FileHandler("assistant.log", encoding="utf-8")  # Запись логов в файл
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Роли и промты
roles = {
    "стилист": """
    Вы стилист-эксперт по моде и сочетаниям, который помогает улучшить внешний вид и находить идеи для капсульного гардероба.
    Вы специализируетесь на:
    - Анализе стилей и предпочтений
    - Создании капсульных гардеробов
    - Подборе вещей и аксессуаров
    - Подборе рекомендаций для различных ситуаций
    
    При взаимодействии с клиентами вы проявляете следующие:
    - Профессионализм
    - Внимание к деталям
    - Адаптивность к запросам
    - Понимание и учёт особенностей и бюджета
    
    Ваша основная цель - помочь пользователю выбрать и приобрести идеальные предметы одежды, создать образ, соответствующий его потребностям.
    """,
    
    "косметолог": """
    Вы косметолог-эксперт по уходовой и декоративной косметике, который помогает улучшить состав используемой косметики для улучшения здоровья кожи.
    Вы специализируетесь на:
    - Анализе типа кожи/волос
    - Подборе косметических средств
    - Рекомендациях по уходу за кожей
    - Консультировании по составам и брендам
    
    При взаимодействии с клиентами вы проявляете следующие:
    - Профессионализм
    - Внимание к ингредиентам
    - Адаптивность к запросам
    - Понимание и учёт особенностей и типа кожи
    
    Ваша основная цель - помочь выбрать лучшие средства для пользователя и составить индивидуальный уходовый режим для его кожи.
    """,
    
    "нутрициолог": """
    Вы нутрициолог-эксперт по питанию и добавкам, который помогает улучшить рацион для достижения здоровья и самочувствия.
    Вы специализируетесь на:
    - Анализе особенностей питания и здоровья
    - Подборе оптимальных рационов питания
    - Рекомендациях по подбору БАДов
    - Консультировании по вопросам питания и здоровья
    
    При взаимодействии с клиентами вы проявляете следующие:
    - Профессионализм
    - Внимание к потребностям
    - Адаптивность к запросам
    - Понимание и учёт особенностей и целей
    
    Ваша основная цель - помочь выбрать лучший рацион для пользователя и составить продуктовую корзину для достижения его целей здоровья.
    """,
    
    "дизайнер": """
    Вы дизайнер-эксперт по интерьерам и декору, который помогает улучшить пространство и создавать гармоничные интерьеры.
    Вы специализируетесь на:
    - Анализе стилей и предпочтений
    - Создании гармоничных интерьеров
    - Рекомендациях по декору и мебели
    - Консультировании по вопросам дизайна и стиля
    
    При взаимодействии с клиентами вы проявляете следующие:
    - Профессионализм
    - Внимание к деталям
    - Адаптивность к запросам
    - Понимание и учёт особенностей и бюджета
    
    Ваша основная цель - помочь пользователю выбрать и приобрести идеальные предметы для его пространства и создать гармоничный интерьер.
    """
}

# Декоратор для повторного вызывания асинхронных функций
def async_retry(max_retries=3, initial_delay=1, backoff_factor=2, exceptions=(Exception,), jitter=True):
    """
    Улучшенный декоратор для повторения асинхронной функции при исключениях.
    
    Args:
        max_retries: Максимальное количество повторных попыток
        initial_delay: Начальная задержка в секундах
        backoff_factor: Множитель для увеличения задержки после каждой неудачной попытки
        exceptions: Кортеж типов исключений, которые следует обрабатывать
        jitter: Использовать случайное отклонение в задержке для избежания эффекта синхронизации
        
    Returns:
        Декоратор для обернутой функции
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            # Метрики повторных попыток
            retry_metrics = {
                "function": func.__name__,
                "attempts": 0,
                "total_delay": 0,
                "exceptions": [],
                "success": False,
                "start_time": time.time()
            }
            
            # Создаем словарь для логирования, чтобы не логировать одинаковые ошибки
            logged_errors = set()
            
            # Пытаемся выполнить функцию, при ошибке повторяем
            for attempt in range(max_retries + 1):  # +1 для исходной попытки
                try:
                    retry_metrics["attempts"] = attempt + 1
                    
                    if attempt > 0:
                        # Добавляем случайное отклонение (jitter) для предотвращения эффекта синхронизации
                        actual_delay = delay
                        if jitter:
                            actual_delay = delay * (0.5 + random.random())  # 50-150% от базовой задержки
                        
                        logger.info(f"Попытка {attempt+1}/{max_retries+1} для {func.__name__}, ожидание {actual_delay:.2f} секунд...")
                        retry_metrics["total_delay"] += actual_delay
                        await asyncio.sleep(actual_delay)
                        
                    # Вызываем функцию
                    result = await func(*args, **kwargs)
                    
                    # Если успешно, возвращаем результат
                    retry_metrics["success"] = True
                    retry_metrics["end_time"] = time.time()
                    retry_metrics["duration"] = retry_metrics["end_time"] - retry_metrics["start_time"]
                    
                    # Логируем только если были повторные попытки
                    if attempt > 0:
                        logger.info(f"Успешное выполнение {func.__name__} после {attempt+1} попыток")
                        try:
                            # Если функция является методом класса и есть _log_metrics
                            if args and hasattr(args[0], '_log_metrics') and callable(getattr(args[0], '_log_metrics')):
                                args[0]._log_metrics(f"retry_{func.__name__}", retry_metrics)
                        except Exception as e:
                            logger.debug(f"Не удалось записать метрики повторных попыток: {str(e)}")
                    
                    return result
                    
                except exceptions as e:
                    # Сохраняем исключение
                    last_exception = e
                    error_type = type(e).__name__
                    error_message = str(e)
                    
                    # Формируем уникальный ключ ошибки для дедупликации логов
                    error_key = f"{error_type}:{error_message}"
                    
                    # Логируем только уникальные ошибки
                    if error_key not in logged_errors:
                        logged_errors.add(error_key)
                        logger.warning(f"Ошибка в {func.__name__} (попытка {attempt+1}/{max_retries+1}): {error_type}: {error_message}")
                    
                    # Если стоит последняя попытка, просто пропускаем
                    if attempt == max_retries:
                        continue
                    
                    # Добавляем информацию об исключении в метрики
                    retry_metrics["exceptions"].append({
                        "attempt": attempt + 1,
                        "type": error_type,
                        "message": error_message,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Увеличиваем задержку
                    delay *= backoff_factor
            
            # Если все попытки не удались, логируем ошибку и выбрасываем последнее исключение
            retry_metrics["end_time"] = time.time()
            retry_metrics["duration"] = retry_metrics["end_time"] - retry_metrics["start_time"]
            
            try:
                # Если функция является методом класса и есть _log_metrics
                if args and hasattr(args[0], '_log_metrics') and callable(getattr(args[0], '_log_metrics')):
                    args[0]._log_metrics(f"retry_failed_{func.__name__}", retry_metrics)
            except Exception as e:
                logger.debug(f"Не удалось записать метрики неудачных повторных попыток: {str(e)}")
            
            logger.error(f"Все попытки ({max_retries+1}) для {func.__name__} не удались. Последняя ошибка: {last_exception}")
            raise last_exception
            
        return wrapper
    return decorator

class UserPreferences(BaseModel):
    """Модель для хранения предпочтений пользователя"""
    user_id: str
    role: str
    style_preferences: Optional[Dict[str, Any]] = None
    budget: Optional[float] = None
    size: Optional[str] = None
    color_preferences: Optional[List[str]] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Параметры для роли стилист
    season: Optional[str] = None
    garment_types: Optional[List[str]] = None
    occasions: Optional[List[str]] = None
    
    # Параметры для роли косметолог
    skin_type: Optional[str] = None
    skin_concerns: Optional[List[str]] = None
    age_range: Optional[str] = None
    allergies: Optional[List[str]] = None
    preferred_brands: Optional[List[str]] = None
    organic_only: Optional[bool] = False
    
    # Параметры для роли нутрициолог
    dietary_goal: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    activity_level: Optional[str] = None
    meal_preferences: Optional[Dict[str, Any]] = None
    allergies_food: Optional[List[str]] = None
    
    # Параметры для роли дизайнер
    interior_style: Optional[str] = None
    room_types: Optional[List[str]] = None
    home_size: Optional[float] = None
    color_scheme: Optional[List[str]] = None
    existing_furniture: Optional[Dict[str, Any]] = None
    renovation_planned: Optional[bool] = None
    
    def get_role_specific_preferences(self) -> Dict[str, Any]:
        """
        Возвращает словарь с предпочтениями, специфичными для текущей роли пользователя.
        
        Returns:
            Dict[str, Any]: Словарь с предпочтениями для конкретной роли
        """
        base_prefs = {
            "budget": self.budget,
            "color_preferences": self.color_preferences
        }
        
        if self.role == "стилист":
            return {
                **base_prefs,
                "size": self.size,
                "season": self.season,
                "garment_types": self.garment_types,
                "occasions": self.occasions
            }
        elif self.role == "косметолог":
            return {
                **base_prefs,
                "skin_type": self.skin_type,
                "skin_concerns": self.skin_concerns,
                "age_range": self.age_range,
                "allergies": self.allergies,
                "preferred_brands": self.preferred_brands,
                "organic_only": self.organic_only
            }
        elif self.role == "нутрициолог":
            return {
                **base_prefs,
                "dietary_goal": self.dietary_goal,
                "dietary_restrictions": self.dietary_restrictions,
                "weight": self.weight,
                "height": self.height,
                "activity_level": self.activity_level,
                "meal_preferences": self.meal_preferences,
                "allergies_food": self.allergies_food
            }
        elif self.role == "дизайнер":
            return {
                **base_prefs,
                "interior_style": self.interior_style,
                "room_types": self.room_types,
                "home_size": self.home_size,
                "color_scheme": self.color_scheme,
                "existing_furniture": self.existing_furniture,
                "renovation_planned": self.renovation_planned
            }
        else:
            return base_prefs
            
    def dict(self, **kwargs) -> Dict[str, Any]:
        """
        Преобразует модель в словарь для сериализации.
        Обрабатывает специальные типы данных, такие как datetime.
        
        Returns:
            Словарь с атрибутами модели
        """
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):  # Пропускаем приватные атрибуты
                continue
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
                result[key] = value
            else:
                # Для других типов пытаемся сериализовать, если это возможно
                try:
                    if hasattr(value, "dict"):
                        result[key] = value.dict()
                    elif hasattr(value, "__dict__"):
                        result[key] = value.__dict__
                    else:
                        result[key] = str(value)
                except Exception:
                    result[key] = str(value)
        return result

class ChatAssistant:
    """
    Класс для работы с ассистентом-экспертом шопинга.
    
    Предоставляет методы для генерации ответов в различных ролях (стилист, косметолог,
    нутрициолог, дизайнер), а также управления диалоговыми сессиями.
    """
    
    def __init__(
        self,
        model_type: Literal["openai", "openrouter"] = "openrouter",
        model_name: str = "mistralai/mistral-7b-instruct:free",
        openai_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        max_tokens: int = 1000,
        max_retries: int = 3,
        cache_enabled: bool = True,
        cache_ttl: int = 86400,  # 24 часа по умолчанию
        enable_usage_tracking: bool = False,
        bank_statement_cache_dir: str = "bank_statements_cache"
    ):
        """
        Инициализирует экземпляр ChatAssistant.
        
        Args:
            model_type: Тип модели ("openai" или "openrouter")
            model_name: Название модели
            openai_api_key: API ключ для OpenAI (опционально)
            openrouter_api_key: API ключ для OpenRouter (опционально)
            max_tokens: Максимальное количество токенов для генерации
            max_retries: Максимальное количество повторных попыток при ошибках
            cache_enabled: Включено ли кэширование
            cache_ttl: Время жизни кэша в секундах (по умолчанию 24 часа)
            enable_usage_tracking: Включено ли отслеживание использования
            bank_statement_cache_dir: Директория для кэширования данных банковских выписок
        """
        self.model_type = model_type
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.enable_usage_tracking = enable_usage_tracking
        self.http_session = None
        self.bank_statement_cache_dir = bank_statement_cache_dir
        
        # Инициализация парсера банковских выписок, если доступен
        self.bank_statement_parser = None
        if BANK_STATEMENT_PARSER_AVAILABLE:
            self.bank_statement_parser = BankStatementParser(cache_dir=bank_statement_cache_dir)
        
        # Устанавливаем API ключи
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Проверяем наличие нужного ключа в зависимости от типа модели
        if model_type == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API key is required for OpenAI models")
        elif model_type == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OpenRouter API key is required for OpenRouter models")
        
        # Создаем асинхронным клиент OpenAI для соответствующего API
        if model_type == "openai":
            self.client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            # Для OpenRouter используем другой подход с aiohttp
            self.client = None
            
        # Словарь для хранения истории диалогов пользователей
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        
        # Кеш для хранения ответов на повторяющиеся запросы
        self.response_cache: Dict[str, str] = {}
        
        # Создаем HTTP сессию для асинхронных запросов
        self.http_session = None
        
        # Инициализация статистики использования API
        self.api_usage = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "requests_by_model": {},
            "tokens_by_model": {},
            "requests_by_day": {},
            "tokens_by_day": {},
            "errors": {}
        }
        
        # Инициализация клиента для обработки изображений
        self.image_client = None
        if HAS_OPENROUTER_CLIENT and openrouter_api_key:
            try:
                self.image_client = OpenRouterClient(api_key=openrouter_api_key)
                logger.info("OpenRouterClient для обработки изображений успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации OpenRouterClient: {str(e)}")
        
        logger.info(f"Инициализирован ChatAssistant с моделью {model_name} (тип: {model_type})")
    
    async def _ensure_session(self):
        """Создает HTTP сессию, если она еще не создана."""
        if self.http_session is None:
            self.http_session = aiohttp.ClientSession()
            
    @async_retry(max_retries=3, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _call_openrouter_api_async(self, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        """
        Асинхронный вызов OpenRouter API.
        
        Args:
            messages: Список сообщений для API.
            stream: Флаг для потоковой передачи
            
        Returns:
            Возвращает результат от API или объект соединения для потоковой передачи.
        """
        start_time = time.time()
        
        try:
            if self.http_session is None:
                await self._ensure_session()
                
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "HTTP-Referer": "https://github.com/antymon4o", # Вы можете указать URL вашего приложения
                "X-Title": "Shopping Assistant"
            }
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "stream": stream
            }
            
            logger.debug(f"Отправка запроса к OpenRouter API с моделью {self.model_name}")
            
            async with self.http_session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            ) as response:
                if not response.ok:
                    error_text = await response.text()
                    logger.error(f"Ошибка OpenRouter API: {error_text}")
                    response.raise_for_status()
                
                if stream:
                    return response  # Возвращаем объект соединения для потоковой передачи
                else:
                    result = await response.json()
                    
                    if self.enable_usage_tracking and "usage" in result:
                        # Обновляем статистику использования API
                        await self._update_usage_stats(
                            self.model_name, 
                            result["usage"].get("total_tokens", 0)
                        )
                    
                    return result
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenRouter API: {str(e)}")
            if self.enable_usage_tracking:
                self._track_api_error(str(e))
            raise
    
    async def _update_usage_stats(self, model_name: str, tokens: int):
        """
        Обновляет статистику использования API.
        
        Args:
            model_name: Название модели
            tokens: Количество использованных токенов
        """
        if not self.enable_usage_tracking:
            return
            
        try:
            # Здесь можно реализовать сохранение статистики в БД или файл
            logger.debug(f"Использовано {tokens} токенов модели {model_name}")
            
            # Пример сохранения в файл
            usage_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": model_name,
                "tokens": tokens
            }
            
            # Асинхронная запись в файл через отдельный поток
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self._append_to_usage_log(usage_data)
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики использования: {str(e)}")
    
    def _track_api_error(self, error_message: str):
        """
        Отслеживает ошибки API для анализа.
        
        Args:
            error_message: Сообщение об ошибке
        """
        if not self.enable_usage_tracking:
            return
            
        try:
            # Здесь можно реализовать сохранение ошибок в БД или файл
            logger.debug(f"Ошибка API: {error_message}")
            
            # Пример сохранения в файл
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": self.model_name,
                "error": error_message
            }
            
            # Запись в файл
            self._append_to_error_log(error_data)
        except Exception as e:
            logger.error(f"Ошибка при отслеживании ошибок API: {str(e)}")
    
    def _append_to_usage_log(self, usage_data: Dict[str, Any]):
        """
        Добавляет данные об использовании в лог-файл.
        
        Args:
            usage_data: Данные об использовании API
        """
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "api_usage.jsonl"
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(usage_data) + "\n")
        except Exception as e:
            logger.error(f"Ошибка при записи в лог использования: {str(e)}")
    
    def _append_to_error_log(self, error_data: Dict[str, Any]):
        """
        Добавляет данные об ошибках в лог-файл.
        
        Args:
            error_data: Данные об ошибке API
        """
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "api_errors.jsonl"
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_data) + "\n")
        except Exception as e:
            logger.error(f"Ошибка при записи в лог ошибок: {str(e)}")

    async def close(self):
        """Закрывает HTTP сессию."""
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
            logger.debug("HTTP сессия закрыта")
    
    async def _get_cache_key(self, user_id: str, role: str, user_input: str) -> str:
        """
        Формирует ключ для кеширования ответов на основе идентификатора пользователя, роли и входного текста.
        
        Args:
            user_id: Идентификатор пользователя
            role: Роль ассистента
            user_input: Текст пользователя

        Returns:
            str: Ключ кеширования
        """
        # Создаем уникальный ключ для данного запроса
        return f"{user_id}:{role}:{hash(user_input)}"
    
    def _save_to_cache(self, cache_key: str, response: str, ttl: Optional[int] = None) -> None:
        """
        Сохраняет ответ в кэш.
        
        Args:
            cache_key: Ключ для сохранения в кэш
            response: Ответ для сохранения
            ttl: Время жизни кэша в секундах (если None, используется значение по умолчанию)
        """
        if not self.cache_enabled:
            return
            
        try:
            # Используем TTL из параметра или значение по умолчанию
            ttl_value = ttl if ttl is not None else self.cache_ttl
            
            # Определяем, нужно ли сжимать данные (если размер превышает порог)
            compress_data = False
            if len(response) > 8192:  # Сжимаем, если больше 8KB
                compress_data = True
                logger.debug(f"Сжимаем данные для кэша с ключом {cache_key} (размер: {len(response)} байт)")
            
            # Создаем объект с данными и временем истечения
            cache_data = {
                "data": response,
                "expires_at": int(time.time()) + ttl_value,
                "compressed": compress_data,
                "created_at": int(time.time())
            }
            
            # Если нужно сжимать, применяем сжатие
            if compress_data:
                import zlib
                compressed_data = zlib.compress(response.encode('utf-8'))
                cache_data["data"] = base64.b64encode(compressed_data).decode('ascii')
            
            # Сериализуем объект в JSON
            cache_json = json.dumps(cache_data, ensure_ascii=False)
            
            # Определяем путь к файлу кэша
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Хешируем ключ для безопасности пути к файлу
            hashed_key = hashlib.md5(cache_key.encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f"{hashed_key}.json")
            
            # Сохраняем в файл
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(cache_json)
                
            # Записываем в индексный файл для возможности очистки старых кэшей
            index_file = os.path.join(cache_dir, "cache_index.jsonl")
            with open(index_file, "a", encoding="utf-8") as f:
                index_data = {
                    "key": cache_key, 
                    "hashed_key": hashed_key,
                    "expires_at": int(time.time()) + ttl_value,
                    "created_at": int(time.time()),
                    "size": len(response),
                    "compressed": compress_data
                }
                f.write(json.dumps(index_data) + "\n")
            
            logger.debug(f"Данные сохранены в кэш с ключом {cache_key} и TTL {ttl_value} секунд")
            
            # Периодически очищаем устаревшие кэши (с вероятностью 5%)
            if random.random() < 0.05:
                self._cleanup_expired_cache()
                
        except Exception as e:
            logger.warning(f"Ошибка при сохранении в кэш: {str(e)}")
            import traceback
            logger.debug(f"Трассировка стека ошибки при сохранении в кэш: {traceback.format_exc()}")

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Получает ответ из кэша.
        
        Args:
            cache_key: Ключ для поиска в кэше
            
        Returns:
            Кэшированный ответ или None, если кэш не найден или истек
        """
        if not self.cache_enabled:
            return None
            
        try:
            # Определяем путь к файлу кэша
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
            
            # Хешируем ключ для безопасности пути к файлу
            hashed_key = hashlib.md5(cache_key.encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f"{hashed_key}.json")
            
            # Проверяем существование файла
            if not os.path.exists(cache_file):
                logger.debug(f"Кэш с ключом {cache_key} не найден")
                return None
                
            # Читаем данные из файла
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_json = f.read()
                
            # Десериализуем JSON
            cache_data = json.loads(cache_json)
            
            # Проверяем время истечения
            current_time = int(time.time())
            expires_at = cache_data.get("expires_at", 0)
            
            if current_time > expires_at:
                logger.debug(f"Кэш с ключом {cache_key} истек и будет удален")
                # Удаляем устаревший кэш
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.warning(f"Ошибка при удалении устаревшего кэша: {str(e)}")
                return None
            
            # Проверяем, сжаты ли данные
            if cache_data.get("compressed", False):
                try:
                    import zlib
                    # Декодируем из base64 и распаковываем
                    compressed_data = base64.b64decode(cache_data["data"])
                    uncompressed_data = zlib.decompress(compressed_data).decode('utf-8')
                    return uncompressed_data
                except Exception as e:
                    logger.warning(f"Ошибка при распаковке сжатых данных: {str(e)}")
                    # Удаляем поврежденный кэш
                    try:
                        os.remove(cache_file)
                    except:
                        pass
                    return None
                
            # Возвращаем данные
            return cache_data.get("data")
            
        except Exception as e:
            logger.warning(f"Ошибка при получении из кэша: {str(e)}")
            return None
    
    def _cleanup_expired_cache(self) -> None:
        """
        Очищает устаревшие записи кэша.
        """
        if not self.cache_enabled:
            return
            
        try:
            # Определяем путь к директории кэша
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
            if not os.path.exists(cache_dir):
                return
                
            # Текущее время
            current_time = int(time.time())
            removed_count = 0
            total_size = 0
            
            # Сканируем все файлы в директории кэша
            for file_name in os.listdir(cache_dir):
                if not file_name.endswith('.json') or file_name == 'cache_index.jsonl':
                    continue
                    
                file_path = os.path.join(cache_dir, file_name)
                
                try:
                    # Если файл старше 7 дней, удаляем его
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 7 * 24 * 3600:  # 7 дней
                        os.remove(file_path)
                        removed_count += 1
                        continue
                        
                    # Проверяем содержимое файла
                    with open(file_path, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                    
                    # Если кэш истек, удаляем его
                    expires_at = cache_data.get("expires_at", 0)
                    if current_time > expires_at:
                        os.remove(file_path)
                        removed_count += 1
                    else:
                        # Считаем размер валидных кэшей
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        
                except Exception as e:
                    logger.warning(f"Ошибка при очистке кэша для файла {file_name}: {str(e)}")
            
            # Обновляем индексный файл
            self._rebuild_cache_index()
            
            logger.info(f"Очистка кэша завершена: удалено {removed_count} файлов, общий размер оставшихся файлов: {total_size/1024:.2f} KB")
            
        except Exception as e:
            logger.warning(f"Ошибка при очистке кэша: {str(e)}")
    
    def _rebuild_cache_index(self) -> None:
        """
        Перестраивает индекс кэша, удаляя записи о несуществующих или устаревших файлах.
        """
        try:
            # Определяем путь к директории кэша
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
            if not os.path.exists(cache_dir):
                return
                
            # Индексный файл
            index_file = os.path.join(cache_dir, "cache_index.jsonl")
            
            # Если индексного файла нет, создаем новый
            if not os.path.exists(index_file):
                return
                
            # Текущее время
            current_time = int(time.time())
            
            # Читаем текущий индекс
            valid_entries = []
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            hashed_key = entry.get("hashed_key")
                            if not hashed_key:
                                continue
                                
                            # Проверяем существование файла
                            cache_file = os.path.join(cache_dir, f"{hashed_key}.json")
                            if not os.path.exists(cache_file):
                                continue
                                
                            # Проверяем срок истечения
                            expires_at = entry.get("expires_at", 0)
                            if current_time > expires_at:
                                # Удаляем устаревший файл
                                try:
                                    os.remove(cache_file)
                                except:
                                    pass
                                continue
                                
                            # Добавляем валидную запись
                            valid_entries.append(entry)
                            
                        except Exception as e:
                            logger.debug(f"Ошибка при обработке записи индекса: {str(e)}")
            except Exception as e:
                logger.warning(f"Ошибка при чтении индексного файла: {str(e)}")
                # В случае ошибки пересоздаем индекс
                valid_entries = []
            
            # Записываем обновленный индекс
            with open(index_file, "w", encoding="utf-8") as f:
                for entry in valid_entries:
                    f.write(json.dumps(entry) + "\n")
                    
            logger.debug(f"Индекс кэша перестроен, валидных записей: {len(valid_entries)}")
            
        except Exception as e:
            logger.warning(f"Ошибка при перестроении индекса кэша: {str(e)}")

    def _update_conversation_history(self, user_id: str, user_input: str, assistant_response: str) -> None:
        """
        Обновляет историю диалога с пользователем.
        
        Args:
            user_id: Идентификатор пользователя
            user_input: Текст пользователя
            assistant_response: Ответ ассистента
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []
            
        self.conversations[user_id].append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Ограничиваем историю последними 20 сообщениями
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]
            
        logger.debug(f"История диалога с пользователем {user_id} обновлена (сообщений: {len(self.conversations[user_id])})")
    
    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def generate_response_async(self, user_id: str, user_input: str, role: str = "стилист", **kwargs) -> str:
        """
        Асинхронно генерирует ответ на запрос пользователя с учетом роли.
        
        Args:
            user_id: Идентификатор пользователя
            user_input: Текст пользователя
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            **kwargs: Дополнительные параметры для запроса (temperature, top_p и т.д.)

        Returns:
            str: Ответ ассистента
        """
        logger.debug(f"Генерация ответа для пользователя {user_id} в роли {role}")
        
        # Проверяем корректность роли
        if role not in roles:
            available_roles = ", ".join(roles.keys())
            error_msg = f"Недопустимая роль: {role}. Доступные роли: {available_roles}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Проверяем кеш, если он включен
        cache_key = await self._get_cache_key(user_id, role, user_input)
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            logger.info(f"Ответ взят из кеша для пользователя {user_id}")
            return cached_response
        
        # Инициализируем сессию, если необходимо
        await self._ensure_session()
        
        # Обновляем статистику использования API
        day_key = datetime.utcnow().strftime("%Y-%m-%d")
        self.api_usage["total_requests"] += 1
        self.api_usage["requests_by_day"][day_key] = self.api_usage["requests_by_day"].get(day_key, 0) + 1
        
        # Получаем системный промпт для выбранной роли
        system_prompt = roles[role]
        
        # История диалога
        history = self.conversations.get(user_id, [])
        
        # Формируем сообщения для запроса к API
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавляем предыдущие сообщения из истории диалога (максимум 5 последних)
        for message in history[-5:]:
            messages.append({"role": "user", "content": message["user"]})
            messages.append({"role": "assistant", "content": message["assistant"]})
        
        # Добавляем текущий запрос пользователя
        messages.append({"role": "user", "content": user_input})
        
        # Параметры запроса
        params = {
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9)
        }
        
        try:
            # В зависимости от типа модели используем различные API
            if self.model_type == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **params
                )
                assistant_response = response.choices[0].message.content
                
                # Обновляем статистику использования токенов
                if hasattr(response, "usage") and response.usage:
                    self.api_usage["total_tokens"] += response.usage.total_tokens
                    self.api_usage["tokens_by_day"][day_key] = self.api_usage["tokens_by_day"].get(day_key, 0) + response.usage.total_tokens
                    self.api_usage["tokens_by_model"][self.model_name] = self.api_usage["tokens_by_model"].get(self.model_name, 0) + response.usage.total_tokens
            else:
                # Для OpenRouter используем прямой запрос к API через aiohttp
                async with self.http_session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        **params
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        assistant_response = data["choices"][0]["message"]["content"]
                        
                        # Обновляем статистику использования токенов
                        if "usage" in data:
                            self.api_usage["total_tokens"] += data["usage"]["total_tokens"]
                            self.api_usage["tokens_by_day"][day_key] = self.api_usage["tokens_by_day"].get(day_key, 0) + data["usage"]["total_tokens"]
                            self.api_usage["tokens_by_model"][self.model_name] = self.api_usage["tokens_by_model"].get(self.model_name, 0) + data["usage"]["total_tokens"]
                    else:
                        error_text = await resp.text()
                        raise Exception(f"Ошибка при запросе к OpenRouter API: {resp.status} - {error_text}")
            
            # Обновляем счетчик успешных запросов
            self.api_usage["successful_requests"] += 1
            
            # Обновляем историю диалога
            self._update_conversation_history(user_id, user_input, assistant_response)
            
            # Сохраняем ответ в кеш
            self._save_to_cache(cache_key, assistant_response)
            
            logger.info(f"Получен ответ от модели {self.model_name} для пользователя {user_id}")
            return assistant_response
            
        except Exception as e:
            # Обновляем счетчики ошибок
            self.api_usage["failed_requests"] += 1
            error_type = type(e).__name__
            self.api_usage["errors"][error_type] = self.api_usage["errors"].get(error_type, 0) + 1
            
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            raise
    
    def generate_response(self, user_id: str, user_input: str, role: str = "стилист", **kwargs) -> str:
        """
        Синхронная версия метода generate_response_async.
        
        Args:
            user_id: Идентификатор пользователя
            user_input: Текст пользователя
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            **kwargs: Дополнительные параметры для запроса (temperature, top_p и т.д.)

        Returns:
            str: Ответ ассистента
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если событийный цикл уже работает, создаем новый
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.generate_response_async(user_id, user_input, role, **kwargs)
            )
            new_loop.close()
        else:
            # Используем текущий событийный цикл
            response = loop.run_until_complete(
                self.generate_response_async(user_id, user_input, role, **kwargs)
            )
        return response

    def _encode_image(self, image_path: Union[str, Path]) -> str:
        """
        Кодирует изображение в base64.
        
        Args:
            image_path: Путь к изображению

        Returns:
            str: Изображение, закодированное в base64
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка при кодировании изображения {image_path}: {str(e)}")
            raise
    
    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def analyze_image_async(self, image_path: Union[str, Path], prompt: str = "Опиши, что изображено на этой фотографии") -> str:
        """
        Анализирует изображение с помощью модели компьютерного зрения.
        
        Args:
            image_path: Путь к изображению
            prompt: Запрос для анализа изображения

        Returns:
            str: Описание изображения
        """
        logger.debug(f"Анализ изображения {image_path}")
        
        # Проверяем наличие клиента для работы с изображениями
        if not HAS_OPENROUTER_CLIENT or not self.image_client:
            error_msg = "Для анализа изображений требуется инициализировать OpenRouterClient"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Кодируем изображение в base64
            image_base64 = self._encode_image(image_path)
            
            # Анализируем изображение с помощью OpenRouterClient
            response = await self.image_client.analyze_image(image_base64, prompt)
            
            logger.info(f"Изображение {image_path} успешно проанализировано")
            return response
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения {image_path}: {str(e)}")
            raise
    
    def analyze_image(self, image_path: Union[str, Path], prompt: str = "Опиши, что изображено на этой фотографии") -> str:
        """
        Синхронная версия метода analyze_image_async.
        
        Args:
            image_path: Путь к изображению
            prompt: Запрос для анализа изображения

        Returns:
            str: Описание изображения
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.analyze_image_async(image_path, prompt)
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.analyze_image_async(image_path, prompt)
            )
        return response
    
    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def generate_response_with_image_async(
        self, 
        user_id: str, 
        user_input: str, 
        image_path: Union[str, Path], 
        role: str = "стилист", 
        **kwargs
    ) -> str:
        """
        Генерирует ответ на основе текста и изображения в выбранной роли.
        
        Args:
            user_id: Идентификатор пользователя
            user_input: Текст пользователя
            image_path: Путь к изображению
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            **kwargs: Дополнительные параметры для запроса

        Returns:
            str: Ответ ассистента
        """
        logger.debug(f"Генерация ответа на основе изображения для пользователя {user_id} в роли {role}")
        
        # Проверяем корректность роли
        if role not in roles:
            available_roles = ", ".join(roles.keys())
            error_msg = f"Недопустимая роль: {role}. Доступные роли: {available_roles}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Проверяем наличие клиента для работы с изображениями
        if self.model_type == "openai":
            if not self.client:
                error_msg = "Не инициализирован клиент OpenAI"
                logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            if not HAS_OPENROUTER_CLIENT or not self.image_client:
                error_msg = "Для анализа изображений требуется инициализировать OpenRouterClient"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Инициализируем сессию, если необходимо
        await self._ensure_session()
        
        # Обновляем статистику использования API
        day_key = datetime.utcnow().strftime("%Y-%m-%d")
        self.api_usage["total_requests"] += 1
        self.api_usage["requests_by_day"][day_key] = self.api_usage["requests_by_day"].get(day_key, 0) + 1
        
        # Получаем системный промпт для выбранной роли
        system_prompt = roles[role]
        
        try:
            # Кодируем изображение в base64
            image_base64 = self._encode_image(image_path)
            
            # В зависимости от типа модели используем различные API
            if self.model_type == "openai":
                # Формируем сообщения для запроса к API
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_input},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
                
                # Параметры запроса
                params = {
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9)
                }
                
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **params
                )
                
                assistant_response = response.choices[0].message.content
                
                # Обновляем статистику использования токенов
                if hasattr(response, "usage") and response.usage:
                    self.api_usage["total_tokens"] += response.usage.total_tokens
                    self.api_usage["tokens_by_day"][day_key] = self.api_usage["tokens_by_day"].get(day_key, 0) + response.usage.total_tokens
                    self.api_usage["tokens_by_model"][self.model_name] = self.api_usage["tokens_by_model"].get(self.model_name, 0) + response.usage.total_tokens
            else:
                # Для OpenRouter используем OpenRouterClient
                assistant_response = await self.image_client.generate_response(
                    model=self.model_name, 
                    image_base64=image_base64, 
                    prompt=f"{system_prompt}\n\n{user_input}",
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.9)
                )
            
            # Обновляем счетчик успешных запросов
            self.api_usage["successful_requests"] += 1
            
            # Обновляем историю диалога
            self._update_conversation_history(
                user_id, 
                f"{user_input} [С изображением]", 
                assistant_response
            )
            
            logger.info(f"Получен ответ на основе изображения от модели {self.model_name} для пользователя {user_id}")
            return assistant_response
            
        except Exception as e:
            # Обновляем счетчики ошибок
            self.api_usage["failed_requests"] += 1
            error_type = type(e).__name__
            self.api_usage["errors"][error_type] = self.api_usage["errors"].get(error_type, 0) + 1
            
            logger.error(f"Ошибка при генерации ответа на основе изображения: {str(e)}")
            raise
    
    def generate_response_with_image(
        self, 
        user_id: str, 
        user_input: str, 
        image_path: Union[str, Path], 
        role: str = "стилист", 
        **kwargs
    ) -> str:
        """
        Синхронная версия метода generate_response_with_image_async.
        
        Args:
            user_id: Идентификатор пользователя
            user_input: Текст пользователя
            image_path: Путь к изображению
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            **kwargs: Дополнительные параметры для запроса

        Returns:
            str: Ответ ассистента
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.generate_response_with_image_async(user_id, user_input, image_path, role, **kwargs)
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.generate_response_with_image_async(user_id, user_input, image_path, role, **kwargs)
            )
        return response
    
    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def find_similar_products_wildberries_async(
        self,
        query: Optional[str] = None,
        image_path: Optional[Union[str, Path]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        sort: str = "popular",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Находит похожие товары на Wildberries по текстовому запросу или изображению.
        
        Args:
            query: Текстовый запрос для поиска
            image_path: Путь к изображению для поиска похожих товаров
            min_price: Минимальная цена (фильтрует по основной цене)
            max_price: Максимальная цена (фильтрует по скидочной цене)
            limit: Максимальное количество товаров для возврата
            sort: Способ сортировки товаров (popular, priceup, pricedown, newly, rate)
            **kwargs: Дополнительные параметры для поиска

        Returns:
            List[Dict[str, Any]]: Список найденных товаров
        """
        logger.debug(f"Поиск товаров на Wildberries: query={query}, image_path={image_path}, min_price={min_price}, max_price={max_price}")
        
        # Проверяем наличие интеграции с Wildberries API
        if not WILDBERRIES_ASYNC_AVAILABLE:
            error_msg = "Интеграция с асинхронным API Wildberries недоступна"
            logger.error(error_msg)
            raise ImportError(error_msg)
        
        # Проверяем наличие запроса или изображения
        if not query and not image_path:
            error_msg = "Для поиска товаров необходимо указать текстовый запрос (query) или путь к изображению (image_path)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        wildberries_api = WildberriesAsyncAPI()
        
        # Если предоставлено изображение, но нет запроса, анализируем изображение для получения запроса
        if image_path and not query:
            logger.info(f"Анализ изображения {image_path} для поиска похожих товаров")
            try:
                image_analysis = await self.analyze_image_async(
                    image_path,
                    prompt="Опиши это изображение с точки зрения поиска похожих товаров. Укажи тип одежды/предмета, цвет, материал, стиль."
                )
                
                # Генерируем поисковый запрос на основе анализа изображения
                search_query = await self.generate_response_async(
                    "system",
                    f"На основе этого описания изображения создай короткий поисковый запрос (3-5 слов) для поиска похожих товаров на Wildberries: {image_analysis}",
                    "стилист"
                )
                
                query = search_query.strip()
                logger.info(f"Сгенерирован поисковый запрос на основе изображения: {query}")
            except Exception as e:
                logger.error(f"Ошибка при анализе изображения и генерации поискового запроса: {str(e)}")
                # Если не удалось проанализировать изображение, используем общий запрос
                query = "одежда"
        
        try:
            # Выполняем поиск товаров
            products = await wildberries_api.search_products(
                query=query,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                sort=sort,
                **kwargs
            )
            
            # Если не найдены товары, пробуем более общий запрос
            if not products and image_path:
                logger.warning(f"Не найдены товары по запросу '{query}'. Попытка с более общим запросом.")
                
                # Извлечем ключевое слово из запроса
                general_query = query.split()[0] if " " in query else query
                
                products = await wildberries_api.search_products(
                    query=general_query,
                    limit=limit,
                    min_price=min_price,
                    max_price=max_price,
                    sort=sort,
                    **kwargs
                )
            
            logger.info(f"Найдено {len(products)} товаров по запросу '{query}'")
            return products
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров на Wildberries: {str(e)}")
            raise
    
    def find_similar_products_wildberries(
        self,
        query: Optional[str] = None,
        image_path: Optional[Union[str, Path]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        sort: str = "popular",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Синхронная версия метода find_similar_products_wildberries_async.
        
        Args:
            query: Текстовый запрос для поиска
            image_path: Путь к изображению для поиска похожих товаров
            min_price: Минимальная цена (фильтрует по основной цене)
            max_price: Максимальная цена (фильтрует по скидочной цене)
            limit: Максимальное количество товаров для возврата
            sort: Способ сортировки товаров (popular, priceup, pricedown, newly, rate)
            **kwargs: Дополнительные параметры для поиска

        Returns:
            List[Dict[str, Any]]: Список найденных товаров
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.find_similar_products_wildberries_async(
                    query=query,
                    image_path=image_path,
                    min_price=min_price,
                    max_price=max_price,
                    limit=limit,
                    sort=sort,
                    **kwargs
                )
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.find_similar_products_wildberries_async(
                    query=query,
                    image_path=image_path,
                    min_price=min_price,
                    max_price=max_price,
                    limit=limit,
                    sort=sort,
                    **kwargs
                )
            )
        return response

    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def calculate_nutrition_async(
        self,
        products: List[Dict[str, Any]],
        quantities: List[float],
        user_preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        """
        Рассчитывает пищевую ценность продуктов с учетом их количества.
        
        Args:
            products: Список продуктов с их пищевой ценностью
            quantities: Список количеств продуктов в граммах
            user_preferences: Предпочтения пользователя (опционально)

        Returns:
            Dict[str, Any]: Словарь с рассчитанной пищевой ценностью
        """
        logger.debug(f"Расчет пищевой ценности для {len(products)} продуктов")
        
        if len(products) != len(quantities):
            error_msg = "Количество продуктов не соответствует количеству значений их масс"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            total_nutrition = {
                "calories": 0.0,
                "proteins": 0.0,
                "fats": 0.0,
                "carbohydrates": 0.0,
                "fiber": 0.0,
                "vitamins": {},
                "minerals": {},
                "allergens": set()
            }
            
            # Рассчитываем общую пищевую ценность
            for product, quantity in zip(products, quantities):
                # Переводим количество в коэффициент (из грамм в доли от 100г)
                factor = quantity / 100.0
                
                # Основные нутриенты
                total_nutrition["calories"] += product.get("calories", 0) * factor
                total_nutrition["proteins"] += product.get("proteins", 0) * factor
                total_nutrition["fats"] += product.get("fats", 0) * factor
                total_nutrition["carbohydrates"] += product.get("carbohydrates", 0) * factor
                total_nutrition["fiber"] += product.get("fiber", 0) * factor
                
                # Витамины и минералы
                for vitamin, amount in product.get("vitamins", {}).items():
                    if vitamin not in total_nutrition["vitamins"]:
                        total_nutrition["vitamins"][vitamin] = 0
                    total_nutrition["vitamins"][vitamin] += amount * factor
                
                for mineral, amount in product.get("minerals", {}).items():
                    if mineral not in total_nutrition["minerals"]:
                        total_nutrition["minerals"][mineral] = 0
                    total_nutrition["minerals"][mineral] += amount * factor
                
                # Аллергены
                if "allergens" in product:
                    total_nutrition["allergens"].update(product["allergens"])
            
            # Проверяем аллергены пользователя
            if user_preferences and user_preferences.allergies_food:
                allergen_warnings = []
                for allergen in total_nutrition["allergens"]:
                    if allergen in user_preferences.allergies_food:
                        allergen_warnings.append(f"Внимание: продукты содержат аллерген '{allergen}'")
                if allergen_warnings:
                    total_nutrition["warnings"] = allergen_warnings
            
            # Преобразуем set в list для сериализации
            total_nutrition["allergens"] = list(total_nutrition["allergens"])
            
            # Округляем значения для удобства
            for key in ["calories", "proteins", "fats", "carbohydrates", "fiber"]:
                total_nutrition[key] = round(total_nutrition[key], 2)
            
            for vitamin_dict in [total_nutrition["vitamins"], total_nutrition["minerals"]]:
                for key in vitamin_dict:
                    vitamin_dict[key] = round(vitamin_dict[key], 2)
            
            logger.info("Расчет пищевой ценности успешно выполнен")
            return total_nutrition
            
        except Exception as e:
            logger.error(f"Ошибка при расчете пищевой ценности: {str(e)}")
            raise

    def calculate_nutrition(
        self,
        products: List[Dict[str, Any]],
        quantities: List[float],
        user_preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        """
        Синхронная версия метода calculate_nutrition_async.
        
        Args:
            products: Список продуктов с их пищевой ценностью
            quantities: Список количеств продуктов в граммах
            user_preferences: Предпочтения пользователя (опционально)

        Returns:
            Dict[str, Any]: Словарь с рассчитанной пищевой ценностью
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.calculate_nutrition_async(products, quantities, user_preferences)
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.calculate_nutrition_async(products, quantities, user_preferences)
            )
        return response

    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def create_meal_plan_async(
        self,
        user_preferences: UserPreferences,
        days: int = 7,
        meals_per_day: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создает план питания на основе предпочтений пользователя.
        
        Args:
            user_preferences: Предпочтения пользователя
            days: Количество дней для планирования
            meals_per_day: Количество приемов пищи в день
            **kwargs: Дополнительные параметры для настройки плана

        Returns:
            Dict[str, Any]: План питания с разбивкой по дням и приемам пищи
        """
        logger.debug(f"Создание плана питания на {days} дней для пользователя {user_preferences.user_id}")
        
        if not user_preferences.dietary_goal:
            error_msg = "Не указана цель диеты в предпочтениях пользователя"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            # Рассчитываем базовые потребности
            height_m = user_preferences.height / 100 if user_preferences.height else 1.7
            weight_kg = user_preferences.weight if user_preferences.weight else 70
            
            # Базовый обмен веществ (формула Миффлина-Сан Жеора)
            if user_preferences.age_range:
                age = int(user_preferences.age_range.split("-")[0])  # Берем нижнюю границу возраста
            else:
                age = 30  # Значение по умолчанию
                
            # Коэффициенты активности
            activity_factors = {
                "низкая": 1.2,
                "умеренная": 1.375,
                "средняя": 1.55,
                "высокая": 1.725,
                "очень высокая": 1.9
            }
            
            activity_factor = activity_factors.get(
                user_preferences.activity_level.lower() if user_preferences.activity_level else "умеренная",
                1.375
            )
            
            # Расчет суточной потребности в калориях
            bmr = (10 * weight_kg) + (6.25 * height_m * 100) - (5 * age)
            daily_calories = bmr * activity_factor
            
            # Корректировка калорий в зависимости от цели
            if "похудение" in user_preferences.dietary_goal.lower():
                daily_calories *= 0.85  # Дефицит 15%
            elif "набор" in user_preferences.dietary_goal.lower():
                daily_calories *= 1.15  # Профицит 15%
            
            # Распределение БЖУ
            if "набор" in user_preferences.dietary_goal.lower():
                protein_ratio = 0.3  # 30% белков
                fat_ratio = 0.3      # 30% жиров
                carb_ratio = 0.4     # 40% углеводов
            elif "похудение" in user_preferences.dietary_goal.lower():
                protein_ratio = 0.35  # 35% белков
                fat_ratio = 0.35     # 35% жиров
                carb_ratio = 0.3     # 30% углеводов
            else:
                protein_ratio = 0.3   # 30% белков
                fat_ratio = 0.3      # 30% жиров
                carb_ratio = 0.4     # 40% углеводов
            
            # Создаем план питания
            meal_plan = {
                "summary": {
                    "daily_calories": round(daily_calories, 0),
                    "daily_proteins": round((daily_calories * protein_ratio) / 4, 1),  # 4 ккал/г белка
                    "daily_fats": round((daily_calories * fat_ratio) / 9, 1),         # 9 ккал/г жира
                    "daily_carbs": round((daily_calories * carb_ratio) / 4, 1),       # 4 ккал/г углеводов
                },
                "restrictions": user_preferences.dietary_restrictions or [],
                "allergies": user_preferences.allergies_food or [],
                "days": {}
            }
            
            # Распределение калорий по приемам пищи
            meal_ratios = {
                3: {"завтрак": 0.3, "обед": 0.4, "ужин": 0.3},
                4: {"завтрак": 0.25, "второй завтрак": 0.15, "обед": 0.35, "ужин": 0.25},
                5: {"завтрак": 0.25, "второй завтрак": 0.15, "обед": 0.3, "полдник": 0.1, "ужин": 0.2}
            }
            
            current_meal_ratios = meal_ratios.get(meals_per_day, meal_ratios[3])
            
            # Генерируем план по дням
            for day in range(1, days + 1):
                meal_plan["days"][f"день_{day}"] = {
                    "приемы_пищи": {},
                    "итого": {
                        "калории": 0,
                        "белки": 0,
                        "жиры": 0,
                        "углеводы": 0
                    }
                }
                
                # Распределяем нутриенты по приемам пищи
                for meal_name, ratio in current_meal_ratios.items():
                    meal_calories = daily_calories * ratio
                    meal_plan["days"][f"день_{day}"]["приемы_пищи"][meal_name] = {
                        "калории": round(meal_calories, 0),
                        "белки": round((meal_calories * protein_ratio) / 4, 1),
                        "жиры": round((meal_calories * fat_ratio) / 9, 1),
                        "углеводы": round((meal_calories * carb_ratio) / 4, 1)
                    }
                    
                    # Обновляем итоги дня
                    meal_plan["days"][f"день_{day}"]["итого"]["калории"] += round(meal_calories, 0)
                    meal_plan["days"][f"день_{day}"]["итого"]["белки"] += round((meal_calories * protein_ratio) / 4, 1)
                    meal_plan["days"][f"день_{day}"]["итого"]["жиры"] += round((meal_calories * fat_ratio) / 9, 1)
                    meal_plan["days"][f"день_{day}"]["итого"]["углеводы"] += round((meal_calories * carb_ratio) / 4, 1)
            
            logger.info(f"План питания на {days} дней успешно создан")
            return meal_plan
            
        except Exception as e:
            logger.error(f"Ошибка при создании плана питания: {str(e)}")
            raise

    def create_meal_plan(
        self,
        user_preferences: UserPreferences,
        days: int = 7,
        meals_per_day: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Синхронная версия метода create_meal_plan_async.
        
        Args:
            user_preferences: Предпочтения пользователя
            days: Количество дней для планирования
            meals_per_day: Количество приемов пищи в день
            **kwargs: Дополнительные параметры для настройки плана

        Returns:
            Dict[str, Any]: План питания с разбивкой по дням и приемам пищи
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.create_meal_plan_async(user_preferences, days, meals_per_day, **kwargs)
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.create_meal_plan_async(user_preferences, days, meals_per_day, **kwargs)
            )
        return response

    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def analyze_interior_async(
        self,
        image_path: Union[str, Path],
        room_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Анализирует интерьер на изображении и определяет его характеристики.
        
        Args:
            image_path: Путь к изображению интерьера
            room_type: Тип комнаты (опционально)
            **kwargs: Дополнительные параметры для анализа

        Returns:
            Dict[str, Any]: Результаты анализа интерьера
        """
        logger.debug(f"Анализ интерьера из изображения {image_path}")
        
        try:
            # Анализируем изображение с помощью модели компьютерного зрения
            prompt = f"""
            Проанализируй этот интерьер и определи:
            1. Стиль интерьера
            2. Основные цвета и их сочетания
            3. Ключевые предметы мебели и декора
            4. Особенности планировки и зонирования
            5. Освещение и его характеристики
            {"6. Соответствие типу комнаты: " + room_type if room_type else ""}
            """
            
            analysis = await self.analyze_image_async(image_path, prompt)
            
            # Генерируем структурированный ответ на основе анализа
            response = await self.generate_response_async(
                "system",
                f"Преобразуй этот анализ интерьера в структурированный JSON с полями: style, colors, furniture, layout, lighting, recommendations:\n\n{analysis}",
                "дизайнер"
            )
            
            # Преобразуем ответ в словарь
            try:
                structured_analysis = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("Не удалось преобразовать ответ в JSON, возвращаем текстовый анализ")
                structured_analysis = {
                    "raw_analysis": analysis,
                    "error": "Не удалось структурировать анализ"
                }
            
            logger.info(f"Анализ интерьера успешно выполнен")
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Ошибка при анализе интерьера: {str(e)}")
            raise

    def analyze_interior(
        self,
        image_path: Union[str, Path],
        room_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Синхронная версия метода analyze_interior_async.
        
        Args:
            image_path: Путь к изображению интерьера
            room_type: Тип комнаты (опционально)
            **kwargs: Дополнительные параметры для анализа

        Returns:
            Dict[str, Any]: Результаты анализа интерьера
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.analyze_interior_async(image_path, room_type, **kwargs)
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.analyze_interior_async(image_path, room_type, **kwargs)
            )
        return response

    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def suggest_interior_items_async(
        self,
        user_preferences: UserPreferences,
        room_type: str,
        existing_items: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Предлагает предметы интерьера на основе предпочтений пользователя и типа комнаты.
        
        Args:
            user_preferences: Предпочтения пользователя
            room_type: Тип комнаты
            existing_items: Список существующих предметов (опционально)
            **kwargs: Дополнительные параметры для подбора

        Returns:
            Dict[str, Any]: Рекомендации по предметам интерьера
        """
        logger.debug(f"Подбор предметов интерьера для комнаты типа {room_type}")
        
        if not user_preferences.interior_style:
            error_msg = "Не указан стиль интерьера в предпочтениях пользователя"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            # Формируем запрос для генерации рекомендаций
            prompt = f"""
            Предложи предметы интерьера для {room_type} в стиле {user_preferences.interior_style}.
            
            Бюджет: {user_preferences.budget if user_preferences.budget else 'не указан'}
            Цветовая схема: {', '.join(user_preferences.color_scheme) if user_preferences.color_scheme else 'не указана'}
            
            {f'Уже имеющиеся предметы: {", ".join(existing_items)}' if existing_items else ''}
            
            Предложи:
            1. Основную мебель
            2. Освещение
            3. Текстиль
            4. Декор
            5. Хранение
            """
            
            # Генерируем рекомендации
            recommendations = await self.generate_response_async(
                "system",
                prompt,
                "дизайнер"
            )
            
            # Ищем подходящие товары на маркетплейсе
            suggested_items = {
                "мебель": [],
                "освещение": [],
                "текстиль": [],
                "декор": [],
                "хранение": []
            }
            
            # Категории поиска для разных типов предметов
            search_categories = {
                "мебель": ["диван", "кровать", "стол", "стул", "шкаф"],
                "освещение": ["люстра", "светильник", "бра", "торшер"],
                "текстиль": ["шторы", "ковер", "подушки", "плед"],
                "декор": ["картина", "ваза", "зеркало", "статуэтка"],
                "хранение": ["комод", "тумба", "стеллаж", "органайзер"]
            }
            
            # Для каждой категории ищем товары
            for category, search_terms in search_categories.items():
                for term in search_terms:
                    query = f"{term} {user_preferences.interior_style}"
                    try:
                        items = await self.find_similar_products_wildberries_async(
                            query=query,
                            min_price=user_preferences.budget * 0.1 if user_preferences.budget else None,  # Минимум 10% от бюджета
                            max_price=user_preferences.budget * 0.4 if user_preferences.budget else None,  # Максимум 40% от бюджета
                            limit=3
                        )
                        suggested_items[category].extend(items)
                    except Exception as e:
                        logger.warning(f"Не удалось найти товары для запроса '{query}': {str(e)}")
            
            # Формируем итоговые рекомендации
            result = {
                "анализ": recommendations,
                "рекомендуемые_товары": suggested_items,
                "общие_рекомендации": {
                    "стиль": user_preferences.interior_style,
                    "цветовая_схема": user_preferences.color_scheme,
                    "тип_комнаты": room_type
                }
            }
            
            if user_preferences.budget:
                result["бюджет"] = {
                    "общий": user_preferences.budget,
                    "рекомендации_по_распределению": {
                        "мебель": "40-50% бюджета",
                        "освещение": "15-20% бюджета",
                        "текстиль": "10-15% бюджета",
                        "декор": "10-15% бюджета",
                        "хранение": "10-15% бюджета"
                    }
                }
            
            logger.info(f"Рекомендации по предметам интерьера успешно сформированы")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при подборе предметов интерьера: {str(e)}")
            raise

    def suggest_interior_items(
        self,
        user_preferences: UserPreferences,
        room_type: str,
        existing_items: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Синхронная версия метода suggest_interior_items_async.
        
        Args:
            user_preferences: Предпочтения пользователя
            room_type: Тип комнаты
            existing_items: Список существующих предметов (опционально)
            **kwargs: Дополнительные параметры для подбора

        Returns:
            Dict[str, Any]: Рекомендации по предметам интерьера
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            response = new_loop.run_until_complete(
                self.suggest_interior_items_async(user_preferences, room_type, existing_items, **kwargs)
            )
            new_loop.close()
        else:
            response = loop.run_until_complete(
                self.suggest_interior_items_async(user_preferences, room_type, existing_items, **kwargs)
            )
        return response

    @async_retry(max_retries=3, initial_delay=1, backoff_factor=2)
    async def determine_user_needs_async(
        self,
        user_id: str,
        role: str,
        user_input: str,
        previous_preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        """
        Асинхронно анализирует ввод пользователя и определяет его потребности на основе роли.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            user_input: Входящее сообщение пользователя
            previous_preferences: Предыдущие предпочтения пользователя (опционально)
            
        Returns:
            Словарь с результатами анализа:
            - success: Успешность операции
            - identified_needs: Определенные потребности
            - clarifying_questions: Уточняющие вопросы
            - preferences_updated: Были ли обновлены предпочтения
            - preferences: Обновленные предпочтения
            
        Example:
            >>> assistant = ChatAssistant()
            >>> result = await assistant.determine_user_needs_async(
            ...     user_id="user123",
            ...     role="нутрициолог",
            ...     user_input="Я хочу составить план питания для похудения. У меня аллергия на орехи.")
            >>> print(result["identified_needs"]["dietary_goal"])
            'похудение'
            >>> print(result["identified_needs"]["allergies_food"])
            ['орехи']
        """
        # Создаем словарь для отслеживания метрик и ошибок
        metrics = {
            "start_time": time.time(),
            "cache_hit": False,
            "json_parse_method": None,
            "error_type": None,
            "error_details": None,
            "recovery_attempts": 0,
            "success": False
        }
        
        try:
            # Проверяем наличие в кэше
            if self.cache_enabled:
                try:
                    # Создаем более детерминистичный ключ кэша
                    # Улучшенная санитизация входных данных для кэша
                    sanitized_input = self._sanitize_cache_key_input(user_input)
                    role_hash = hashlib.md5(role.encode('utf-8')).hexdigest()[:8]
                    user_hash = hashlib.md5(user_id.encode('utf-8')).hexdigest()[:8]
                    input_hash = hashlib.md5(sanitized_input.encode('utf-8')).hexdigest()[:16]
                    
                    cache_key = f"determine_needs_{user_hash}_{role_hash}_{input_hash}"
                    logger.debug(f"Сгенерирован ключ кэша: {cache_key}")
                    
                    cached_result = self._get_from_cache(cache_key)
                    
                    if cached_result:
                        logger.info(f"Найден кэшированный результат для определения потребностей пользователя {user_id}")
                        metrics["cache_hit"] = True
                        
                        try:
                            # Десериализуем кэшированный результат
                            cached_data = json.loads(cached_result)
                            
                            # Проверяем валидность кэшированных данных
                            if not isinstance(cached_data, dict):
                                logger.warning(f"Кэшированный результат имеет неверный формат. Ожидался словарь, получено: {type(cached_data)}")
                                metrics["error_type"] = "cache_format_error"
                                metrics["error_details"] = f"Неверный формат кэшированных данных: {type(cached_data)}"
                                raise ValueError("Неверный формат кэшированных данных")
                            
                            # Проверяем наличие необходимых ключей
                            required_keys = ["success", "identified_needs", "clarifying_questions"]
                            if not all(key in cached_data for key in required_keys):
                                missing_keys = [key for key in required_keys if key not in cached_data]
                                logger.warning(f"В кэшированном результате отсутствуют необходимые ключи: {missing_keys}")
                                metrics["error_type"] = "cache_missing_keys"
                                metrics["error_details"] = f"В кэшированных данных отсутствуют необходимые ключи: {missing_keys}"
                                raise ValueError(f"В кэшированных данных отсутствуют необходимые ключи: {missing_keys}")
                            
                            # Если есть previous_preferences, обновляем их значениями из кэша
                            if previous_preferences:
                                cached_prefs = cached_data.get('preferences', {})
                                
                                # Проверяем, что cached_prefs - словарь
                                if not isinstance(cached_prefs, dict):
                                    logger.warning(f"Предпочтения в кэше имеют неверный формат. Ожидался словарь, получено: {type(cached_prefs)}")
                                    # Продолжаем выполнение с пустым словарем предпочтений
                                    cached_prefs = {}
                                
                                # Обновляем предпочтения, сохраняя объект previous_preferences
                                if cached_prefs:
                                    # Создаем копию предпочтений, чтобы не модифицировать оригинал в случае ошибок
                                    updated_preferences = copy.deepcopy(previous_preferences)
                                    
                                    # Безопасно обновляем атрибуты
                                    for key, value in cached_prefs.items():
                                        if hasattr(updated_preferences, key) and value is not None:
                                            try:
                                                # Попытка конвертации типов, если необходимо
                                                if isinstance(value, (int, float)) and key in ["budget", "weight", "height", "home_size"]:
                                                    value = float(value)
                                                # Устанавливаем атрибут
                                                setattr(updated_preferences, key, value)
                                            except Exception as attr_err:
                                                logger.warning(f"Не удалось установить атрибут {key}={value}: {str(attr_err)}")
                                                metrics["error_type"] = "cache_attribute_error"
                                                metrics["error_details"] = f"Не удалось установить атрибут {key}={value}: {str(attr_err)}"
                                    
                                    # Возвращаем результат с обновленными предпочтениями
                                    result = {
                                        **cached_data,
                                        'preferences': updated_preferences,
                                        'cache_used': True
                                    }
                                    
                                    logger.debug(f"Успешно восстановлены предпочтения из кэша для пользователя {user_id}")
                                    metrics["success"] = True
                                    metrics["end_time"] = time.time()
                                    metrics["duration"] = metrics["end_time"] - metrics["start_time"]
                                    self._log_metrics("determine_user_needs_async", metrics)
                                    return result
                            
                            # Если нет previous_preferences или не удалось их обновить, возвращаем кэшированный результат как есть
                            # Но нужно создать объект UserPreferences из словаря предпочтений
                            if "preferences" in cached_data and isinstance(cached_data["preferences"], dict):
                                try:
                                    prefs_dict = cached_data["preferences"]
                                    # Создаем новый объект UserPreferences
                                    new_preferences = UserPreferences(user_id=user_id, role=role)
                                    
                                    # Обновляем его атрибуты из словаря
                                    for key, value in prefs_dict.items():
                                        if hasattr(new_preferences, key) and value is not None:
                                            setattr(new_preferences, key, value)
                                    
                                    # Заменяем словарь на объект в результате
                                    cached_data["preferences"] = new_preferences
                                except Exception as e:
                                    logger.warning(f"Не удалось создать объект UserPreferences из кэша: {str(e)}")
                                    metrics["error_type"] = "cache_preferences_creation_error"
                                    metrics["error_details"] = f"Не удалось создать объект UserPreferences из кэша: {str(e)}"
                                    # Если не удалось создать объект, создаем новый
                                    cached_data["preferences"] = UserPreferences(user_id=user_id, role=role)
                            else:
                                # Если предпочтений нет, добавляем их
                                cached_data["preferences"] = UserPreferences(user_id=user_id, role=role)
                            
                            # Добавляем флаг использования кэша
                            cached_data["cache_used"] = True
                            
                            logger.debug(f"Успешно восстановлен результат из кэша для пользователя {user_id}")
                            metrics["success"] = True
                            metrics["end_time"] = time.time()
                            metrics["duration"] = metrics["end_time"] - metrics["start_time"]
                            self._log_metrics("determine_user_needs_async", metrics)
                            return cached_data
                            
                        except Exception as e:
                            logger.error(f"Ошибка при обработке кэшированного результата: {str(e)}")
                            metrics["error_type"] = "cache_processing_error"
                            metrics["error_details"] = f"Ошибка при обработке кэшированного результата: {str(e)}"
                            # Продолжаем выполнение без использования кэша
                except Exception as cache_error:
                    logger.error(f"Ошибка при проверке кэша: {str(cache_error)}")
                    metrics["error_type"] = "cache_access_error"
                    metrics["error_details"] = f"Ошибка при проверке кэша: {str(cache_error)}"
                    # Продолжаем выполнение без использования кэша
            
            # Создаем или используем существующие предпочтения
            preferences = previous_preferences
            if preferences is None:
                preferences = UserPreferences(user_id=user_id, role=role)
            
            # Формируем промпт в зависимости от роли
            if role == "стилист":
                prompt_template = """
                Проанализируй сообщение пользователя и определи следующие параметры:
                - бюджет (числовое значение)
                - стилевые предпочтения (формальный, повседневный, спортивный и т.д.)
                - размер одежды (S, M, L, XL и т.д.)
                - цветовые предпочтения
                - сезон (зима, весна, лето, осень)
                - типы одежды (верхняя одежда, платья, брюки и т.д.)
                - случаи использования (работа, отдых, особые случаи и т.д.)
                
                Если какой-то параметр не указан явно, оставь его пустым.
                
                Сформируй список уточняющих вопросов для параметров, которые не удалось определить.
                
                Ответ предоставь в формате JSON:
                {
                    "identified_needs": {
                        "budget": число или null,
                        "style_preferences": объект или null,
                        "size": строка или null,
                        "color_preferences": [список строк] или null,
                        "season": строка или null,
                        "garment_types": [список строк] или null,
                        "occasions": [список строк] или null
                    },
                    "clarifying_questions": [список строк с вопросами]
                }
                """
            elif role == "косметолог":
                prompt_template = """
                Проанализируй сообщение пользователя и определи следующие параметры:
                - бюджет (числовое значение)
                - тип кожи (сухая, жирная, комбинированная, нормальная)
                - проблемы с кожей (акне, морщины, пигментация и т.д.)
                - возрастная группа (например, 20-30, 30-40, 40+)
                - аллергии или непереносимость ингредиентов
                - предпочитаемые бренды
                - предпочтение органических/натуральных средств (да/нет)
                
                Если какой-то параметр не указан явно, оставь его пустым.
                
                Сформируй список уточняющих вопросов для параметров, которые не удалось определить.
                
                Ответ предоставь в формате JSON:
                {
                    "identified_needs": {
                        "budget": число или null,
                        "skin_type": строка или null,
                        "skin_concerns": [список строк] или null,
                        "age_range": строка или null,
                        "allergies": [список строк] или null,
                        "preferred_brands": [список строк] или null,
                        "organic_only": true/false или null
                    },
                    "clarifying_questions": [список строк с вопросами]
                }
                """
            elif role == "нутрициолог":
                prompt_template = """
                Проанализируй сообщение пользователя и определи следующие параметры:
                - бюджет (числовое значение)
                - цель питания (похудение, набор массы, поддержание веса, здоровое питание и т.д.)
                - диетические ограничения (вегетарианство, веганство, безглютеновая диета и т.д.)
                - вес (в кг)
                - рост (в см)
                - уровень активности (низкий, умеренный, высокий)
                - предпочтения в еде (любимые продукты, блюда)
                - аллергии или непереносимость продуктов
                
                Если какой-то параметр не указан явно, оставь его пустым.
                
                Сформируй список уточняющих вопросов для параметров, которые не удалось определить.
                
                Ответ предоставь в формате JSON:
                {
                    "identified_needs": {
                        "budget": число или null,
                        "dietary_goal": строка или null,
                        "dietary_restrictions": [список строк] или null,
                        "weight": число или null,
                        "height": число или null,
                        "activity_level": строка или null,
                        "meal_preferences": объект или null,
                        "allergies_food": [список строк] или null
                    },
                    "clarifying_questions": [список строк с вопросами]
                }
                """
            elif role == "дизайнер":
                prompt_template = """
                Проанализируй сообщение пользователя и определи следующие параметры:
                - бюджет (числовое значение)
                - стиль интерьера (скандинавский, минимализм, классический и т.д.)
                - типы комнат (гостиная, спальня, кухня и т.д.)
                - размер помещения (в кв.м)
                - цветовая схема
                - имеющаяся мебель
                - планируется ли ремонт (да/нет)
                
                Если какой-то параметр не указан явно, оставь его пустым.
                
                Сформируй список уточняющих вопросов для параметров, которые не удалось определить.
                
                Ответ предоставь в формате JSON:
                {
                    "identified_needs": {
                        "budget": число или null,
                        "interior_style": строка или null,
                        "room_types": [список строк] или null,
                        "home_size": число или null,
                        "color_scheme": [список строк] или null,
                        "existing_furniture": объект или null,
                        "renovation_planned": true/false или null
                    },
                    "clarifying_questions": [список строк с вопросами]
                }
                """
            else:
                logger.warning(f"Неизвестная роль: {role}, используем базовые вопросы")
                return {
                    "success": False,
                    "error": f"Неизвестная роль: {role}",
                    "clarifying_questions": [
                        "Какой у вас бюджет?",
                        "Какие у вас предпочтения?",
                        "Какая конкретная задача вас интересует?"
                    ],
                    "preferences_updated": False,
                    "preferences": preferences
                }
            
            # Формируем запрос к модели
            messages = [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": user_input}
            ]
            
            logger.debug(f"Отправляем запрос для определения потребностей пользователя с ролью {role}")
            
            # Отправляем запрос к API
            if self.model_type == "openrouter":
                await self._ensure_session()
                response_json = await self._call_openrouter_api_async(messages)
                response_text = response_json["choices"][0]["message"]["content"]
            else:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7
                )
                response_text = response.choices[0].message.content
            
            logger.debug(f"Получен ответ от модели: {response_text[:100]}...")
            
            # Парсим JSON из ответа
            try:
                # Проверяем и очищаем строку ответа от лишних символов
                cleaned_response = response_text.strip()
                
                # Логируем исходный ответ для отладки
                logger.debug(f"Исходный ответ от модели: {cleaned_response[:200]}...")
                
                # Метод 0: Извлечение JSON из текста (может содержать комментарии, пояснения и прочее)
                # Ищем первую открывающую и последнюю закрывающую скобки JSON
                json_start = cleaned_response.find('{')
                json_end = cleaned_response.rfind('}')
                
                if json_start == -1 or json_end == -1:
                    logger.error(f"Не удалось найти корректный JSON в ответе: {cleaned_response}")
                    raise json.JSONDecodeError("Не удалось найти корректный JSON в ответе", cleaned_response, 0)
                
                # Извлекаем JSON-часть из ответа
                json_response = cleaned_response[json_start:json_end+1]
                logger.debug(f"Извлеченный JSON: {json_response[:200]}...")
                
                # Проверяем корректность JSON
                try:
                    # Первая попытка парсинга JSON как есть
                    result = json.loads(json_response)
                    logger.info("JSON успешно распарсен с первой попытки")
                    metrics["json_parse_method"] = "direct"
                except json.JSONDecodeError as e:
                    logger.warning(f"Первая попытка парсинга JSON не удалась: {str(e)}, пробуем восстановить JSON")
                    metrics["recovery_attempts"] += 1
                    
                    try:
                        # Метод 1: Ищем паттерны с пропущенными кавычками у ключей
                        # Заменяем ключи без кавычек на ключи с кавычками: {key: value} -> {"key": value}
                        json_response_fixed = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_response)
                        # Заменяем одинарные кавычки на двойные для соответствия JSON-формату
                        json_response_fixed = json_response_fixed.replace("'", '"')
                        
                        # Логируем исправленный JSON
                        logger.debug(f"JSON после метода 1: {json_response_fixed[:200]}...")
                        
                        # Пробуем парсинг после замены кавычек
                        result = json.loads(json_response_fixed)
                        logger.info("JSON успешно восстановлен методом 1 (исправление кавычек)")
                        metrics["json_parse_method"] = "method1_quotes_fix"
                    except json.JSONDecodeError as e1:
                        logger.warning(f"Метод 1 не сработал: {str(e1)}, пробуем метод 2")
                        metrics["recovery_attempts"] += 1
                        
                        try:
                            # Метод 2: Используем более агрессивную регулярку для исправления ключей без кавычек
                            # Добавляем кавычки ко всем алфавитно-цифровым идентификаторам перед двоеточиями
                            json_response_fixed = re.sub(r'(\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', json_response)
                            json_response_fixed = json_response_fixed.replace("'", '"')
                            
                            # Удаляем возможные запятые перед закрывающими скобками
                            json_response_fixed = re.sub(r',(\s*})', r'\1', json_response_fixed)
                            # Удаляем возможные запятые перед закрывающими квадратными скобками
                            json_response_fixed = re.sub(r',(\s*\])', r'\1', json_response_fixed)
                            
                            # Логируем исправленный JSON
                            logger.debug(f"JSON после метода 2: {json_response_fixed[:200]}...")
                            
                            # Пробуем парсинг после более агрессивного исправления
                            result = json.loads(json_response_fixed)
                            logger.info("JSON успешно восстановлен методом 2 (агрессивная замена ключей)")
                            metrics["json_parse_method"] = "method2_aggressive_fix"
                        except json.JSONDecodeError as e2:
                            logger.warning(f"Метод 2 не сработал: {str(e2)}, пробуем метод 3")
                            metrics["recovery_attempts"] += 1
                            
                            try:
                                # Метод 3: Используем регулярные выражения для извлечения структуры
                                # Ищем структуру identified_needs и clarifying_questions
                                needs_match = re.search(r'"identified_needs"\s*:\s*{([^}]+)}', json_response)
                                questions_match = re.search(r'"clarifying_questions"\s*:\s*\[(.*?)\]', json_response, re.DOTALL)
                                
                                # Строим новый JSON на основе извлеченных данных
                                if needs_match and questions_match:
                                    needs_str = needs_match.group(1)
                                    questions_str = questions_match.group(1)
                                    
                                    # Создаем минимальный валидный JSON
                                    minimal_json = '{' + f'"identified_needs":{{{needs_str}}}, "clarifying_questions":[{questions_str}]' + '}'
                                    # Пробуем исправить проблемы
                                    minimal_json = minimal_json.replace("'", '"')
                                    minimal_json = re.sub(r'(\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', minimal_json)
                                    minimal_json = re.sub(r',(\s*})', r'\1', minimal_json)
                                    minimal_json = re.sub(r',(\s*\])', r'\1', minimal_json)
                                    
                                    # Логируем минимальный JSON
                                    logger.debug(f"JSON после метода 3: {minimal_json[:200]}...")
                                    
                                    # Пробуем парсинг минимального JSON
                                    result = json.loads(minimal_json)
                                    logger.info("JSON успешно восстановлен методом 3 (извлечение структуры)")
                                    metrics["json_parse_method"] = "method3_structure_extraction"
                                else:
                                    logger.warning("Не удалось извлечь структуру JSON методом 3, пробуем метод 4")
                                    metrics["recovery_attempts"] += 1
                                    
                                    # Метод 4: Используем более гибкий подход с поиском ключевых структур
                                    try:
                                        # Ищем все пары ключ-значение в формате "ключ": значение
                                        key_value_pairs = re.findall(r'"([^"]+)"\s*:\s*([^,}]+)', json_response)
                                        
                                        # Создаем словарь из найденных пар
                                        extracted_data = {}
                                        for key, value in key_value_pairs:
                                            # Пытаемся преобразовать значение в соответствующий тип
                                            try:
                                                # Если значение похоже на число
                                                if re.match(r'^-?\d+(\.\d+)?$', value.strip()):
                                                    extracted_data[key] = float(value)
                                                # Если значение похоже на null
                                                elif value.strip().lower() == 'null':
                                                    extracted_data[key] = None
                                                # Если значение похоже на булево
                                                elif value.strip().lower() in ('true', 'false'):
                                                    extracted_data[key] = value.strip().lower() == 'true'
                                                # Если значение похоже на массив или объект
                                                elif value.strip().startswith('[') or value.strip().startswith('{'):
                                                    try:
                                                        # Пытаемся парсить как JSON
                                                        extracted_data[key] = json.loads(value)
                                                    except:
                                                        # Если не получается, оставляем как строку
                                                        extracted_data[key] = value
                                                else:
                                                    # В остальных случаях считаем строкой
                                                    extracted_data[key] = value.strip().strip('"\'')
                                            except Exception as conv_err:
                                                logger.warning(f"Ошибка при преобразовании значения {key}: {str(conv_err)}")
                                                extracted_data[key] = value
                                        
                                        # Проверяем, что у нас есть необходимые ключи
                                        if "identified_needs" not in extracted_data:
                                            extracted_data["identified_needs"] = {}
                                        if "clarifying_questions" not in extracted_data:
                                            extracted_data["clarifying_questions"] = []
                                        
                                        # Используем извлеченные данные
                                        result = extracted_data
                                        logger.info("JSON успешно восстановлен методом 4 (извлечение пар ключ-значение)")
                                        metrics["json_parse_method"] = "method4_key_value_extraction"
                                    except Exception as e4:
                                        logger.error(f"Метод 4 не сработал: {str(e4)}, пробуем метод 5")
                                        metrics["recovery_attempts"] += 1
                                        
                                        # Метод 5: Используем регулярные выражения для извлечения вложенных структур
                                        try:
                                            # Более сложный подход для извлечения вложенных структур
                                            # Извлекаем объект identified_needs
                                            needs_pattern = r'"identified_needs"\s*:\s*({[^}]*})'
                                            needs_match = re.search(needs_pattern, json_response, re.DOTALL)
                                            needs_data = {}
                                            
                                            if needs_match:
                                                needs_json = needs_match.group(1)
                                                # Исправляем возможные проблемы с кавычками
                                                needs_json = re.sub(r'(\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', needs_json)
                                                needs_json = needs_json.replace("'", '"')
                                                
                                                try:
                                                    # Пытаемся парсить объект needs
                                                    needs_data = json.loads(needs_json)
                                                except:
                                                    # Если не получается, извлекаем по отдельным полям
                                                    for field in ["budget", "style_preferences", "size", "color_preferences", 
                                                                "season", "garment_types", "occasions", "skin_type", 
                                                                "skin_concerns", "age_range", "allergies", "preferred_brands",
                                                                "organic_only", "dietary_goal", "dietary_restrictions", 
                                                                "weight", "height", "activity_level", "meal_preferences",
                                                                "allergies_food", "interior_style", "room_types", 
                                                                "home_size", "color_scheme", "existing_furniture", 
                                                                "renovation_planned"]:
                                                        field_pattern = fr'"{field}"\s*:\s*([^,}}]+)'
                                                        field_match = re.search(field_pattern, needs_json)
                                                        if field_match:
                                                            value_str = field_match.group(1).strip()
                                                            # Преобразуем значение в соответствующий тип
                                                            try:
                                                                if value_str.lower() == 'null':
                                                                    needs_data[field] = None
                                                                elif value_str.lower() in ('true', 'false'):
                                                                    needs_data[field] = value_str.lower() == 'true'
                                                                elif re.match(r'^-?\d+(\.\d+)?$', value_str):
                                                                    needs_data[field] = float(value_str)
                                                                elif value_str.startswith('[') and value_str.endswith(']'):
                                                                    # Пытаемся парсить как список
                                                                    try:
                                                                        needs_data[field] = json.loads(value_str)
                                                                    except:
                                                                        needs_data[field] = value_str
                                                                elif value_str.startswith('{') and value_str.endswith('}'):
                                                                    # Пытаемся парсить как объект
                                                                    try:
                                                                        needs_data[field] = json.loads(value_str)
                                                                    except:
                                                                        needs_data[field] = value_str
                                                                else:
                                                                    # Удаляем кавычки, если они есть
                                                                    needs_data[field] = value_str.strip('"\'')
                                                            except Exception as field_err:
                                                                logger.warning(f"Ошибка при обработке поля {field}: {str(field_err)}")
                                                                needs_data[field] = value_str
                                            
                                            # Извлекаем список clarifying_questions
                                            questions_pattern = r'"clarifying_questions"\s*:\s*(\[.*?\])'
                                            questions_match = re.search(questions_pattern, json_response, re.DOTALL)
                                            questions_data = []
                                            
                                            if questions_match:
                                                questions_json = questions_match.group(1)
                                                questions_json = questions_json.replace("'", '"')
                                                
                                                try:
                                                    # Пытаемся парсить список вопросов
                                                    questions_data = json.loads(questions_json)
                                                except:
                                                    # Если не получается, извлекаем отдельные строки
                                                    question_items = re.findall(r'"([^"]+)"', questions_json)
                                                    questions_data = question_items
                                            
                                            # Создаем результирующий объект
                                            result = {
                                                "identified_needs": needs_data,
                                                "clarifying_questions": questions_data
                                            }
                                            
                                            logger.info("JSON успешно восстановлен методом 5 (извлечение сложных структур)")
                                            metrics["json_parse_method"] = "method5_complex_extraction"
                                            
                                        except Exception as e5:
                                            logger.error(f"Метод 5 не сработал: {str(e5)}, пробуем метод 6")
                                            metrics["recovery_attempts"] += 1
                                            
                                            # Метод 6: Интеллектуальная реконструкция JSON с исправлением наиболее распространенных проблем
                                            try:
                                                # Шаг 1: Нормализация текста ответа с удалением лишних символов
                                                normalized_json = re.sub(r'\s*[\r\n]+\s*', ' ', json_response)
                                                logger.debug(f"Нормализованный JSON: {normalized_json[:200]}...")
                                                
                                                # Шаг 2: Исправление основных проблем с JSON-форматом
                                                # 2.1: Исправление кавычек в ключах и значениях (замена одинарных на двойные)
                                                fixed_json = normalized_json.replace("'", '"')
                                                # 2.2: Исправление незаключенных в кавычки ключей (все виды допустимых идентификаторов)
                                                fixed_json = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', fixed_json)
                                                # 2.3: Исправление необработанных булевых и null значений
                                                fixed_json = re.sub(r':\s*null([,}])', r': null\1', fixed_json)
                                                fixed_json = re.sub(r':\s*true([,}])', r': true\1', fixed_json)
                                                fixed_json = re.sub(r':\s*false([,}])', r': false\1', fixed_json)
                                                # 2.4: Удаление лишних запятых перед закрывающимися скобками
                                                fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                                                # 2.5: Исправление отсутствия запятых между элементами
                                                fixed_json = re.sub(r'(["\w\d}])\s*([{[])', r'\1, \2', fixed_json)
                                                # 2.6: Исправление неэкранированных кавычек в строковых значениях
                                                fixed_json = re.sub(r':\s*"([^"]*)"([^,}]*)"([^"]*)"', r': "\1\2\3"', fixed_json)

                                                logger.debug(f"Исправленный JSON методом 6: {fixed_json[:200]}...")
                                                
                                                # Шаг 3: Проверка баланса скобок для валидности JSON
                                                opening_braces = sum(1 for c in fixed_json if c in '{[')
                                                closing_braces = sum(1 for c in fixed_json if c in '}]')
                                                
                                                if opening_braces != closing_braces:
                                                    logger.warning(f"Несбалансированные скобки в JSON: {opening_braces} открывающих и {closing_braces} закрывающих")
                                                    # 3.1: Если не хватает закрывающих скобок, добавляем их
                                                    if opening_braces > closing_braces:
                                                        fixed_json += '}' * (opening_braces - closing_braces)
                                                    # 3.2: Если лишние закрывающие скобки, найдем и удалим лишние
                                                    else:
                                                        # Находим индекс последней открывающей скобки
                                                        last_opening = -1
                                                        for i, c in enumerate(fixed_json):
                                                            if c in '{[':
                                                                last_opening = i
                                                        
                                                        if last_opening > -1:
                                                            fixed_json = fixed_json[:last_opening+1]
                                                            # Добавляем соответствующую закрывающую скобку
                                                            if fixed_json[last_opening] == '{':
                                                                fixed_json += '}'
                                                            else:
                                                                fixed_json += ']'
                                                
                                                # Шаг 4: Попытка парсинга исправленного JSON
                                                try:
                                                    result = json.loads(fixed_json)
                                                    logger.info("JSON успешно восстановлен методом 6 (интеллектуальная реконструкция)")
                                                    metrics["json_parse_method"] = "method6_smart_reconstruction"
                                                except json.JSONDecodeError as e6_parse:
                                                    # Шаг 5: Если не получилось, используем структурное восстановление JSON
                                                    logger.warning(f"Ошибка при парсинге исправленного JSON методом 6: {str(e6_parse)}")
                                                    
                                                    # 5.1: Ищем ключевые части JSON
                                                    identified_needs_start = fixed_json.find('"identified_needs"')
                                                    clarifying_questions_start = fixed_json.find('"clarifying_questions"')
                                                    
                                                    needs = {}
                                                    questions = []
                                                    
                                                    # Если нашли секцию identified_needs
                                                    if identified_needs_start != -1:
                                                        needs_section = fixed_json[identified_needs_start:]
                                                        # Ищем открывающую фигурную скобку после ключа
                                                        open_brace = needs_section.find('{', needs_section.find(':'))
                                                        if open_brace != -1:
                                                            needs_subsection = needs_section[open_brace:]
                                                            # Находим соответствующую закрывающую скобку
                                                            level = 0
                                                            close_index = -1
                                                            for i, char in enumerate(needs_subsection):
                                                                if char == '{':
                                                                    level += 1
                                                                elif char == '}':
                                                                    level -= 1
                                                                    if level == 0:
                                                                        close_index = i
                                                                        break
                                                            
                                                            if close_index != -1:
                                                                needs_str = needs_subsection[:close_index+1]
                                                                try:
                                                                    needs = json.loads(needs_str)
                                                                except:
                                                                    # Если не удалось распарсить, используем простую структуру
                                                                    logger.warning("Не удалось распарсить объект identified_needs")
                                                                    needs = {}
                                                                    # Извлекаем ключи и значения по отдельности
                                                                    field_values = re.findall(r'"([^"]+)"\s*:\s*([^,}]+)', needs_str)
                                                                    for field, value in field_values:
                                                                        needs = self._process_field_value(field, value, needs)
                                                    
                                                    # Если нашли секцию clarifying_questions
                                                    if clarifying_questions_start != -1:
                                                        questions_section = fixed_json[clarifying_questions_start:]
                                                        # Ищем открывающую квадратную скобку после ключа
                                                        open_bracket = questions_section.find('[', questions_section.find(':'))
                                                        if open_bracket != -1:
                                                            questions_subsection = questions_section[open_bracket:]
                                                            # Находим соответствующую закрывающую скобку
                                                            level = 0
                                                            close_index = -1
                                                            for i, char in enumerate(questions_subsection):
                                                                if char == '[':
                                                                    level += 1
                                                                elif char == ']':
                                                                    level -= 1
                                                                    if level == 0:
                                                                        close_index = i
                                                                        break
                                                            
                                                            if close_index != -1:
                                                                questions_str = questions_subsection[:close_index+1]
                                                                try:
                                                                    questions = json.loads(questions_str)
                                                                except:
                                                                    # Если не удалось распарсить, извлекаем вопросы по отдельности
                                                                    logger.warning("Не удалось распарсить список clarifying_questions")
                                                                    questions = []
                                                                    # Ищем строки в кавычках
                                                                    questions_items = re.findall(r'"([^"]+)"', questions_str)
                                                                    questions = questions_items
                                                    
                                                    # Собираем итоговый результат
                                                    result = {
                                                        "identified_needs": needs,
                                                        "clarifying_questions": questions
                                                    }
                                                    
                                                    logger.info("JSON успешно восстановлен структурным методом 6")
                                                    metrics["json_parse_method"] = "method6_structural_recovery"
                                            
                                            except Exception as e6:
                                                logger.error(f"Все методы восстановления JSON не сработали: {str(e6)}")
                                                metrics["json_parse_method"] = "fallback"
                                                
                                                # Создаем базовый объект результата
                                                result = {
                                                    "identified_needs": {},
                                                    "clarifying_questions": [
                                                        "Пожалуйста, предоставьте больше информации о ваших предпочтениях.",
                                                        "Какой у вас бюджет?",
                                                        "Уточните, пожалуйста, ваши конкретные пожелания."
                                                    ]
                                                }
                            except Exception as e3:
                                logger.error(f"Ошибка при восстановлении JSON методом 3: {str(e3)}")
                                metrics["json_parse_method"] = "fallback"
                                
                                # Создаем базовый объект результата
                                result = {
                                    "identified_needs": {},
                                    "clarifying_questions": [
                                        "Пожалуйста, предоставьте больше информации о ваших предпочтениях.",
                                        "Какой у вас бюджет?",
                                        "Уточните, пожалуйста, ваши конкретные пожелания."
                                    ]
                                }
                
                # Проверяем наличие необходимых ключей в результате
                if "identified_needs" not in result:
                    logger.warning("В ответе отсутствует ключ identified_needs, создаем пустой объект")
                    result["identified_needs"] = {}
                
                if "clarifying_questions" not in result:
                    logger.warning("В ответе отсутствует ключ clarifying_questions, создаем пустой список")
                    result["clarifying_questions"] = []
                
                identified_needs = result.get("identified_needs", {})
                clarifying_questions = result.get("clarifying_questions", [])
                
                # Логируем структуру полученного JSON для отладки
                logger.debug(f"Структура извлеченного JSON: {list(result.keys())}")
                logger.debug(f"Identified_needs: {identified_needs.keys() if isinstance(identified_needs, dict) else 'не словарь'}")
                logger.debug(f"Clarifying_questions (количество): {len(clarifying_questions)}")
                
                # Обновляем предпочтения пользователя
                preferences_updated = False
                
                if role == "стилист":
                    if "budget" in identified_needs and identified_needs["budget"] is not None:
                        preferences.budget = float(identified_needs["budget"])
                        preferences_updated = True
                    if "style_preferences" in identified_needs and identified_needs["style_preferences"] is not None:
                        preferences.style_preferences = identified_needs["style_preferences"]
                        preferences_updated = True
                    if "size" in identified_needs and identified_needs["size"] is not None:
                        preferences.size = identified_needs["size"]
                        preferences_updated = True
                    if "color_preferences" in identified_needs and identified_needs["color_preferences"] is not None:
                        preferences.color_preferences = identified_needs["color_preferences"]
                        preferences_updated = True
                    if "season" in identified_needs and identified_needs["season"] is not None:
                        preferences.season = identified_needs["season"]
                        preferences_updated = True
                    if "garment_types" in identified_needs and identified_needs["garment_types"] is not None:
                        preferences.garment_types = identified_needs["garment_types"]
                        preferences_updated = True
                    if "occasions" in identified_needs and identified_needs["occasions"] is not None:
                        preferences.occasions = identified_needs["occasions"]
                        preferences_updated = True
                
                elif role == "косметолог":
                    if "budget" in identified_needs and identified_needs["budget"] is not None:
                        preferences.budget = float(identified_needs["budget"])
                        preferences_updated = True
                    if "skin_type" in identified_needs and identified_needs["skin_type"] is not None:
                        preferences.skin_type = identified_needs["skin_type"]
                        preferences_updated = True
                    if "skin_concerns" in identified_needs and identified_needs["skin_concerns"] is not None:
                        preferences.skin_concerns = identified_needs["skin_concerns"]
                        preferences_updated = True
                    if "age_range" in identified_needs and identified_needs["age_range"] is not None:
                        preferences.age_range = identified_needs["age_range"]
                        preferences_updated = True
                    if "allergies" in identified_needs and identified_needs["allergies"] is not None:
                        preferences.allergies = identified_needs["allergies"]
                        preferences_updated = True
                    if "preferred_brands" in identified_needs and identified_needs["preferred_brands"] is not None:
                        preferences.preferred_brands = identified_needs["preferred_brands"]
                        preferences_updated = True
                    if "organic_only" in identified_needs and identified_needs["organic_only"] is not None:
                        preferences.organic_only = identified_needs["organic_only"]
                        preferences_updated = True
                
                elif role == "нутрициолог":
                    if "budget" in identified_needs and identified_needs["budget"] is not None:
                        preferences.budget = float(identified_needs["budget"])
                        preferences_updated = True
                    if "dietary_goal" in identified_needs and identified_needs["dietary_goal"] is not None:
                        preferences.dietary_goal = identified_needs["dietary_goal"]
                        preferences_updated = True
                    if "dietary_restrictions" in identified_needs and identified_needs["dietary_restrictions"] is not None:
                        preferences.dietary_restrictions = identified_needs["dietary_restrictions"]
                        preferences_updated = True
                    if "weight" in identified_needs and identified_needs["weight"] is not None:
                        preferences.weight = float(identified_needs["weight"])
                        preferences_updated = True
                    if "height" in identified_needs and identified_needs["height"] is not None:
                        preferences.height = float(identified_needs["height"])
                        preferences_updated = True
                    if "activity_level" in identified_needs and identified_needs["activity_level"] is not None:
                        preferences.activity_level = identified_needs["activity_level"]
                        preferences_updated = True
                    if "meal_preferences" in identified_needs and identified_needs["meal_preferences"] is not None:
                        preferences.meal_preferences = identified_needs["meal_preferences"]
                        preferences_updated = True
                    if "allergies_food" in identified_needs and identified_needs["allergies_food"] is not None:
                        preferences.allergies_food = identified_needs["allergies_food"]
                        preferences_updated = True
                
                elif role == "дизайнер":
                    if "budget" in identified_needs and identified_needs["budget"] is not None:
                        preferences.budget = float(identified_needs["budget"])
                        preferences_updated = True
                    if "interior_style" in identified_needs and identified_needs["interior_style"] is not None:
                        preferences.interior_style = identified_needs["interior_style"]
                        preferences_updated = True
                    if "room_types" in identified_needs and identified_needs["room_types"] is not None:
                        preferences.room_types = identified_needs["room_types"]
                        preferences_updated = True
                    if "home_size" in identified_needs and identified_needs["home_size"] is not None:
                        preferences.home_size = float(identified_needs["home_size"])
                        preferences_updated = True
                    if "color_scheme" in identified_needs and identified_needs["color_scheme"] is not None:
                        preferences.color_scheme = identified_needs["color_scheme"]
                        preferences_updated = True
                    if "existing_furniture" in identified_needs and identified_needs["existing_furniture"] is not None:
                        preferences.existing_furniture = identified_needs["existing_furniture"]
                        preferences_updated = True
                    if "renovation_planned" in identified_needs and identified_needs["renovation_planned"] is not None:
                        preferences.renovation_planned = identified_needs["renovation_planned"]
                        preferences_updated = True
                
                # Обновляем время последнего обновления
                preferences.last_updated = datetime.utcnow()
                
                logger.info(f"Успешно определены потребности пользователя для роли {role}. Обновлено: {preferences_updated}")
                
                # Формируем результат
                result_dict = {
                    "success": True,
                    "identified_needs": identified_needs,
                    "clarifying_questions": clarifying_questions,
                    "preferences_updated": preferences_updated,
                    "preferences": preferences
                }
                
                # Логируем метрики успешного выполнения
                metrics["success"] = True
                metrics["end_time"] = time.time()
                metrics["duration"] = metrics["end_time"] - metrics["start_time"]
                metrics["json_parse_method"] = "success"
                self._log_metrics("determine_user_needs_async", metrics)
                
                # Сохраняем результат в кэш, если кэширование включено
                if self.cache_enabled:
                    try:
                        # Создаем копию для кэширования, чтобы не модифицировать оригинал
                        result_for_cache = copy.deepcopy(result_dict)
                        
                        # Преобразуем предпочтения в словарь для сериализации
                        if "preferences" in result_for_cache and isinstance(result_for_cache["preferences"], UserPreferences):
                            try:
                                # Используем метод dict() для сериализации, если он есть
                                if hasattr(result_for_cache["preferences"], "dict") and callable(getattr(result_for_cache["preferences"], "dict")):
                                    result_for_cache["preferences"] = result_for_cache["preferences"].dict()
                                else:
                                    # Иначе создаем словарь из атрибутов объекта
                                    prefs_dict = {}
                                    for key, value in vars(result_for_cache["preferences"]).items():
                                        # Обрабатываем специальные типы, которые не сериализуются в JSON
                                        if key.startswith('_'):
                                            continue  # Пропускаем приватные атрибуты
                                        if isinstance(value, datetime.datetime):
                                            prefs_dict[key] = value.isoformat()
                                        elif isinstance(value, (set, frozenset)):
                                            prefs_dict[key] = list(value)
                                        else:
                                            try:
                                                # Проверяем, сериализуется ли значение в JSON
                                                json.dumps({key: value})
                                                prefs_dict[key] = value
                                            except TypeError:
                                                # Если нет, преобразуем в строку
                                                prefs_dict[key] = str(value)
                                    result_for_cache["preferences"] = prefs_dict
                            except Exception as e:
                                logger.warning(f"Ошибка при сериализации предпочтений для кэша: {str(e)}")
                                # В случае ошибки удаляем предпочтения из результата для кэша
                                result_for_cache.pop("preferences", None)
                        
                        # Создаем более детерминистичный ключ кэша
                        sanitized_input = re.sub(r'\s+', ' ', user_input.lower().strip())
                        cache_key = f"determine_needs_{user_id}_{role}_{hash(sanitized_input)}"
                        
                        # Используем default=str для корректной сериализации дат и других объектов
                        json_result = json.dumps(result_for_cache, default=str, ensure_ascii=False)
                        self._save_to_cache(cache_key, json_result)
                        logger.debug(f"Результат определения потребностей сохранен в кэш с ключом: {cache_key}")
                    except Exception as e:
                        logger.warning(f"Не удалось сохранить результат в кэш: {str(e)}")
                        import traceback
                        logger.debug(f"Трассировка стека ошибки при сохранении в кэш: {traceback.format_exc()}")
                
                return result_dict
            
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при парсинге JSON из ответа: {str(e)}")
                logger.debug(f"Ответ, вызвавший ошибку: {response_text}")
                return {
                    "success": False,
                    "error": f"Ошибка при парсинге JSON: {str(e)}",
                    "clarifying_questions": [
                        "Какой у вас бюджет?",
                        "Какие у вас предпочтения?",
                        "Какая конкретная задача вас интересует?"
                    ],
                    "preferences_updated": False,
                    "preferences": preferences
                }
        
        except Exception as e:
            logger.error(f"Ошибка при определении потребностей пользователя: {str(e)}")
            import traceback
            logger.debug(f"Трассировка стека ошибки: {traceback.format_exc()}")
            
            # Классифицируем ошибку
            error_type = type(e).__name__
            metrics["error_type"] = error_type
            metrics["error_details"] = str(e)
            metrics["success"] = False
            metrics["end_time"] = time.time()
            metrics["duration"] = metrics["end_time"] - metrics["start_time"]
            self._log_metrics("determine_user_needs_async", metrics)
            
            # Пытаемся восстановиться после ошибки
            try:
                # Создаем базовые предпочтения, если их нет
                recovery_preferences = previous_preferences or UserPreferences(user_id=user_id, role=role)
                
                # Пытаемся извлечь хоть какую-то информацию из запроса пользователя
                recovery_needs = {}
                recovery_questions = [
                    "Какой у вас бюджет?",
                    "Какие у вас предпочтения?",
                    "Какая конкретная задача вас интересует?"
                ]
                
                # Простой анализ текста для извлечения базовой информации
                if "бюджет" in user_input.lower():
                    # Ищем числа рядом со словом "бюджет"
                    budget_match = re.search(r'бюджет\D*(\d+)', user_input.lower())
                    if budget_match:
                        try:
                            recovery_needs["budget"] = float(budget_match.group(1))
                            # Если нашли бюджет, обновляем предпочтения
                            recovery_preferences.budget = float(budget_match.group(1))
                        except:
                            pass
                
                # Возвращаем результат восстановления
                return {
                    "success": False,
                    "error": f"Ошибка: {str(e)}",
                    "error_type": error_type,
                    "recovery_attempted": True,
                    "identified_needs": recovery_needs,
                    "clarifying_questions": recovery_questions,
                    "preferences_updated": len(recovery_needs) > 0,
                    "preferences": recovery_preferences
                }
            except Exception as recovery_error:
                # Если даже восстановление не удалось, возвращаем минимальный результат
                logger.error(f"Ошибка при попытке восстановления: {str(recovery_error)}")
                return {
                    "success": False,
                    "error": f"Ошибка: {str(e)}",
                    "error_type": error_type,
                    "recovery_attempted": False,
                    "clarifying_questions": [
                        "Какой у вас бюджет?",
                        "Какие у вас предпочтения?",
                        "Какая конкретная задача вас интересует?"
                    ],
                    "preferences_updated": False,
                    "preferences": previous_preferences or UserPreferences(user_id=user_id, role=role)
                }

    def determine_user_needs(
        self,
        user_id: str,
        role: str,
        user_input: str,
        previous_preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        """
        Синхронная обертка для метода determine_user_needs_async.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            user_input: Входящее сообщение пользователя
            previous_preferences: Предыдущие предпочтения пользователя (опционально)
            
        Returns:
            Словарь с результатами анализа:
            - success: Успешность операции
            - identified_needs: Определенные потребности
            - clarifying_questions: Уточняющие вопросы
            - preferences_updated: Были ли обновлены предпочтения
            - preferences: Обновленные предпочтения
        
        Example:
            >>> assistant = ChatAssistant()
            >>> result = assistant.determine_user_needs(
            ...     user_id="user123",
            ...     role="нутрициолог",
            ...     user_input="Я хочу составить план питания для похудения. У меня аллергия на орехи.")
            >>> print(result["identified_needs"]["dietary_goal"])
            'похудение'
        """
        loop = None
        new_loop_created = False
        
        try:
            # Создаем или получаем существующий event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                new_loop_created = True
                logger.debug("Создан новый event loop")
            
            # Вспомогательная функция для корректного закрытия сессии
            async def determine_and_close():
                try:
                    # Обязательно инициализируем сессию перед запросом
                    await self._ensure_session()
                    # Выполняем основной метод
                    return await self.determine_user_needs_async(user_id, role, user_input, previous_preferences)
                finally:
                    # Обязательно закрываем сессию после выполнения запроса
                    if hasattr(self, 'http_session') and self.http_session and not self.http_session.closed:
                        try:
                            await self.http_session.close()
                            logger.debug("HTTP-сессия успешно закрыта")
                        except Exception as close_error:
                            logger.warning(f"Ошибка при закрытии HTTP-сессии: {str(close_error)}")
            
            # Выполняем асинхронную функцию с корректным закрытием сессии
            result = loop.run_until_complete(determine_and_close())
            logger.debug("Запрос успешно выполнен")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в синхронной обертке determine_user_needs: {str(e)}")
            import traceback
            logger.error(f"Трассировка стека: {traceback.format_exc()}")
            # Возвращаем объект с информацией об ошибке
            return {
                "success": False,
                "error": f"Ошибка: {str(e)}",
                "clarifying_questions": [
                    "Какой у вас бюджет?",
                    "Какие у вас предпочтения?",
                    "Какая конкретная задача вас интересует?"
                ],
                "preferences_updated": False,
                "preferences": previous_preferences or UserPreferences(user_id=user_id, role=role)
            }
        finally:
            # Закрываем event loop, если создали новый
            if new_loop_created and loop is not None:
                try:
                    # Закрываем все оставшиеся таски
                    if hasattr(loop, 'shutdown_asyncgens'):
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                    logger.debug("Созданный event loop успешно закрыт")
                except Exception as loop_error:
                    logger.warning(f"Ошибка при закрытии event loop: {str(loop_error)}")

    def _sanitize_cache_key_input(self, input_str: str) -> str:
        """
        Преобразует входную строку в допустимый ключ кеша, удаляя стоп-слова и специальные символы.
        """
        # Преобразование к нижнему регистру
        input_str = input_str.lower()
        
        # Удаление пунктуации и замена на пробелы
        translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
        input_str = input_str.translate(translator)
        
        # Разбиение по словам
        words = input_str.split()
        
        # Фильтрация стоп-слов
        stop_words = {'и', 'в', 'не', 'на', 'с', 'по', 'за', 'от', 'к', 'а', 'но', 'или', 'что', 'как',
                      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'of'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # Удаляем дубликаты и сортируем
        unique_words = sorted(set(filtered_words))
        
        # Соединяем в строку
        return '_'.join(unique_words)
    
    def _process_field_value(self, field, value, needs):
        """
        Вспомогательная функция для обработки значения поля при парсинге JSON.
        """
        try:
            # Преобразуем значение в правильный тип
            cleaned_value = value.strip()
            if cleaned_value.lower() == 'null':
                needs[field] = None
            elif cleaned_value.lower() in ('true', 'false'):
                needs[field] = cleaned_value.lower() == 'true'
            elif re.match(r'^-?\d+(\.\d+)?$', cleaned_value):
                needs[field] = float(cleaned_value)
            else:
                needs[field] = cleaned_value.strip('"')
        except Exception as val_err:
            logger.warning(f"Ошибка преобразования значения поля {field}: {str(val_err)}")
            needs[field] = value.strip('"')
        return needs

    def _log_metrics(self, method_name: str, metrics: Dict[str, Any]) -> None:
        """
        Логирует метрики выполнения метода с ротацией файлов.
        
        Args:
            method_name: Название метода
            metrics: Словарь с метриками
        """
        try:
            # Создаем директорию для метрик, если её нет
            metrics_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics")
            os.makedirs(metrics_dir, exist_ok=True)
            
            # Формируем имя файла с метриками и его максимальный размер
            date_str = datetime.now().strftime("%Y-%m-%d")
            metrics_file = os.path.join(metrics_dir, f"{method_name}_{date_str}.jsonl")
            max_file_size = 5 * 1024 * 1024  # 5 МБ
            
            # Проверяем размер файла
            if os.path.exists(metrics_file) and os.path.getsize(metrics_file) > max_file_size:
                # Если файл превышает максимальный размер, создаем новый с временной меткой
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(metrics_dir, f"{method_name}_{date_str}_{timestamp}.jsonl")
                try:
                    os.rename(metrics_file, backup_file)
                    logger.debug(f"Файл метрик {metrics_file} переименован в {backup_file}")
                except Exception as e:
                    logger.warning(f"Не удалось переименовать файл метрик: {str(e)}")
                    # Если переименование не удалось, просто продолжаем с тем же файлом
            
            # Обогащаем метрики дополнительной информацией
            metrics["timestamp"] = datetime.now().isoformat()
            metrics["session_id"] = id(self)  # Уникальный идентификатор сессии
            
            # Добавляем информацию о системе
            metrics["system_info"] = {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "interpreter": sys.executable
            }
            
            # Добавляем статус операции
            if "success" not in metrics:
                metrics["success"] = False  # По умолчанию считаем неуспешной
            
            # Классифицируем ошибки более детально
            if not metrics["success"] and "error_type" in metrics:
                # Определяем категорию ошибки
                error_type = metrics["error_type"]
                
                if error_type in ["JSONDecodeError", "json.decoder.JSONDecodeError"]:
                    metrics["error_category"] = "json_parsing"
                elif error_type in ["KeyError", "IndexError", "TypeError", "ValueError"]:
                    metrics["error_category"] = "data_processing"
                elif error_type in ["ClientError", "ClientConnectorError", "ClientResponseError", "TimeoutError", "asyncio.TimeoutError"]:
                    metrics["error_category"] = "network"
                elif error_type in ["FileNotFoundError", "PermissionError", "IOError"]:
                    metrics["error_category"] = "file_system"
                else:
                    metrics["error_category"] = "other"
            
            # Записываем метрики в файл
            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics, default=str) + "\n")
            
            # Если это ошибка, также записываем в отдельный файл ошибок
            if not metrics["success"]:
                error_file = os.path.join(metrics_dir, f"errors_{date_str}.jsonl")
                with open(error_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(metrics, default=str) + "\n")
                    
            logger.debug(f"Метрики для метода {method_name} успешно записаны")
            
            # Периодически выполняем очистку старых метрик (вероятность 1%)
            if random.random() < 0.01:
                self._cleanup_old_metrics(metrics_dir)
                
        except Exception as e:
            logger.warning(f"Ошибка при записи метрик: {str(e)}")
    
    def _cleanup_old_metrics(self, metrics_dir: str) -> None:
        """
        Очищает старые файлы метрик.
        
        Args:
            metrics_dir: Путь к директории с метриками
        """
        try:
            # Если директория не существует, ничего не делаем
            if not os.path.exists(metrics_dir):
                return
                
            # Текущее время
            current_time = time.time()
            
            # Удаляем файлы старше 30 дней
            max_age = 30 * 24 * 3600  # 30 дней в секундах
            removed_count = 0
            
            for file_name in os.listdir(metrics_dir):
                file_path = os.path.join(metrics_dir, file_name)
                
                # Если это не файл, пропускаем
                if not os.path.isfile(file_path):
                    continue
                    
                # Если файл старше max_age, удаляем
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Не удалось удалить старый файл метрик {file_name}: {str(e)}")
            
            if removed_count > 0:
                logger.info(f"Очистка метрик: удалено {removed_count} старых файлов")
                
        except Exception as e:
            logger.warning(f"Ошибка при очистке старых метрик: {str(e)}")

    def parse_bank_statement(self, file_path: str, force_reparse: bool = False) -> dict:
        """
        Парсит банковскую выписку и возвращает данные о транзакциях.
        
        Args:
            file_path: Путь к файлу банковской выписки (PDF или текстовый файл)
            force_reparse: Пересчитать данные, даже если они есть в кэше
            
        Returns:
            Словарь с данными о транзакциях и метаданными выписки
        """
        if not BANK_STATEMENT_PARSER_AVAILABLE:
            raise ImportError("Модуль bank_statement_parser недоступен. Установите необходимые зависимости.")
        
        if not self.bank_statement_parser:
            self.bank_statement_parser = BankStatementParser(cache_dir=self.bank_statement_cache_dir)
        
        # Проверяем расширение файла
        if file_path.lower().endswith('.pdf'):
            # Парсим PDF выписку
            transactions_df = self.bank_statement_parser.parse_pdf_statement(file_path, force_reparse)
        elif file_path.lower().endswith('.txt'):
            # Парсим текстовую выписку
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata = self.bank_statement_parser._extract_statement_metadata(text)
            transactions = self.bank_statement_parser._extract_transactions_from_text(text)
            if transactions:
                import pandas as pd
                transactions_df = pd.DataFrame(transactions)
                # Добавляем метаданные
                for key, value in metadata.items():
                    transactions_df[key] = value
            else:
                return {"error": "Не удалось извлечь транзакции из текстового файла"}
        else:
            return {"error": "Неподдерживаемый формат файла. Поддерживаются только файлы .pdf и .txt"}
        
        if transactions_df.empty:
            return {"error": "Не удалось извлечь транзакции из выписки"}
        
        # Анализируем расходы по категориям
        category_spending = self.bank_statement_parser.analyze_spending_by_category(transactions_df)
        
        # Получаем тренд расходов по месяцам
        monthly_trend = self.bank_statement_parser.get_monthly_spending_trend(transactions_df)
        
        # Прогнозируем будущие расходы
        future_spending = self.bank_statement_parser.predict_future_spending(transactions_df)
        
        # Формируем результат
        result = {
            "transactions_count": len(transactions_df),
            "categories": category_spending.to_dict('records') if not category_spending.empty else [],
            "monthly_trend": monthly_trend.to_dict('records') if not monthly_trend.empty else [],
            "future_spending": future_spending,
            "metadata": {}
        }
        
        # Добавляем метаданные, если они есть
        metadata_fields = ["Номер_договора", "Номер_счета", "Дата_договора", "Период_с", "Период_по", "ФИО"]
        for field in metadata_fields:
            if field in transactions_df.columns and not transactions_df.empty:
                result["metadata"][field] = transactions_df[field].iloc[0]
        
        return result
    
    def generate_spending_report(self, file_path: str, output_dir: str = "reports/bank_analytics") -> dict:
        """
        Генерирует отчет о расходах на основе банковской выписки с визуализацией.
        
        Args:
            file_path: Путь к файлу банковской выписки
            output_dir: Директория для сохранения отчета
            
        Returns:
            Словарь с данными отчета и путями к визуализациям
        """
        if not BANK_STATEMENT_PARSER_AVAILABLE:
            raise ImportError("Модуль bank_statement_parser недоступен. Установите необходимые зависимости.")
        
        if not self.bank_statement_parser:
            self.bank_statement_parser = BankStatementParser(cache_dir=self.bank_statement_cache_dir)
        
        # Проверяем расширение файла
        if file_path.lower().endswith('.pdf'):
            # Парсим PDF выписку
            transactions_df = self.bank_statement_parser.parse_pdf_statement(file_path)
        elif file_path.lower().endswith('.txt'):
            # Парсим текстовую выписку
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata = self.bank_statement_parser._extract_statement_metadata(text)
            transactions = self.bank_statement_parser._extract_transactions_from_text(text)
            if transactions:
                import pandas as pd
                transactions_df = pd.DataFrame(transactions)
                # Добавляем метаданные
                for key, value in metadata.items():
                    transactions_df[key] = value
            else:
                return {"error": "Не удалось извлечь транзакции из текстового файла"}
        else:
            return {"error": "Неподдерживаемый формат файла. Поддерживаются только файлы .pdf и .txt"}
        
        if transactions_df.empty:
            return {"error": "Не удалось извлечь транзакции из выписки"}
        
        # Генерируем отчет с визуализацией
        report = self.bank_statement_parser.generate_spending_report(transactions_df, output_dir=output_dir)
        
        return report
    
    def get_financial_recommendations(self, file_path: str, user_query: str) -> dict:
        """
        Формирует финансовые рекомендации на основе анализа банковской выписки и запроса пользователя.
        
        Args:
            file_path: Путь к файлу банковской выписки
            user_query: Запрос пользователя для формирования рекомендаций
            
        Returns:
            Словарь с финансовыми рекомендациями и анализом расходов
        """
        # Парсим банковскую выписку
        parsing_result = self.parse_bank_statement(file_path)
        
        if "error" in parsing_result:
            return parsing_result
        
        # Формируем контекст для модели
        spending_context = "Анализ расходов пользователя:\n"
        
        # Добавляем информацию о категориях расходов
        spending_context += "\nРасходы по категориям:\n"
        for category in parsing_result["categories"]:
            spending_context += f"- {category['Категория']}: {category['Сумма']:.2f} руб.\n"
        
        # Добавляем прогноз расходов
        spending_context += "\nПрогноз расходов на следующий месяц:\n"
        for category, amount in parsing_result["future_spending"].items():
            spending_context += f"- {category}: {amount:.2f} руб.\n"
        
        # Формируем промпт для модели
        prompt = f"""Ты финансовый аналитик, который дает рекомендации на основе банковских выписок.
Проанализируй данные о расходах пользователя и ответь на запрос.

{spending_context}

Запрос пользователя: {user_query}

Дай конкретные, персонализированные рекомендации по управлению финансами, основываясь на анализе расходов.
Обязательно укажи возможности оптимизации бюджета, если они есть.
"""
        
        # Генерируем ответ с помощью модели
        response = self.generate_response(prompt, max_tokens=1500)
        
        # Формируем результат
        result = {
            "analysis": parsing_result,
            "recommendations": response
        }
        
        return result