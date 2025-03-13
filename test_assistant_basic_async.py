#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Асинхронный базовый тестовый скрипт для проверки работы ChatAssistant без интерактивного ввода.
"""

import os
import logging
import sys
import asyncio
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

async def run_test_async():
    """
    Асинхронная функция для базового тестирования ChatAssistant.
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
            cache_enabled=True
        )
        
        user_id = "test_user"
        role = "стилист"
        
        # Простой тестовый запрос
        print("\nОтправка тестового запроса...")
        test_query = "Помоги мне подобрать летний гардероб для поездки на море. Бюджет 15000 рублей."
        
        # Получаем ответ от ассистента
        print("\nПолучение ответа (асинхронно)...")
        response = await assistant.generate_response_async(
            user_id=user_id,
            role=role,
            user_input=test_query
        )
        
        print(f"\nОтвет ассистента:\n{response}")
        
        # Проверяем очистку истории
        print("\nОчистка истории диалога (асинхронно)...")
        clear_result = await assistant.clear_conversation_async(user_id)
        print(clear_result)
        
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