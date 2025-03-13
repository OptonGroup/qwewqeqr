#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модульный тест для проверки методов determine_user_needs в ChatAssistant.
"""

import os
import json
import sys
import logging
from dotenv import load_dotenv
from assistant import ChatAssistant, UserPreferences

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("test_determine_needs.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

def save_to_file(data, filename):
    """Сохраняет данные в файл."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            if isinstance(data, dict) or isinstance(data, list):
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                f.write(str(data))
        logger.info(f"Данные сохранены в файл: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {filename}: {e}")

def test_determine_needs():
    """Тестирует метод determine_user_needs для разных ролей."""
    # Получаем API ключи из переменных окружения
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not (openai_api_key or openrouter_api_key):
        logger.error("Не найдены API ключи. Установите переменные окружения OPENAI_API_KEY или OPENROUTER_API_KEY.")
        return 1
    
    # Тестовые запросы для разных ролей
    test_cases = [
        {
            "role": "нутрициолог",
            "user_input": "Я хочу составить план питания для похудения. У меня аллергия на орехи. Бюджет 2000 рублей в неделю."
        },
        {
            "role": "стилист", 
            "user_input": "Нужно подобрать осенний гардероб для работы в офисе, мой размер M, предпочитаю темные цвета."
        },
        {
            "role": "косметолог",
            "user_input": "У меня жирная кожа с акне, ищу органические средства для ухода."
        },
        {
            "role": "дизайнер",
            "user_input": "Хочу обновить гостиную в скандинавском стиле, площадь 20 кв.м., уже есть диван и журнальный столик."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        role = test_case["role"]
        user_input = test_case["user_input"]
        
        print(f"\n\nТест {i}: Определение потребностей пользователя для роли '{role}'\n")
        print(f"Запрос: {user_input}\n")
        
        try:
            # Создаем новый экземпляр ChatAssistant для каждого теста
            test_assistant = ChatAssistant(
                openrouter_api_key=openrouter_api_key, 
                openai_api_key=openai_api_key
            )
            
            # Вызываем метод определения потребностей
            result = test_assistant.determine_user_needs(
                user_id=f"test_user_{i}",
                role=role,
                user_input=user_input
            )
            
            # Проверяем успешность операции
            if result["success"]:
                # Получаем определенные потребности
                identified_needs = result["identified_needs"]
                clarifying_questions = result["clarifying_questions"]
                preferences = result["preferences"]
                
                # Выводим результаты
                print(f"Роль: {role}")
                print("Определенные потребности:")
                print(json.dumps(identified_needs, ensure_ascii=False, indent=2))
                
                print("\nУточняющие вопросы:")
                for q in clarifying_questions:
                    print(f"- {q}")
                
                print("\nОбновленные предпочтения:")
                preferences_dict = preferences.get_role_specific_preferences()
                print(json.dumps(preferences_dict, ensure_ascii=False, indent=2))
                
                # Сохраняем результаты в файл
                save_to_file(
                    {
                        "success": result["success"],
                        "identified_needs": result["identified_needs"],
                        "clarifying_questions": result["clarifying_questions"],
                        "preferences_updated": result["preferences_updated"],
                        "preferences": preferences_dict
                    },
                    f"test_determine_needs_{role}_{i}.json"
                )
            else:
                print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста {i}: {str(e)}")
            import traceback
            logger.error(f"Трассировка стека: {traceback.format_exc()}")
            print(f"Произошла ошибка: {str(e)}")

def main():
    """Основная функция для запуска тестов."""
    print("Запуск тестов метода determine_user_needs...")
    
    # Запускаем тест метода determine_user_needs
    test_determine_needs()
    
    print("\nТесты завершены.")

if __name__ == "__main__":
    main() 