#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Асинхронный тестовый скрипт для проверки работы ChatAssistant.
"""

import os
import asyncio
from assistant import ChatAssistant, roles
import argparse
from dotenv import load_dotenv
import logging
import sys
import aioconsole  # Для асинхронного ввода

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

async def main_async():
    """
    Основная асинхронная функция для тестирования ChatAssistant.
    """
    parser = argparse.ArgumentParser(description='Асинхронное тестирование ChatAssistant')
    parser.add_argument('--model', '-m', default='openrouter', choices=['openai', 'openrouter'],
                        help='Тип модели (openai или openrouter)')
    parser.add_argument('--model-name', '-n', default='mistralai/mistral-7b-instruct:free',
                        help='Название модели для использования')
    parser.add_argument('--role', '-r', default='стилист', choices=list(roles.keys()),
                        help='Роль ассистента')
    parser.add_argument('--tokens', '-t', type=int, default=2048,
                        help='Максимальное количество токенов в ответе')
    parser.add_argument('--cache', '-c', action='store_true',
                        help='Включить кеширование ответов')
    
    args = parser.parse_args()
    
    # Получаем API ключи из переменных окружения
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Проверяем наличие нужного ключа
    if args.model == 'openai' and not openai_api_key:
        print("Ошибка: Не найден API ключ OpenAI. Установите переменную окружения OPENAI_API_KEY.")
        return 1
    elif args.model == 'openrouter' and not openrouter_api_key:
        print("Ошибка: Не найден API ключ OpenRouter. Установите переменную окружения OPENROUTER_API_KEY.")
        return 1
    
    try:
        # Инициализируем ассистента
        assistant = ChatAssistant(
            model_type=args.model,
            model_name=args.model_name,
            openai_api_key=openai_api_key,
            openrouter_api_key=openrouter_api_key,
            max_tokens=args.tokens,
            cache_enabled=args.cache
        )
        
        print(f"Инициализирован ChatAssistant с моделью {args.model_name} в роли '{args.role}'")
        print("Введите 'exit' или 'quit' для выхода")
        print("Введите 'clear' для очистки истории диалога")
        print("-" * 50)
        
        user_id = "test_user"  # Тестовый ID пользователя
        
        # Основной цикл диалога
        while True:
            user_input = await aioconsole.ainput("\nВы: ")
            
            # Проверяем команды выхода
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Проверяем команду очистки
            if user_input.lower() == "clear":
                result = await assistant.clear_conversation_async(user_id)
                print(result)
                continue
            
            # Получаем ответ от ассистента
            print("\nАссистент думает...")
            response = await assistant.generate_response_async(
                user_id=user_id,
                role=args.role,
                user_input=user_input
            )
            
            print(f"\nАссистент: {response}")
        
        # Закрываем сессию ассистента
        await assistant.close()
    
    except Exception as e:
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1
    
    return 0

def main():
    """
    Точка входа для запуска асинхронной функции.
    """
    return asyncio.run(main_async())

if __name__ == '__main__':
    sys.exit(main()) 