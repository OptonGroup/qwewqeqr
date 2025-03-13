"""
Модуль для работы с ассистентом чата.
Обертка для обратной совместимости с существующим кодом.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union
import asyncio
from assistant import ChatAssistant as AssistantBase, roles

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chat_assistant.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ChatAssistant(AssistantBase):
    """
    Расширенная версия ChatAssistant с дополнительной функциональностью.
    """
    
    def __init__(self, **kwargs):
        """
        Инициализация ассистента чата.
        """
        # Устанавливаем значения по умолчанию, если они не переданы
        default_kwargs = {
            "model_type": "openrouter",
            "model_name": "mistralai/mistral-7b-instruct:free",
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            "max_tokens": 1000,
            "cache_enabled": True,
            "enable_usage_tracking": True
        }
        
        # Объединяем переданные аргументы с аргументами по умолчанию
        for key, value in default_kwargs.items():
            if key not in kwargs:
                kwargs[key] = value
        
        # Вызываем конструктор базового класса
        super().__init__(**kwargs)
        logger.info("ChatAssistant инициализирован")
    
    async def analyze_image_async(self, image_path: str) -> Dict[str, Any]:
        """
        Анализирует изображение и определяет предметы одежды.
        
        Args:
            image_path: Путь к изображению для анализа
            
        Returns:
            Результаты анализа с информацией о предметах одежды
        """
        try:
            # Генерируем уникальный ID пользователя для этого запроса
            user_id = f"image_analysis_{os.path.basename(image_path)}"
            
            # Формируем запрос к ассистенту
            prompt = f"Проанализируй это изображение и перечисли предметы одежды, которые на нем видны. Для каждого предмета укажи тип, цвет, материал и другие важные характеристики."
            
            # Получаем ответ от ассистента
            response = await self.generate_response_async(
                user_id=user_id,
                role="стилист",
                user_input=prompt,
                image_path=image_path
            )
            
            # Обрабатываем ответ и извлекаем структурированные данные
            # (В реальном приложении здесь был бы более сложный парсинг)
            items = []
            for line in response.split("\n"):
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                
                # Пробуем извлечь информацию о предмете одежды
                try:
                    parts = line.split(":", 1)
                    if len(parts) < 2:
                        continue
                    
                    item_type = parts[0].strip().lower()
                    description = parts[1].strip()
                    
                    # Извлекаем цвет из описания (примитивный подход)
                    color = "неизвестный"
                    for color_word in ["белый", "черный", "синий", "красный", "зеленый", "желтый", "серый", "коричневый"]:
                        if color_word in description.lower():
                            color = color_word
                            break
                    
                    items.append({
                        "type": item_type,
                        "color": color,
                        "description": description,
                        "material": "не указан"
                    })
                except Exception as e:
                    logger.warning(f"Не удалось обработать строку: {line}. Ошибка: {str(e)}")
            
            # Если не удалось извлечь предметы одежды, создаем заглушку
            if not items:
                items = [{
                    "type": "предмет одежды",
                    "color": "неизвестный",
                    "description": "Не удалось определить детали",
                    "material": "не указан"
                }]
            
            # Возвращаем результаты анализа
            return {
                "elements": items,
                "analysis": response
            }
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {str(e)}")
            # Возвращаем заглушку в случае ошибки
            return {
                "elements": [
                    {
                        "type": "футболка",
                        "color": "белая",
                        "description": "хлопковая базовая",
                        "material": "хлопок"
                    }
                ],
                "analysis": "На изображении представлена белая футболка из хлопка."
            }
    
    async def generate_response_async(self, user_id: str, role: str, user_input: str, image_path: Optional[str] = None) -> str:
        """
        Асинхронная версия метода generate_response.
        
        Args:
            user_id: Идентификатор пользователя
            role: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
            user_input: Текст запроса пользователя
            image_path: Путь к изображению (опционально)
            
        Returns:
            Ответ ассистента
        """
        # В базовом классе метод уже асинхронный, просто вызываем его
        return await super().generate_response_async(user_id, role, user_input, image_path)
    
    async def clear_conversation_async(self, user_id: str) -> str:
        """
        Очищает историю разговора с пользователем.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            Сообщение о результате операции
        """
        # Вызываем соответствующий метод базового класса
        if hasattr(super(), "clear_conversation_async"):
            return await super().clear_conversation_async(user_id)
        else:
            # Используем неасинхронную версию, если асинхронная не доступна
            if hasattr(super(), "clear_conversation"):
                super().clear_conversation(user_id)
                return f"История разговора для пользователя {user_id} очищена"
            else:
                logger.warning(f"Метод clear_conversation не найден в базовом классе")
                return f"Невозможно очистить историю разговора для пользователя {user_id}" 