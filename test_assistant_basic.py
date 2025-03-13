#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Базовый тестовый скрипт для проверки работы ChatAssistant без интерактивного ввода.
"""

import os
import logging
import sys
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

def main():
    """
    Основная функция для базового тестирования ChatAssistant.
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
        print("\nПолучение ответа...")
        response = assistant.generate_response(
            user_id=user_id,
            role=role,
            user_input=test_query
        )
        
        print(f"\nОтвет ассистента:\n{response}")
        
        # Проверяем очистку истории
        print("\nОчистка истории диалога...")
        clear_result = assistant.clear_conversation(user_id)
        print(clear_result)
        
        print("\nТестирование успешно завершено!")
        return 0
    
    except Exception as e:
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 