#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки синхронного метода find_similar_products_wildberries.
"""

import os
import logging
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from assistant import ChatAssistant

# Проверяем наличие модуля encoding_utils
try:
    from encoding_utils import (
        setup_console_encoding, 
        safe_write, 
        safe_read, 
        print_system_info, 
        is_powershell,
        setup_file_logger
    )
    ENCODING_UTILS_ENABLED = True
except ImportError:
    ENCODING_UTILS_ENABLED = False
    print("ВНИМАНИЕ: Модуль encoding_utils не найден. Будет использована стандартная обработка кодировки.")

# Настройка кодировки консоли
if ENCODING_UTILS_ENABLED:
    setup_console_encoding()
    print_system_info()
    # Настраиваем логирование в файл с корректной кодировкой
    file_logger = setup_file_logger("test_output_sync.log")
    logger = logging.getLogger(__name__)
else:
    # Стандартная настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler("test_output_sync.txt", mode="w", encoding="utf-8")
        ]
    )
    logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

def get_test_parameters():
    """
    Получает параметры теста из переменных окружения.
    
    Returns:
        dict: Словарь с параметрами теста
    """
    # Значения по умолчанию
    default_params = {
        "image_path": "test_image.jpg",
        "budget": 10000,
        "style_preferences": "Деловой стиль, офисная одежда",
        "max_results": 2
    }
    
    # Получаем параметры из переменных окружения
    params = {}
    
    # Проверяем наличие переменных окружения с префиксом TEST_
    for key, default_value in default_params.items():
        env_key = f"TEST_{key.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            # Преобразуем значение в нужный тип
            if isinstance(default_value, int):
                try:
                    params[key] = int(env_value)
                except ValueError:
                    logger.warning(f"Не удалось преобразовать значение '{env_value}' для параметра '{key}' в целое число. Используем значение по умолчанию: {default_value}")
                    params[key] = default_value
            else:
                params[key] = env_value
        else:
            params[key] = default_value
    
    # Получаем имя конфигурации
    params["name"] = os.getenv("TEST_NAME", "default")
    
    return params

def save_to_file(data, filename):
    """
    Безопасно сохраняет данные в файл с обработкой ошибок кодировки.
    
    Args:
        data: Данные для сохранения (строка или объект, который можно сериализовать в JSON)
        filename (str): Имя файла для сохранения
    
    Returns:
        bool: True, если сохранение успешно, иначе False
    """
    try:
        # Если данные не являются строкой, преобразуем их в JSON
        if not isinstance(data, str):
            data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        
        # Используем модуль encoding_utils, если доступен
        if ENCODING_UTILS_ENABLED:
            return safe_write(filename, data)
        else:
            # Стандартное сохранение с обработкой ошибок
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(data)
                return True
            except UnicodeEncodeError:
                # Пробуем с другой кодировкой
                with open(filename, 'w', encoding='cp1251') as f:
                    f.write(data)
                return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {filename}: {e}")
        return False

def test_wildberries_sync():
    """
    Тестирование синхронного метода find_similar_products_wildberries.
    """
    # Получаем API ключи из переменных окружения
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        logger.error("Не найден API ключ OpenRouter. Установите переменную окружения OPENROUTER_API_KEY.")
        print("Ошибка: Не найден API ключ OpenRouter. Установите переменную окружения OPENROUTER_API_KEY.")
        return 1
    
    # Получаем параметры теста
    test_params = get_test_parameters()
    logger.info(f"Параметры теста: {json.dumps(test_params, ensure_ascii=False)}")
    
    # Формируем имя файла для сохранения результатов
    config_name = test_params.get("name", "default")
    result_filename = f"test_assistant_wildberries_sync_{config_name}_result.txt"
    image_analysis_filename = f"image_analysis_test_image_sync.txt"
    recommendations_filename = f"recommendations_test_image_sync.txt"
    
    # Инициализируем класс ChatAssistant
    print("\nИнициализация ChatAssistant...")
    assistant = ChatAssistant(openrouter_api_key=openrouter_api_key, openai_api_key=openai_api_key)
    
    # Тестируем синхронный метод
    print("\nТест: Синхронный вариант поиска товаров...\n")
    
    # Засекаем время выполнения
    start_time = time.time()
    
    try:
        # Запускаем синхронный метод поиска товаров
        image_path = test_params.get("image_path", "test_image.jpg")
        budget = test_params.get("budget", 10000)
        style_preferences = test_params.get("style_preferences", "Деловой стиль")
        max_results = test_params.get("max_results", 3)
        
        results = assistant.find_similar_products_wildberries(
            image_path=image_path,
            budget=budget,
            style_preferences=style_preferences,
            max_results=max_results
        )
        
        # Измеряем время выполнения
        execution_time = time.time() - start_time
        logger.info(f"Время выполнения: {execution_time:.2f} секунд")
        
        # Логируем результаты для отладки
        logger.debug(f"Результаты поиска товаров: {json.dumps(results, ensure_ascii=False, default=str)}")
        
        # Безопасно получаем данные из результатов
        success = results.get('success', False)
        search_query = results.get('query', 'Не указан')
        found_products = results.get('products', [])
        image_analysis = results.get('image_analysis', '')
        recommendations = results.get('recommendations', '')
        error = results.get('error', None)
        
        # Выводим результаты
        print("\nРезультаты синхронного поиска товаров:")
        print("-" * 80)
        print(f"Поисковый запрос: {search_query}")
        print(f"Количество найденных товаров: {len(found_products)}")
        
        if image_analysis:
            print("\nАнализ изображения:")
            print(image_analysis)
            # Сохраняем анализ изображения в отдельный файл
            save_to_file(image_analysis, image_analysis_filename)
        
        if found_products:
            print("\nНайденные товары:\n")
            for i, product in enumerate(found_products, 1):
                name = product.get('name', 'Без названия')
                brand = product.get('brand', 'Без бренда')
                price = product.get('price', 'Цена не указана')
                rating = product.get('rating', 'Нет рейтинга')
                url = product.get('url', '')
                
                print(f"{i}. {name} ({brand})")
                print(f"   Цена: {price} руб.")
                print(f"   Рейтинг: {rating}")
                print(f"   URL: {url}")
                print()
        
        if recommendations:
            print("Рекомендации:")
            print(recommendations)
            # Сохраняем рекомендации в отдельный файл
            save_to_file(recommendations, recommendations_filename)
        
        print("-" * 80)
        
        # Сохраняем результаты в файлы
        result_data = {
            "success": success,
            "query": search_query,
            "products": found_products,
            "image_analysis": image_analysis,
            "recommendations": recommendations,
            "error": error
        }
        
        # Сохраняем полные результаты
        save_to_file(result_data, "test_sync_results_full.json")
        
        # Сохраняем только найденные товары
        save_to_file(found_products, "products_found_sync.json")
        
        # Формируем текстовый отчет
        report = [
            f"Тест: test_assistant_wildberries_sync.py",
            f"Конфигурация: {config_name}",
            f"Параметры: {json.dumps(test_params, ensure_ascii=False, indent=2)}",
            f"Запущен: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Код возврата: {0}",
            f"Время выполнения: {execution_time:.2f} с",
            "",
            "STDOUT:",
            "Инициализация ChatAssistant...",
            "",
            "Тест: Синхронный вариант поиска товаров...",
            "",
            "Результаты синхронного поиска товаров:",
            "-" * 80,
            f"Поисковый запрос: {search_query}",
            f"Количество найденных товаров: {len(found_products)}",
            "",
            "Анализ изображения:" if image_analysis else "",
            image_analysis if image_analysis else "",
            "",
            "Найденные товары:" if found_products else "",
        ]
        
        for i, product in enumerate(found_products, 1):
            name = product.get('name', 'Без названия')
            brand = product.get('brand', 'Без бренда')
            price = product.get('price', 'Цена не указана')
            rating = product.get('rating', 'Нет рейтинга')
            url = product.get('url', '')
            
            report.extend([
                f"{i}. {name} ({brand})",
                f"   Цена: {price} руб.",
                f"   Рейтинг: {rating}",
                f"   URL: {url}",
                ""
            ])
        
        if recommendations:
            report.extend([
                "Рекомендации:",
                recommendations,
                ""
            ])
        
        # Сохраняем отчет в файл
        save_to_file("\n".join(report), result_filename)
        
        logger.info("Тестирование успешно завершено!")
        print("\nТестирование успешно завершено!")
        return 0
    
    except Exception as e:
        logger.exception(f"Ошибка при работе с ассистентом: {str(e)}")
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(test_wildberries_sync()) 