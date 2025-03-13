#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки функций ChatAssistant по работе с изображениями.
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
        logging.StreamHandler(sys.stderr)
    ]
)

# Загрузка переменных окружения
load_dotenv()

async def test_image_processing_async():
    """
    Тестирование функций обработки изображений.
    """
    # Получаем API ключи из переменных окружения
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        print("Ошибка: Не найден API ключ OpenRouter. Установите переменную окружения OPENROUTER_API_KEY.")
        return 1
    
    try:
        # Инициализируем ассистента
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
        test_image = "test_image.jpg"
        if not Path(test_image).exists():
            print(f"Ошибка: Тестовое изображение {test_image} не найдено.")
            print("Пожалуйста, поместите тестовое изображение в текущую директорию с именем test_image.jpg")
            return 1
        
        # Тест 1: Базовый анализ изображения
        print("\nТест 1: Анализ изображения...")
        role = "стилист"
        
        image_analysis = await assistant.analyze_image_async(
            image_path=test_image,
            role=role
        )
        
        print(f"\nРезультат анализа изображения ({role}):")
        print("-" * 80)
        print(image_analysis)
        print("-" * 80)
        
        # Тест 2: Генерация ответа с учетом изображения
        print("\nТест 2: Генерация ответа с учетом изображения...")
        prompt = "Что мне носить с этой вещью? Предложи 3 варианта комплектов."
        
        response = await assistant.generate_response_with_image_async(
            prompt=prompt,
            image_path=test_image,
            role=role
        )
        
        print(f"\nОтвет ассистента:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
        # Тест 3: Поиск похожей одежды
        print("\nТест 3: Поиск похожей одежды...")
        
        similar_clothes = await assistant.find_similar_clothing_async(
            image_path=test_image,
            budget=5000,
            style_preferences="Повседневный стиль, комфортная одежда"
        )
        
        print(f"\nРезультат поиска похожей одежды:")
        print("-" * 80)
        print(similar_clothes)
        print("-" * 80)
        
        # Тест 4: Анализ изображения в роли дизайнера
        print("\nТест 4: Анализ изображения в роли дизайнера...")
        
        designer_analysis = await assistant.analyze_image_async(
            image_path=test_image,
            role="дизайнер"
        )
        
        print(f"\nРезультат анализа изображения (дизайнер):")
        print("-" * 80)
        print(designer_analysis)
        print("-" * 80)
        
        # Закрываем HTTP сессию
        await assistant.close()
        
        print("\nТестирование успешно завершено!")
        return 0
    
    except Exception as e:
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1
    finally:
        # Гарантируем закрытие сессии даже при ошибках
        if 'assistant' in locals():
            await assistant.close()

def main():
    """
    Точка входа для запуска асинхронного тестирования.
    """
    return asyncio.run(test_image_processing_async())

if __name__ == '__main__':
    sys.exit(main()) 