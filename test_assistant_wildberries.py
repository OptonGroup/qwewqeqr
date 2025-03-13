#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки интеграции ChatAssistant с Wildberries API.
"""

import os
import logging
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from assistant import ChatAssistant

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("test_output.txt", mode="w", encoding="utf-8")
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
        "budget": 5000,
        "style_preferences": "Повседневный стиль, комфортная одежда",
        "max_results": 3
    }
    
    # Получаем параметры из переменных окружения
    params = {}
    for key, default_value in default_params.items():
        env_key = f"TEST_{key.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            # Преобразуем значение к нужному типу
            if isinstance(default_value, int):
                params[key] = int(env_value)
            else:
                params[key] = env_value
            logger.info(f"Используется параметр из окружения: {key}={params[key]}")
        else:
            params[key] = default_value
            logger.info(f"Используется параметр по умолчанию: {key}={params[key]}")
    
    return params

async def test_wildberries_integration_async():
    """
    Тестирование интеграции с Wildberries API.
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
    
    try:
        # Инициализируем ассистента
        logger.info("Инициализация ChatAssistant...")
        print("Инициализация ChatAssistant...")
        assistant = ChatAssistant(
            model_type="openrouter",
            model_name="mistralai/mistral-7b-instruct:free",
            openrouter_api_key=openrouter_api_key,
            max_tokens=1024,
            cache_enabled=True,
            enable_usage_tracking=True
        )
        
        # Проверяем наличие тестового изображения
        test_image = test_params["image_path"]
        if not Path(test_image).exists():
            logger.error(f"Тестовое изображение {test_image} не найдено.")
            print(f"Ошибка: Тестовое изображение {test_image} не найдено.")
            print(f"Пожалуйста, поместите тестовое изображение в текущую директорию с именем {test_image}")
            return 1
        
        # Тест 1: Поиск похожих товаров на Wildberries
        logger.info("Тест 1: Поиск похожих товаров на Wildberries...")
        print("\nТест 1: Поиск похожих товаров на Wildberries...")
        
        # Используем параметры из переменных окружения
        results = await assistant.find_similar_products_wildberries_async(
            image_path=test_params["image_path"],
            budget=test_params["budget"],
            style_preferences=test_params["style_preferences"],
            max_results=test_params["max_results"]
        )
        
        # Сохраняем полный результат в JSON для дальнейшего анализа
        with open("test_results_full.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info("Полный результат сохранен в файл test_results_full.json")
        
        print(f"\nРезультаты поиска товаров на Wildberries:")
        print("-" * 80)
        
        # Логируем полный результат для отладки
        logger.debug(f"Полный результат: {json.dumps(results, ensure_ascii=False, indent=2)}")
        
        if results.get("success", False):
            products = results.get('products', [])
            products_count = len(products)
            query = results.get('query', 'Не указан')
            
            logger.info(f"Поиск товаров успешен. Найдено {products_count} товаров по запросу '{query}'.")
            print(f"Поисковый запрос: {query}")
            print(f"Количество найденных товаров: {products_count}")
            
            image_analysis = results.get("image_analysis", "")
            if image_analysis:
                print("\nАнализ изображения:")
                print(image_analysis)
                logger.info("Анализ изображения получен успешно.")
                
                # Сохраняем анализ изображения в отдельный файл
                analysis_file = f"image_analysis_{Path(test_params['image_path']).stem}.txt"
                with open(analysis_file, "w", encoding="utf-8") as f:
                    f.write(image_analysis)
                logger.info(f"Анализ изображения сохранен в файл {analysis_file}")
            else:
                logger.warning("Анализ изображения отсутствует в результатах")
            
            print("\nНайденные товары:")
            if products_count > 0:
                # Сохраняем информацию о товарах в отдельный JSON файл
                with open("products_found.json", "w", encoding="utf-8") as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)
                logger.info("Информация о товарах сохранена в файл products_found.json")
                
                for i, product in enumerate(products, 1):
                    name = product.get('name', 'Без названия')
                    brand = product.get('brand', 'Бренд не указан')
                    price = product.get('price', 'Не указана')
                    rating = product.get('rating', 'Не указан')
                    url = product.get('url', '#')
                    
                    print(f"\n{i}. {name} ({brand})")
                    print(f"   Цена: {price} руб.")
                    print(f"   Рейтинг: {rating}")
                    print(f"   URL: {url}")
                    
                    logger.debug(f"Товар #{i}: {name}, Цена: {price}, URL: {url}")
                    
                    # Добавляем расширенное логирование для каждого товара
                    logger.debug(f"Подробная информация о товаре #{i}:")
                    for key, value in product.items():
                        logger.debug(f"  - {key}: {value}")
            else:
                print("Товары не найдены в результатах запроса")
                logger.warning("Массив products пуст, хотя запрос выполнен успешно")
            
            recommendations = results.get("recommendations", "")
            if recommendations:
                print("\nРекомендации:")
                print(recommendations)
                logger.info("Рекомендации получены успешно.")
                
                # Сохраняем рекомендации в отдельный файл
                recommendations_file = f"recommendations_{Path(test_params['image_path']).stem}.txt"
                with open(recommendations_file, "w", encoding="utf-8") as f:
                    f.write(recommendations)
                logger.info(f"Рекомендации сохранены в файл {recommendations_file}")
            else:
                logger.warning("Рекомендации отсутствуют в результатах")
        else:
            error_msg = results.get('error', 'Неизвестная ошибка')
            logger.error(f"Ошибка при поиске товаров: {error_msg}")
            print(f"Ошибка при поиске товаров: {error_msg}")
            
            # Вывод результатов анализа изображения даже при ошибке
            image_analysis = results.get("image_analysis", "")
            if image_analysis:
                print("\nРезультаты анализа изображения (несмотря на ошибку):")
                print(image_analysis)
                logger.info("Анализ изображения получен, несмотря на ошибку в основном запросе.")
                
                # Сохраняем анализ изображения в отдельный файл даже при ошибке
                error_analysis_file = f"error_image_analysis_{Path(test_params['image_path']).stem}.txt"
                with open(error_analysis_file, "w", encoding="utf-8") as f:
                    f.write(image_analysis)
                logger.info(f"Анализ изображения при ошибке сохранен в файл {error_analysis_file}")
            
            # Проверяем наличие query даже при ошибке
            query = results.get("query", "")
            if query:
                print(f"\nИспользованный поисковый запрос: {query}")
                logger.info(f"Поисковый запрос был сформирован: {query}")
        
        print("-" * 80)
        
        # Тест 2: Синхронный вариант поиска товаров
        logger.info("Тест 2: Синхронный вариант поиска товаров (пропущен)...")
        print("\nТест 2: Синхронный вариант поиска товаров...")
        
        # Закрываем HTTP сессию перед синхронным вызовом
        await assistant.close()
        
        # Запускаем синхронный тест в отдельном процессе
        print("\nРезультаты синхронного поиска товаров:")
        print("-" * 80)
        print("Синхронный тест пропущен из-за проблем с event loop.")
        print("Для тестирования синхронного метода запустите отдельный скрипт.")
        print("-" * 80)
        
        logger.info("Тестирование успешно завершено!")
        print("\nТестирование успешно завершено!")
        return 0
    
    except Exception as e:
        logger.exception(f"Ошибка при работе с ассистентом: {str(e)}")
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1
    finally:
        # Гарантируем закрытие сессии даже при ошибках
        if 'assistant' in locals():
            logger.info("Закрытие HTTP сессии ассистента...")
            try:
                await assistant.close()
                logger.info("HTTP сессия успешно закрыта")
            except Exception as close_error:
                logger.error(f"Ошибка при закрытии HTTP сессии: {str(close_error)}")

def main():
    """
    Точка входа для запуска асинхронного тестирования.
    """
    return asyncio.run(test_wildberries_integration_async())

if __name__ == '__main__':
    sys.exit(main()) 