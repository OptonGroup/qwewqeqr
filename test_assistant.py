#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки работы ChatAssistant.
"""

import os
from assistant import ChatAssistant, roles
import argparse
from dotenv import load_dotenv
import logging
import sys

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
    Основная функция для тестирования ChatAssistant в консоли.
    """
    parser = argparse.ArgumentParser(description='Тестирование ChatAssistant')
    parser.add_argument('--model', '-m', default='openrouter', choices=['openai', 'openrouter'],
                        help='Тип модели (openai или openrouter)')
    parser.add_argument('--model-name', '-n', default='mistralai/mistral-7b-instruct:free',
                        help='Название модели для использования')
    parser.add_argument('--role', '-r', default='стилист', choices=list(roles.keys()),
                        help='Роль ассистента')
    parser.add_argument('--tokens', '-t', type=int, default=2048,
                        help='Максимальное количество токенов в ответе')
    
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
            max_tokens=args.tokens
        )
        
        print(f"Инициализирован ChatAssistant с моделью {args.model_name} в роли '{args.role}'")
        print("Введите 'exit' или 'quit' для выхода")
        print("Введите 'clear' для очистки истории диалога")
        print("-" * 50)
        
        user_id = "test_user"  # Тестовый ID пользователя
        
        # Основной цикл диалога
        while True:
            user_input = input("\nВы: ")
            
            # Проверяем команды выхода
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Проверяем команду очистки
            if user_input.lower() == "clear":
                assistant.clear_conversation(user_id)
                print("История диалога очищена.")
                continue
            
            # Получаем ответ от ассистента
            print("\nАссистент думает...")
            response = assistant.generate_response(
                user_id=user_id,
                role=args.role,
                user_input=user_input
            )
            
            print(f"\nАссистент: {response}")
    
    except Exception as e:
        print(f"Ошибка при работе с ассистентом: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 