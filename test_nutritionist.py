#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки функциональности роли нутрициолога в ChatAssistant.
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
        logging.FileHandler("test_nutritionist.log", encoding="utf-8")
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
    """
    Тестирует метод determine_user_needs для роли нутрициолога.
    """
    # Получаем API ключи из переменных окружения
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not (openai_api_key or openrouter_api_key):
        logger.error("Не найдены API ключи. Установите переменные окружения OPENAI_API_KEY или OPENROUTER_API_KEY.")
        return 1
    
    # Инициализируем класс ChatAssistant
    print("\nИнициализация ChatAssistant для роли нутрициолога...")
    
    assistant = ChatAssistant(
        openrouter_api_key=openrouter_api_key, 
        openai_api_key=openai_api_key
    )
    
    # Тестовый запрос пользователя
    test_inputs = [
        "Я хочу составить план питания для похудения. У меня аллергия на орехи. Бюджет 2000 рублей в неделю.",
        "Мне нужно набрать мышечную массу. Я хожу в зал 3 раза в неделю. Мой вес 70 кг, рост 180 см.",
        "Помоги составить рацион для диабетика, который хочет поддерживать здоровый вес.",
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n\nТест {i}: Определение потребностей пользователя\n")
        print(f"Запрос: {user_input}\n")
        
        try:
            # Вызываем метод определения потребностей
            result = assistant.determine_user_needs(
                user_id=f"test_user_{i}",
                role="нутрициолог",
                user_input=user_input
            )
            
            # Проверяем успешность операции
            if result["success"]:
                # Получаем определенные потребности
                identified_needs = result["identified_needs"]
                clarifying_questions = result["clarifying_questions"]
                preferences = result["preferences"]
                
                # Выводим результаты
                print("Определенные потребности:")
                print(json.dumps(identified_needs, ensure_ascii=False, indent=2))
                
                print("\nУточняющие вопросы:")
                for q in clarifying_questions:
                    print(f"- {q}")
                
                print("\nОбновленные предпочтения:")
                preferences_dict = {
                    "user_id": preferences.user_id,
                    "role": preferences.role,
                    "budget": preferences.budget,
                    "dietary_goal": preferences.dietary_goal,
                    "dietary_restrictions": preferences.dietary_restrictions,
                    "weight": preferences.weight,
                    "height": preferences.height,
                    "activity_level": preferences.activity_level,
                    "allergies_food": preferences.allergies_food
                }
                print(json.dumps(preferences_dict, ensure_ascii=False, indent=2))
                
                # Сохраняем результаты в файл
                save_to_file(
                    result,
                    f"test_nutritionist_needs_{i}.json"
                )
            else:
                print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста {i}: {str(e)}")
            print(f"Произошла ошибка: {str(e)}")

def test_calculate_nutrition():
    """
    Тестирует метод calculate_nutrition для расчета питательной ценности набора продуктов.
    """
    # Получаем API ключи из переменных окружения
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not (openai_api_key or openrouter_api_key):
        logger.error("Не найдены API ключи. Установите переменные окружения OPENAI_API_KEY или OPENROUTER_API_KEY.")
        return 1
    
    # Инициализируем класс ChatAssistant
    print("\nИнициализация ChatAssistant для роли нутрициолога...")
    
    assistant = ChatAssistant(
        openrouter_api_key=openrouter_api_key, 
        openai_api_key=openai_api_key
    )
    
    # Тестовый набор продуктов
    products = [
        {"name": "Куриная грудка", "protein": 23.0, "fat": 1.5, "carbs": 0.0, "calories": 113.0, "fiber": 0.0, "sugar": 0.0},
        {"name": "Рис коричневый", "protein": 7.9, "fat": 2.7, "carbs": 76.2, "calories": 362.0, "fiber": 3.5, "sugar": 0.7},
        {"name": "Брокколи", "protein": 2.8, "fat": 0.4, "carbs": 6.6, "calories": 34.0, "fiber": 2.6, "sugar": 1.7},
        {"name": "Оливковое масло", "protein": 0.0, "fat": 100.0, "carbs": 0.0, "calories": 884.0, "fiber": 0.0, "sugar": 0.0},
        {"name": "Яблоко", "protein": 0.3, "fat": 0.4, "carbs": 14.0, "calories": 52.0, "fiber": 2.4, "sugar": 10.3}
    ]
    
    quantities = [150, 100, 200, 15, 150]  # граммы
    
    print("\nТест: Расчет питательной ценности продуктов\n")
    print("Набор продуктов:")
    for i, (product, quantity) in enumerate(zip(products, quantities), 1):
        print(f"{i}. {product['name']} - {quantity} г")
    
    try:
        # Вызываем метод расчета питательной ценности
        result = assistant.calculate_nutrition(products, quantities)
        
        # Проверяем успешность операции
        if result["success"]:
            # Получаем результаты расчета
            total_calories = result["total_calories"]
            total_protein = result["total_protein"]
            total_fat = result["total_fat"]
            total_carbs = result["total_carbs"]
            total_fiber = result.get("total_fiber", 0)
            pfc_ratio = result["pfc_ratio"]
            recommendations = result["recommendations"]
            
            # Выводим результаты
            print("\nРезультаты расчета:")
            print(f"Общая калорийность: {total_calories} ккал")
            print(f"Белки: {total_protein} г ({pfc_ratio[0]}%)")
            print(f"Жиры: {total_fat} г ({pfc_ratio[1]}%)")
            print(f"Углеводы: {total_carbs} г ({pfc_ratio[2]}%)")
            print(f"Клетчатка: {total_fiber} г")
            
            print("\nРекомендации по оптимизации рациона:")
            print(recommendations)
            
            # Сохраняем результаты в файл
            save_to_file(
                result,
                "test_nutritionist_calculation.json"
            )
        else:
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
    
    except Exception as e:
        logger.error(f"Ошибка при расчете питательной ценности: {str(e)}")
        print(f"Произошла ошибка: {str(e)}")

def main():
    """Основная функция для запуска тестов."""
    print("Запуск тестов функциональности роли нутрициолога...")
    
    # Запускаем тест метода determine_user_needs
    test_determine_needs()
    
    # Запускаем тест метода calculate_nutrition
    test_calculate_nutrition()
    
    print("\nТесты завершены.")

if __name__ == "__main__":
    main() 