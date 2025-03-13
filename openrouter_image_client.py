#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenRouter Image Processing Client

This script demonstrates how to send image data to OpenRouter API
and process the response.
"""

import os
import base64
import requests
from pathlib import Path
import argparse
from typing import Optional, Dict, Any, Union
import json
import logging
from dotenv import load_dotenv
from PIL import Image
import io
import aiohttp
import asyncio
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OpenRouterClient:
    """Client for interacting with OpenRouter API to process images."""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If None, will try to load from OPENROUTER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set it as an argument or as OPENROUTER_API_KEY environment variable.")
        
        # Создаем асинхронную сессию для API запросов
        self._session = None
    
    @property
    async def session(self):
        """Lazy initialization of aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def encode_image(self, image_path: Union[str, Path]) -> str:
        """
        Encode an image file to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Открываем изображение с помощью PIL
            img = Image.open(image_path)
            
            # Конвертируем в RGB, если это не RGB (например, RGBA)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Сохраняем в буфер в формате JPEG
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)
            
            # Кодируем в base64
            return base64.b64encode(buffer.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            raise
    
    def process_image(
        self, 
        image_path: Union[str, Path], 
        model: str = "anthropic/claude-3-haiku-20240307",
        prompt: str = "Опиши подробно, что ты видишь на этом изображении. Ответ должен быть на русском языке.",
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Send an image to OpenRouter and get the response.
        
        Args:
            image_path: Path to the image file
            model: Model identifier to use
            prompt: Text prompt to accompany the image
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            API response as a dictionary
        """
        try:
            encoded_image = self.encode_image(image_path)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": max_tokens
            }
            
            logger.info(f"Sending request to OpenRouter API using model: {model}")
            logger.info(f"Payload structure: {json.dumps(payload, default=str, ensure_ascii=False)[:500]}...")
            
            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = ""
                try:
                    error_json = response.json()
                    error_detail = f"\nError details: {json.dumps(error_json, indent=2, ensure_ascii=False)}"
                except:
                    error_detail = f"\nResponse text: {response.text}"
                
                logger.error(f"API Error: {response.status_code}{error_detail}")
                response.raise_for_status()
            
            # Добавляем подробное логирование ответа
            response_json = response.json()
            logger.info(f"Received response from OpenRouter API: {json.dumps(response_json, default=str, ensure_ascii=False)[:500]}...")
            
            # Проверяем структуру ответа
            if 'choices' not in response_json or len(response_json['choices']) == 0:
                logger.error(f"Unexpected response structure: {json.dumps(response_json, default=str, ensure_ascii=False)}")
                return {"error": "Unexpected response structure", "raw_response": response_json}
            
            if 'message' not in response_json['choices'][0] or 'content' not in response_json['choices'][0]['message']:
                logger.error(f"Missing content in response: {json.dumps(response_json['choices'][0], default=str, ensure_ascii=False)}")
                return {"error": "Missing content in response", "raw_response": response_json}
            
            return response_json
            
        except FileNotFoundError as e:
            logger.error(f"File error: {str(e)}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def generate_response(
        self, 
        prompt: str,
        image_path: Union[str, Path], 
        model: str = "anthropic/claude-3-haiku",
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a response based on a prompt and an image.
        
        Args:
            prompt: Text prompt to accompany the image
            image_path: Path to the image file
            model: Model identifier to use
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            response = self.process_image(
                image_path=image_path,
                model=model,
                prompt=prompt,
                max_tokens=max_tokens
            )
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                return content
            else:
                return "Ошибка: В ответе API отсутствует ожидаемое содержимое."
                
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            return f"Ошибка при генерации ответа: {str(e)}"

    async def analyze_image(self, image_base64: str, prompt: str = "Опиши подробно одежду на этом изображении.") -> Dict[str, Any]:
        """
        Асинхронно анализирует изображение через OpenRouter API.
        
        Args:
            image_base64: Изображение в формате base64
            prompt: Запрос для анализа изображения
            
        Returns:
            Словарь с результатами анализа
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Изменяем запрос, делая его еще более структурированным для лучшего распознавания одежды
            prompt = """Проанализируй всю одежду на изображении и опиши каждый предмет в строго структурированном формате.

Обязательно проанализируй ВСЕ видимые элементы одежды, включая:
- Верхнюю часть (рубашки, блузки, футболки, пиджаки, жакеты, свитера и т.д.)
- Нижнюю часть (брюки, джинсы, юбки, шорты и т.д.)
- Обувь (туфли, кроссовки, ботинки и т.д.)
- Аксессуары (если видны)

Даже если какая-то часть одежды видна не полностью или частично скрыта, всё равно опиши её.

Сначала ЯВНО УКАЖИ, для какого пола предназначена эта одежда: "ПОЛ: мужской", "ПОЛ: женский" или "ПОЛ: унисекс".

Затем перечисли все видимые предметы одежды в виде нумерованного списка одной строкой для каждого предмета:
1. [Тип предмета] [Цвет] [Краткие характеристики]
2. [Тип предмета] [Цвет] [Краткие характеристики]
...

Затем, для каждого предмета создай отдельный раздел со следующей структурой:

[ТИП_ПРЕДМЕТА]:
- Цвет: [цвет]
- Пол: [мужской/женский/унисекс]
- Материал: [материал] (если виден)
- Описание: [короткое описание особенностей]

ВАЖНО:
1. Не добавляй в описание конкретного предмета информацию о других предметах
2. Общие наблюдения об образе выдели в отдельный раздел "ОБЩЕЕ"
3. Следуй строго указанной структуре
4. Если какая-то информация неизвестна - укажи "неизвестно"
5. Даже если нижняя часть одежды (брюки, юбка) видны не полностью, обязательно укажи их
6. Для каждого предмета обязательно определи, для какого пола он предназначен
"""

            payload = {
                "model": "anthropic/claude-3-haiku",  # Используем модель с поддержкой изображений без указания даты
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 2000
            }
            
            logger.info("Отправка запроса к OpenRouter API для анализа изображения")
            session = await self.session
            
            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API Error: {response.status} - {error_text}")
                    raise Exception(f"Ошибка API: {response.status}, {error_text}")
                
                response_data = await response.json()
                
                # Добавляем полное логирование ответа для отладки
                logger.info(f"Полный ответ от OpenRouter API: {json.dumps(response_data, ensure_ascii=False)}")
                
                # Более гибкая проверка структуры ответа
                if 'choices' not in response_data or len(response_data['choices']) == 0:
                    logger.error(f"Неожиданная структура ответа: {json.dumps(response_data, ensure_ascii=False)}")
                    
                    # Проверяем другие возможные структуры ответа
                    if 'data' in response_data and 'content' in response_data['data']:
                        analysis_text = response_data['data']['content']
                    elif 'message' in response_data and 'content' in response_data['message']:
                        analysis_text = response_data['message']['content']
                    elif 'response' in response_data and isinstance(response_data['response'], str):
                        analysis_text = response_data['response']
                    else:
                        # Если не нашли подходящей структуры, используем моковые данные
                        logger.error("Не удалось найти текст анализа в ответе API")
                        clothing_elements = [{
                            "type": "Предмет одежды",
                            "color": None,
                            "description": "Не удалось проанализировать изображение",
                            "material": None,
                            "pattern": None
                        }]
                        return {
                            "elements": clothing_elements,
                            "analysis": "Не удалось получить анализ изображения от API"
                        }
                else:
                    # Стандартная структура ответа
                    analysis_text = response_data["choices"][0]["message"]["content"]
                
                # Анализируем текст для извлечения информации о предметах одежды
                clothing_elements = []
                
                # Расширенный и улучшенный список ключевых слов
                clothing_keywords = [
                    'футболка', 'рубашка', 'блузка', 'платье', 'юбка', 
                    'брюки', 'джинсы', 'шорты', 'куртка', 'пальто', 
                    'свитер', 'пиджак', 'костюм', 'блейзер', 'кардиган',
                    'кроссовки', 'туфли', 'ботинки', 'кеды', 'шапка',
                    'толстовка', 'худи', 'жакет', 'жилет', 'топ', 'майка',
                    'сарафан', 'комбинезон', 'плащ', 'пуловер'
                ]
                
                # Разбиваем ответ на отдельные разделы по предметам одежды
                # Искусственно отделяем общий раздел от описаний конкретных предметов
                sections = re.split(r'\n\n+', analysis_text)
                
                # Словарь для хранения информации о предметах
                clothing_data = {}
                current_item = None
                general_info = []
                
                # Обрабатываем каждый раздел
                for section in sections:
                    section = section.strip()
                    if not section:
                        continue
                    
                    # Ищем разделы с заголовками предметов (БЛУЗКА:, ПИДЖАК:, БРЮКИ:)
                    item_header_match = re.match(r'^([А-Я_]+):$', section, re.MULTILINE)
                    if item_header_match:
                        item_type = item_header_match.group(1).lower().capitalize()
                        if item_type == "Общее":
                            # Секция с общей информацией
                            continue
                        
                        current_item = item_type
                        if current_item not in clothing_data:
                            clothing_data[current_item] = {
                                "type": current_item,
                                "color": None,
                                "material": None,
                                "description": "",
                                "pattern": None,
                                "gender": None
                            }
                        
                        # Извлекаем данные из раздела
                        lines = section.split('\n')
                        for line in lines[1:]:  # Пропускаем заголовок
                            line = line.strip()
                            if not line:
                                continue
                            
                            if line.startswith('- Цвет:'):
                                color_value = line.replace('- Цвет:', '').strip()
                                if color_value.lower() != "неизвестно":
                                    clothing_data[current_item]["color"] = color_value
                            
                            elif line.startswith('- Пол:'):
                                gender_value = line.replace('- Пол:', '').strip()
                                if gender_value.lower() != "неизвестно":
                                    clothing_data[current_item]["gender"] = gender_value
                            
                            elif line.startswith('- Материал:'):
                                material_value = line.replace('- Материал:', '').strip()
                                if material_value.lower() != "неизвестно":
                                    clothing_data[current_item]["material"] = material_value
                            
                            elif line.startswith('- Описание:'):
                                desc_value = line.replace('- Описание:', '').strip()
                                if desc_value.lower() != "неизвестно":
                                    clothing_data[current_item]["description"] = desc_value
                
                    # Проверяем нумерованные списки в начале (1. Белая блузка, 2. Серый пиджак)
                    elif re.match(r'^\d+\.', section):
                        # Обрабатываем каждую строку списка
                        lines = section.split('\n')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Ищем нумерованные строки (1. Белая блузка)
                            list_match = re.match(r'^\d+\.\s+(.+)$', line)
                            if list_match:
                                item_desc = list_match.group(1).strip()
                                
                                # Определяем тип предмета
                                found_type = None
                                for keyword in clothing_keywords:
                                    if keyword in item_desc.lower():
                                        found_type = keyword.capitalize()
                                        
                                        # Если этот тип ещё не добавлен в данные
                                        if found_type not in clothing_data:
                                            # Находим цвет
                                            color_match = re.search(r'([а-яА-Я]+(?:-[а-яА-Я]+)?)\s+'+keyword, item_desc, re.IGNORECASE)
                                            color = color_match.group(1) if color_match else None
                                            
                                            # Создаем новую запись
                                            clothing_data[found_type] = {
                                                "type": found_type,
                                                "color": color,
                                                "description": item_desc,
                                                "material": None,
                                                "pattern": None,
                                                "gender": None
                                            }
                                        break
                
                    # Если это секция общей информации или что-то другое
                    elif 'общее' in section.lower() or current_item is None:
                        general_info.append(section)
                
                # Если мы не нашли структурированные данные, ищем предметы одежды в тексте
                if not clothing_data:
                    # Пытаемся найти упоминания предметов одежды в тексте
                    for keyword in clothing_keywords:
                        if keyword in analysis_text.lower():
                            # Ищем цвет для данного предмета
                            color_matches = []
                            for line in analysis_text.split('\n'):
                                if keyword in line.lower():
                                    # Ищем прилагательные перед существительным
                                    color_match = re.search(r'([а-яА-Я]+(?:-[а-яА-Я]+)?)\s+'+keyword, line, re.IGNORECASE)
                                    if color_match:
                                        color_matches.append(color_match.group(1))
                            
                            color = color_matches[0] if color_matches else None
                            
                            # Добавляем предмет в словарь
                            item_type = keyword.capitalize()
                            if item_type not in clothing_data:
                                clothing_data[item_type] = {
                                    "type": item_type,
                                    "color": color,
                                    "description": f"{color if color else ''} {keyword}".strip(),
                                    "material": None,
                                    "pattern": None,
                                    "gender": None
                                }
                
                # Ищем информацию о поле в тексте анализа
                gender_match = re.search(r'ПОЛ:\s*(мужской|женский|унисекс)', analysis_text, re.IGNORECASE)
                general_gender = None
                if gender_match:
                    general_gender = gender_match.group(1).lower()
                    logger.info(f"Найдена информация о поле: {general_gender}")
                
                # Преобразуем словарь в список
                for key, item in clothing_data.items():
                    # Нормализуем цвета
                    if item["color"]:
                        # Убираем различные формы прилагательных и приводим к стандартной форме
                        standard_colors = {
                            "бел": "белый", "белая": "белый", "белое": "белый", "белые": "белый",
                            "черн": "черный", "черная": "черный", "черное": "черный", "черные": "черный",
                            "сер": "серый", "серая": "серый", "серое": "серый", "серые": "серый",
                            "красн": "красный", "красная": "красный", "красное": "красный", "красные": "красный",
                            "син": "синий", "синяя": "синий", "синее": "синий", "синие": "синий",
                            "зелен": "зеленый", "зеленая": "зеленый", "зеленое": "зеленый", "зеленые": "зеленый",
                            "светло-сер": "светло-серый", "светло-серая": "светло-серый", 
                            "светло-серое": "светло-серый", "светло-серые": "светло-серый"
                        }
                        
                        # Убираем цифры и лишние знаки
                        clean_color = re.sub(r'[0-9.\[\]()]', '', item["color"]).strip()
                        
                        # Проверяем, есть ли цвет в словаре стандартизации
                        for color_form, standard_form in standard_colors.items():
                            if clean_color.lower() == color_form.lower():
                                item["color"] = standard_form
                                break
                        else:
                            # Если цвет не найден в словаре, оставляем как есть
                            item["color"] = clean_color
                    
                    # Очищаем описание от номеров
                    if item["description"]:
                        item["description"] = re.sub(r'^\d+\.\s*', '', item["description"]).strip()
                        # Удаляем цифры в конце описания
                        item["description"] = re.sub(r'\s+\d+\s*$', '', item["description"]).strip()
                    
                    # Если у предмета не указан пол, но есть общая информация о поле, используем её
                    if not item.get("gender") and general_gender:
                        item["gender"] = general_gender
                    
                    clothing_elements.append(item)
                
                # Если не нашли предметы одежды, возвращаем заглушку
                if not clothing_elements:
                    clothing_elements = [{
                        "type": "Предмет одежды",
                        "color": None,
                        "description": "Не удалось определить детали одежды",
                        "material": None,
                        "pattern": None
                    }]
                
                return {
                    "elements": clothing_elements,
                    "analysis": analysis_text
                }
                
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {str(e)}")
            raise AttributeError(f"Ошибка при анализе изображения: {str(e)}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Send an image to OpenRouter API")
    parser.add_argument("--image", "-i", required=True, help="Path to the image file")
    parser.add_argument("--model", "-m", default="anthropic/claude-3-haiku-20240307", 
                        help="Model identifier to use (default: anthropic/claude-3-haiku-20240307)")
    parser.add_argument("--prompt", "-p", default="Опиши подробно, что ты видишь на этом изображении. Ответ должен быть на русском языке.",
                        help="Text prompt to accompany the image")
    parser.add_argument("--max-tokens", "-t", type=int, default=2000,
                        help="Maximum number of tokens to generate (default: 2000)")
    parser.add_argument("--api-key", "-k", help="OpenRouter API key (overrides environment variable)")
    parser.add_argument("--output", "-o", help="Output file to save the response (JSON format)")
    parser.add_argument("--clothing-list", "-c", action="store_true", 
                        help="Generate a numbered list of clothing items seen in the image")
    
    args = parser.parse_args()
    
    # Check if image file exists
    if not Path(args.image).exists():
        logger.error(f"Ошибка: Файл изображения не найден: {args.image}")
        return 1
    
    # Check if API key is available
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("Ошибка: API ключ OpenRouter не найден. Укажите его через аргумент --api-key или переменную окружения OPENROUTER_API_KEY")
        return 1
    
    try:
        client = OpenRouterClient(api_key=args.api_key)
        logger.info(f"Отправка изображения {args.image} в OpenRouter с моделью {args.model}")
        
        # If clothing list is requested, use a specialized prompt
        if args.clothing_list:
            prompt = """Проанализируй одежду, которую носит человек на фотографии, и создай пронумерованный список всех элементов одежды. 
            
Правила для создания списка:
1. Каждый элемент одежды должен быть указан отдельным пунктом.
2. Включи точное описание цвета и материала, если это возможно определить.
3. Опиши стиль и посадку каждого предмета.
4. Не включай предположения или неопределённые описания, если что-то не видно чётко.
5. Если виден узор или принт, опиши его.
6. Включи аксессуары и обувь, если они видны.

Формат списка должен быть таким:
1. [Предмет одежды] - [цвет], [материал], [другие важные детали]
2. [Предмет одежды] - [цвет], [материал], [другие важные детали]
И так далее.

Ответ должен быть ТОЛЬКО на русском языке и представлять собой ТОЛЬКО пронумерованный список без вступления и заключения."""
        else:
            prompt = args.prompt
        
        response = client.process_image(
            image_path=args.image,
            model=args.model,
            prompt=prompt,
            max_tokens=args.max_tokens
        )
        
        # Pretty print the response
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # Save to file if specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
            logger.info(f"Response saved to {args.output}")
            
        # Extract and display the model's response text
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            if args.clothing_list:
                print("\nСписок одежды:")
            else:
                print("\nОтвет модели:")
            print(content)
        else:
            print("\nПредупреждение: В ответе нет содержимого в ожидаемом формате.")
            print("Полный ответ API выше.")
        
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 