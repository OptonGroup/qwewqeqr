#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Расширенный тестовый скрипт для проверки новых функций ChatAssistant.
"""

import os
import logging
import sys
import asyncio
from dotenv import load_dotenv
from assistant import ChatAssistant
import json

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

async def run_test_async():
    """
    Асинхронная функция для тестирования расширенных функций ChatAssistant.
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
        
        # Тест 1: Валидация API ключей
        print("\nТест 1: Валидация API ключей...")
        is_valid = await assistant.validate_api_keys_async()
        print(f"API ключи валидны: {is_valid}")
        
        # Тест 2: Генерация ответа
        print("\nТест 2: Генерация ответа...")
        user_id = "test_user"
        role = "стилист"
        test_query = "Помоги мне подобрать летний гардероб для поездки на море. Бюджет 15000 рублей."
        
        response = await assistant.generate_response_async(
            user_id=user_id,
            role=role,
            user_input=test_query
        )
        
        print(f"\nОтвет ассистента:\n{response[:200]}...")  # Выводим только начало ответа
        
        # Тест 3: Получение статистики использования API
        print("\nТест 3: Получение статистики использования API...")
        stats = await assistant.get_usage_stats_async()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # Тест 4: Переключение модели
        print("\nТест 4: Переключение модели...")
        switch_result = await assistant.switch_model_async(
            model_type="openrouter",
            model_name="anthropic/claude-3-haiku:free"
        )
        print(f"Результат переключения модели: {switch_result}")
        
        # Тест 5: Генерация ответа с новой моделью
        if switch_result:
            print("\nТест 5: Генерация ответа с новой моделью...")
            response = await assistant.generate_response_async(
                user_id=user_id,
                role=role,
                user_input="Какие аксессуары подойдут к летнему гардеробу?"
            )
            
            print(f"\nОтвет ассистента (новая модель):\n{response[:200]}...")  # Выводим только начало ответа
            
            # Тест 6: Обновленная статистика использования API
            print("\nТест 6: Обновленная статистика использования API...")
            stats = await assistant.get_usage_stats_async()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # Тест 7: Сброс статистики использования API
        print("\nТест 7: Сброс статистики использования API...")
        await assistant.reset_usage_stats_async()
        stats = await assistant.get_usage_stats_async()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
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
    Точка входа для запуска асинхронной функции.
    """
    return asyncio.run(run_test_async())

if __name__ == '__main__':
    sys.exit(main()) 