#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки потоковой генерации ответов и контроля лимитов токенов.
"""

import os
import logging
import sys
import asyncio
from dotenv import load_dotenv
from assistant import ChatAssistant
import json
import time

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

async def test_streaming_async():
    """
    Тестирование потоковой генерации ответов.
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
        
        # Тест 1: Потоковая генерация ответа
        print("\nТест 1: Потоковая генерация ответа...")
        user_id = "test_user_stream"
        role = "стилист"
        test_query = "Подбери мне пять аксессуаров для летнего отдыха на море. Опиши каждый аксессуар подробно в 2-3 предложениях."
        
        print("\nОтвет от ассистента (потоковый режим):")
        print("-" * 80)
        
        # Сначала выводим запрос пользователя
        print(f"\nПользователь: {test_query}")
        print("\nАссистент: ", end="", flush=True)
        
        # Замеряем время генерации
        start_time = time.time()
        full_response = ""
        
        async for chunk in assistant.generate_response_stream_async(
            user_id=user_id,
            role=role,
            user_input=test_query
        ):
            full_response += chunk
            print(chunk, end="", flush=True)
            await asyncio.sleep(0.01)  # Небольшая задержка для имитации постепенного появления текста
        
        generation_time = time.time() - start_time
        print(f"\n\nВремя генерации: {generation_time:.2f} сек.")
        print("-" * 80)
        
        # Тест 2: Установка лимитов токенов
        print("\nТест 2: Установка лимитов токенов...")
        await assistant.set_token_limit_async(daily_limit=5000, total_limit=10000)
        
        limits = await assistant.check_token_limits_async()
        print(json.dumps(limits, indent=2, ensure_ascii=False))
        
        # Тест 3: Экспорт статистики использования API
        print("\nТест 3: Экспорт статистики использования API...")
        stats_json = await assistant.export_usage_stats_async(format="json")
        print(stats_json[:200] + "...")  # Выводим только часть статистики
        
        stats_csv = await assistant.export_usage_stats_async(format="csv")
        print("\nСтатистика в формате CSV:")
        print(stats_csv)
        
        # Тест 4: Экспорт статистики в файл
        print("\nТест 4: Экспорт статистики в файл...")
        result = await assistant.export_usage_stats_async(format="json", filename="usage_stats.json")
        print(result)
        
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

def test_streaming_sync():
    """
    Синхронное тестирование потоковой генерации ответов.
    """
    # Получаем API ключи из переменных окружения
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
        
        # Тест потоковой генерации в синхронном режиме
        print("\nТест потоковой генерации (синхронно)...")
        user_id = "test_user_sync"
        role = "стилист"
        test_query = "Какие 3 базовые вещи нужны для создания капсульного гардероба?"
        
        print("\nОтвет от ассистента (синхронный потоковый режим):")
        print("-" * 80)
        
        # Вывод запроса пользователя
        print(f"\nПользователь: {test_query}")
        print("\nАссистент: ", end="", flush=True)
        
        # Функция обратного вызова для обработки частей ответа
        def process_chunk(chunk):
            # В реальном приложении здесь может быть логика обработки частей ответа
            # Например, отправка через WebSocket клиенту
            pass
        
        # Замеряем время генерации
        start_time = time.time()
        
        # Используем генератор для получения частей ответа
        for chunk in assistant.generate_response_stream(
            user_id=user_id,
            role=role,
            user_input=test_query,
            callback=process_chunk
        ):
            print(chunk, end="", flush=True)
            time.sleep(0.01)  # Небольшая задержка для имитации постепенного появления текста
        
        generation_time = time.time() - start_time
        print(f"\n\nВремя генерации: {generation_time:.2f} сек.")
        print("-" * 80)
        
        # Проверяем лимиты токенов
        print("\nПроверка лимитов токенов...")
        limits = assistant.check_token_limits()
        print(json.dumps(limits, indent=2, ensure_ascii=False))
        
        print("\nТестирование успешно завершено!")
        return 0
    
    except Exception as e:
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1

def main():
    """
    Точка входа. Выбор между синхронным и асинхронным тестом.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        return test_streaming_sync()
    else:
        return asyncio.run(test_streaming_async())

if __name__ == '__main__':
    sys.exit(main()) 