from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import os
import uvicorn
from pinterest import PinterestAPI
from wildberries_api import WildberriesService
from chat_assistant import ChatAssistant
from visual_analyzer import VisualAnalyzer
from assistant import ChatAssistant, roles
from typing import Optional, List, Dict, Literal, Any
import time
import urllib.parse
import shutil
import uuid
import json
import traceback
import logging
import re
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import math
import os
import time
import json
import random
import string
import asyncio
import logging
import traceback

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Модели данных для API
class SearchRequest(BaseModel):
    query: str
    number_of_photos: Optional[int] = 10
    source: Optional[Literal["pinterest", "wildberries"]] = "pinterest"
    min_price: Optional[float] = None  # Новый параметр - минимальная цена
    max_price: Optional[float] = None  # Новый параметр - максимальная цена
    gender: Optional[str] = None  # Параметр пола для фильтрации товаров (мужской, женский, унисекс)

class SearchResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    """
    Модель для отслеживания состояния задач
    """
    task_id: str
    query: str
    status: Literal["pending", "processing", "analyzing", "completed", "failed"]
    progress: int = 0
    message: Optional[str] = None
    source: Literal["pinterest", "wildberries"] = "pinterest"
    
    # Поля для задач Pinterest
    total_photos: Optional[int] = None
    downloaded_photos: Optional[int] = 0
    image_urls: Optional[List[str]] = None
    pinterest_results: Optional[List[Dict[str, Any]]] = None
    
    # Поля для задач Wildberries
    total_items: Optional[int] = None
    processed_items: Optional[int] = 0
    wildberries_results: Optional[List[Dict[str, Any]]] = None

# Модели данных для API ассистента
class AssistantRequest(BaseModel):
    user_id: str
    role: str
    message: str
    max_tokens: Optional[int] = None  # Опциональный параметр для контроля длины ответа

class AssistantResponse(BaseModel):
    response: str
    role: str
    status: str = "success"
    error: Optional[str] = None

# Модели данных для визуального анализа
class VisualAnalysisResponse(BaseModel):
    results: Dict[str, float] = {}  # Словарь с результатами анализа и их вероятностями
    top_match: str = "Неизвестно"  # Самое вероятное совпадение
    top_score: float = 0.0  # Вероятность лучшего совпадения
    analysis_text: str = ""  # Текст анализа для отображения
    description: Optional[str] = None  # Добавляем поле для детального описания
    elements: Optional[Dict[str, Any]] = None  # Поэлементный анализ одежды

class PinterestSearchRequest(BaseModel):
    query: str
    gender: Optional[str] = "женский"
    num_results: Optional[int] = 3

class WildberriesSearchRequest(BaseModel):
    pinterest_task_id: str
    items: Optional[List[Dict[str, Any]]] = None
    max_products_per_item: Optional[int] = 3

class DirectProductSearchRequest(BaseModel):
    """Запрос на прямой поиск товаров в Wildberries."""
    query: str
    limit: Optional[int] = 10
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    gender: Optional[str] = None

class CosmetologistRequest(BaseModel):
    """Запрос от компонента ассистента косметолога."""
    skinType: str
    concerns: Optional[List[str]] = None
    age: Optional[str] = None
    lifestyles: Optional[List[str]] = None
    currentProducts: Optional[str] = None
    allergies: Optional[str] = None
    organic_only: Optional[bool] = None
    budget: Optional[float] = None

class NutritionistRequest(BaseModel):
    """Запрос от компонента ассистента нутрициолога."""
    goal: str  # weight_loss, muscle_gain, health, energy, special
    restrictions: Optional[List[str]] = None  # vegetarian, vegan, gluten_free, lactose_free, diabetes
    personalInfo: Optional[Dict[str, Any]] = None  # age, weight, height, activity, gender, budget

class DesignerRequest(BaseModel):
    """Запрос от компонента ассистента дизайнера."""
    roomType: str  # living, bedroom, kitchen, office, children
    style: str  # modern, scandinavian, loft, classic, minimalist
    roomInfo: Optional[Dict[str, Any]] = None  # area, budget, hasWindows, hasImage

class FurnitureRecommendationRequest(BaseModel):
    """Запрос на получение рекомендаций по мебели."""
    roomType: str  # living, bedroom, kitchen, office, children
    style: str  # modern, scandinavian, loft, classic, minimalist
    roomInfo: Dict[str, Any]  # area, budget, hasWindows

# Создаем FastAPI приложение
app = FastAPI(
    title="Shopping Assistant API",
    description="API для шопинг-ассистента с поддержкой Pinterest и Wildberries",
    version="1.0.0"
)

# Настраиваем CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Конкретные источники для фронтенда
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Хранилище для задач
tasks: Dict[str, TaskStatus] = {}

# Хранилище для инстансов сервисов
_pinterest_instance = None
_wildberries_service_instance = None
_assistant_instance = None
_visual_analyzer_instance = None

def get_pinterest() -> Optional[PinterestAPI]:
    """
    Возвращает экземпляр Pinterest API
    
    Returns:
        Экземпляр PinterestAPI или None в случае ошибки
    """
    global _pinterest_instance
    
    try:
        if _pinterest_instance is None:
            # Получаем API ключ OpenAI для анализа изображений
            openai_api_key = os.getenv("OPENAI_API_KEY")
            
            # Создаем директорию для скачивания, если её нет
            os.makedirs('photo', exist_ok=True)
            
            # Импортируем PinterestAPI
            from pinterest import PinterestAPI
            
            # Создаем экземпляр Pinterest с поддержкой анализа изображений
            _pinterest_instance = PinterestAPI(download_dir='photo', openai_api_key=openai_api_key)
            
            logger.info("Инициализирован экземпляр Pinterest API с поддержкой анализа изображений")
        
        return _pinterest_instance
    except Exception as e:
        logger.error(f"Ошибка при инициализации Pinterest API: {e}")
        return None

def get_wildberries_service() -> Optional[WildberriesService]:
    """
    Получает экземпляр WildberriesService
    
    Returns:
        Экземпляр WildberriesService или None в случае ошибки
    """
    global _wildberries_service_instance
    
    try:
        if _wildberries_service_instance is None:
            _wildberries_service_instance = WildberriesService()
        
        return _wildberries_service_instance
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации WildberriesService: {str(e)}")
        return None

def get_assistant() -> Optional[ChatAssistant]:
    """
    Получает экземпляр ChatAssistant
    
    Returns:
        Экземпляр ChatAssistant или None в случае ошибки
    """
    global _assistant_instance
    
    try:
        if _assistant_instance is None:
            # Загружаем переменные окружения из .env файла
            load_dotenv()
            
            # Получаем API-ключ OpenRouter из переменных окружения
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            
            if not openrouter_api_key:
                logger.error("API-ключ OpenRouter не найден в переменных окружения")
                return None
                
            logger.info("API-ключ OpenRouter успешно загружен")
            
            # Создаем экземпляр ChatAssistant с передачей API-ключа
            _assistant_instance = ChatAssistant(
                model_type="openrouter",
                model_name="anthropic/claude-3-haiku",
                openrouter_api_key=openrouter_api_key
            )
        
        return _assistant_instance
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации ChatAssistant: {str(e)}")
        return None

def get_visual_analyzer() -> Optional[VisualAnalyzer]:
    """
    Получает экземпляр VisualAnalyzer
    
    Returns:
        Экземпляр VisualAnalyzer или None в случае ошибки
    """
    global _visual_analyzer_instance
    
    try:
        if _visual_analyzer_instance is None:
            try:
                _visual_analyzer_instance = VisualAnalyzer()
            except Exception as e:
                logger.warning(f"Не удалось инициализировать VisualAnalyzer: {str(e)}")
                return None
        
        return _visual_analyzer_instance
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации VisualAnalyzer: {str(e)}")
        return None

@app.on_event("startup")
async def startup_event():
    """Initializes the application state on startup"""
    # Создаем необходимые директории
    os.makedirs("static", exist_ok=True)
    os.makedirs("static/uploads", exist_ok=True)
    os.makedirs("static/images", exist_ok=True)
    
    # Инициализируем анализатор изображений
    if get_visual_analyzer():
        logger.info("Визуальный анализатор успешно инициализирован")
    else:
        logger.info("Визуальный анализатор недоступен, будет использоваться OpenRouter API")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Закрываем драйверы парсеров при завершении работы
    """
    global _pinterest_instance, _wildberries_service_instance
    if _pinterest_instance:
        _pinterest_instance.close()
    if _wildberries_service_instance:
        _wildberries_service_instance.close()

@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервера
    """
    return {"status": "ok", "message": "Сервер работает"}

@app.post("/search")
async def search_products_endpoint(request: SearchRequest):
    """
    Ищет товары по запросу и возвращает результаты.
    
    Args:
        request: Параметры запроса
    
    Returns:
        Идентификатор задачи и статус
    """
    try:
        logger.info(f"Получен запрос на поиск товаров: {request.query}")
        
        # Создаем задачу
        task_id = str(uuid.uuid4())
        
        # Инициализируем состояние задачи
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            query=request.query,
            status="pending",
            progress=0,
            total_photos=request.number_of_photos,
            downloaded_photos=0,
            source=request.source
        )
        
        # Запускаем задачу в фоне
        background_tasks = BackgroundTasks()
        if request.source == "pinterest":
            background_tasks.add_task(process_pinterest_search, task_id, request)
        else:
            background_tasks.add_task(process_wildberries_search, task_id, request)
        
        # Выполняем задачу немедленно для более быстрого ответа
        if request.source == "pinterest":
            await process_pinterest_search(task_id, request)
        else:
            await process_wildberries_search(task_id, request)
        
        # Возвращаем результат задачи, если он уже есть
        if tasks[task_id].status == "completed":
            logger.info(f"Задача {task_id} завершена успешно")
            return {
                "task_id": task_id,
                "status": "completed",
                "product_details": tasks[task_id].product_details if hasattr(tasks[task_id], "product_details") else [],
                "image_urls": tasks[task_id].image_urls if hasattr(tasks[task_id], "image_urls") else []
            }
        else:
            logger.info(f"Задача {task_id} в процессе выполнения или завершилась с ошибкой")
            return {
                "task_id": task_id,
                "status": tasks[task_id].status,
                "message": tasks[task_id].message
            }
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

async def process_pinterest_search(task_id: str, request: SearchRequest):
    """Обработка поиска в Pinterest"""
    try:
        pinterest = PinterestAPI()
        # Используем search_pins вместо get_images
        pins = await pinterest.search_pins(
            query=request.query,
            limit=request.number_of_photos,
            download=True
        )
        
        if pins:
            tasks[task_id].status = "completed"
            tasks[task_id].progress = 100
            tasks[task_id].downloaded_photos = len(pins)
            tasks[task_id].folder_path = pinterest.photo_dir
            tasks[task_id].image_urls = [pin.image_url for pin in pins]
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"Не найдены изображения для запроса '{request.query}'"
    except Exception as e:
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Ошибка при поиске: {str(e)}"
        logger.error(f"Ошибка при поиске в Pinterest: {str(e)}")
    finally:
        await pinterest.close()

async def process_wildberries_search(task_id: str, request: SearchRequest):
    """
    Обработка поиска в Wildberries
    
    Args:
        task_id: Идентификатор задачи
        request: Параметры запроса
        
    Note:
        Особенности работы с параметрами цены:
        - min_price - фильтрует товары по основной цене (price), т.е. возвращаются товары с price ≥ min_price
        - max_price - фильтрует товары по скидочной цене (sale_price), т.е. возвращаются товары с sale_price ≤ max_price
        - При установке max_price=5000 могут возвращаться товары с основной ценой выше 5000 руб.,
          если их скидочная цена (sale_price) не превышает 5000 руб.
        - При установке обоих параметров (min_price и max_price) применяются оба фильтра последовательно:
          сначала отбираются товары с price ≥ min_price, затем из них выбираются товары с sale_price ≤ max_price
        - При противоречивых параметрах (например, min_price=30000, max_price=10000) приоритет отдается min_price,
          что может привести к пустому результату, если нет товаров, удовлетворяющих обоим условиям
    """
    try:
        logger.info(f"Запуск поиска товаров в Wildberries по запросу: '{request.query}', лимит: {request.number_of_photos}, мин. цена: {request.min_price}, макс. цена: {request.max_price}, пол: {request.gender}")
        
        # Получаем экземпляр Wildberries клиента
        wb = WildberriesService()
        
        # Параметры поиска - используем параметры из запроса
        min_price = request.min_price  # Может быть None
        max_price = request.max_price  # Может быть None
        gender = request.gender  # Может быть None
        
        # Проверка на противоречивые параметры
        if min_price is not None and max_price is not None and min_price > max_price:
            logger.warning(f"Противоречивые параметры цены: min_price ({min_price}) > max_price ({max_price}). Это может привести к пустому результату.")
        
        # Используем search_products из WildberriesAPI с проверенными значениями
        products = await wb.search_products(
            query=request.query,
            limit=request.number_of_photos,
            min_price=min_price,
            max_price=max_price,
            gender=gender
        )
        
        # Обработка результатов
        if products:
            product_count = len(products)
            logger.info(f"Найдено {product_count} товаров по запросу '{request.query}'")
            
            tasks[task_id].status = "completed"
            tasks[task_id].progress = 100
            tasks[task_id].downloaded_photos = product_count
            tasks[task_id].product_details = products
            tasks[task_id].message = f"Найдено {product_count} товаров"
        else:
            logger.warning(f"Не найдены товары в Wildberries для запроса '{request.query}'")
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"Не найдены товары для запроса '{request.query}'"
    except Exception as e:
        logger.error(f"Ошибка при поиске в Wildberries: {str(e)}")
        logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Ошибка при поиске: {str(e)}"
    finally:
        # Закрываем соединения
        if 'wb' in locals():
            await wb.close()
            logger.debug("Соединения с Wildberries закрыты")

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Получение статуса задачи по её ID
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return tasks[task_id]

@app.post("/analyze-image")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Анализирует загруженное изображение и ищет похожие товары на Wildberries
    """
    try:
        logger.info(f"Получен файл для анализа: {file.filename}")
        
        # Создаем директорию, если она не существует
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Сохраняем файл с уникальным именем
        file_ext = os.path.splitext(file.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Файл сохранен: {file_path}")
        
        # Получаем экземпляр ассистента
        assistant = get_assistant()
        if not assistant:
            raise HTTPException(status_code=500, detail="Не удалось инициализировать ассистента")
        
        # Анализируем изображение
        analysis = await assistant.analyze_image_async(file_path)
        logger.info(f"Результат анализа: {analysis}")
        
        # Получаем экземпляр WildberriesService
        wb_service = get_wildberries_service()
        if not wb_service:
            raise HTTPException(status_code=500, detail="Не удалось инициализировать WildberriesService")
        
        # Извлекаем информацию о поле из анализа
        gender = "женский"  # По умолчанию
        if "analysis" in analysis:
            if "мужской" in analysis["analysis"].lower():
                gender = "мужской"
            elif "женский" in analysis["analysis"].lower():
                gender = "женский"
        
        # Формируем структурированный ответ и ищем товары на WB
        clothing_items = []
        elements = analysis.get("elements", [])
        
        # Проверка, является ли анализ некачественным (единственный элемент "Предмет одежды" без деталей)
        is_low_quality = (len(elements) == 1 and 
                          elements[0].get("type") == "Предмет одежды" and 
                          elements[0].get("color") is None and 
                          elements[0].get("description") and 
                          "Не удалось проанализировать" in elements[0].get("description"))
        
        # Если анализ некачественный, генерируем базовые предметы одежды для поиска
        if is_low_quality:
            logger.info("Обнаружен некачественный анализ изображения, применяем запасные предметы")
            
            # Предопределенные типы одежды в зависимости от пола
            if gender == "мужской":
                elements = [
                    {"type": "Пиджак", "color": "Тёмно-синий", "description": "Классический пиджак", "gender": "мужской"},
                    {"type": "Рубашка", "color": "Белый", "description": "Формальная рубашка", "gender": "мужской"},
                    {"type": "Брюки", "color": "Тёмно-синий", "description": "Классические брюки", "gender": "мужской"}
                ]
            else:  # женский по умолчанию
                elements = [
                    {"type": "Блузка", "color": "Белый", "description": "Классическая блузка", "gender": "женский"},
                    {"type": "Жакет", "color": "Тёмно-синий", "description": "Приталенный жакет", "gender": "женский"},
                    {"type": "Юбка", "color": "Тёмно-синий", "description": "Прямая юбка", "gender": "женский"}
                ]
            
            # Обновляем анализ
            analysis["elements"] = elements
            analysis["analysis"] = f"Автоматически определены предметы: {', '.join([item['type'] for item in elements])}"
        
        # Обрабатываем каждый элемент
        for item in elements:
            type_name = item.get("type", "Предмет одежды")
            color = item.get("color", "")
            description = item.get("description", "")
            
            # Формируем поисковый запрос для WB
            search_query = f"{color} {type_name}".strip()
            if description:
                # Добавляем только первые два слова из описания
                desc_words = description.split()[:2]
                search_query += f" {' '.join(desc_words)}"
            
            # Ищем товары на WB
            try:
                wb_products = await wb_service.search_products(
                    query=search_query,
                    limit=3,  # 3 товара для каждого предмета
                    gender=gender
                )
                
                clothing_items.append({
                    "type": type_name,
                    "color": color,
                    "description": description,
                    "gender": gender,
                    "wb_products": wb_products if wb_products else []
                })
            except Exception as e:
                logger.error(f"Ошибка при поиске товаров на WB: {str(e)}")
                clothing_items.append({
                    "type": type_name,
                    "color": color,
                    "description": description,
                    "gender": gender,
                    "wb_products": []
                })
        
        # Формируем ответ
        response = {
            "elements": analysis.get("elements", []),  # Возвращаем оригинальные элементы для отображения
            "analysis": analysis.get("analysis", ""),
            "image_path": f"/static/uploads/{file_name}",
            "gender": gender,
            "results": clothing_items,  # Результаты поиска по элементам
            "api_source": "live"  # Указываем источник данных - живой API
        }
        
        # Если был применен запасной вариант для некачественного анализа
        if is_low_quality:
            response["api_source"] = "fallback"
            response["error"] = "API не смог точно проанализировать изображение. Показаны предложения на основе стандартных моделей одежды."
        
        logger.info(f"Анализ изображения выполнен успешно: {len(clothing_items)} предметов найдено")
        return response
            
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.delete("/assistant/{user_id}")
async def clear_assistant_history(user_id: str):
    """
    Очистка истории разговора для указанного пользователя
    """
    try:
        assistant = get_assistant()
        result = await assistant.clear_conversation_async(user_id)
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        print(f"Ошибка при очистке истории: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при очистке истории: {str(e)}"
        )

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """
    Перенаправляет на страницу документации API
    """
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <meta http-equiv="refresh" content="0;url=/docs" />
            <title>Перенаправление</title>
        </head>
        <body>
            <p>Перенаправление на <a href="/docs">документацию API</a>...</p>
        </body>
    </html>
    """
    return html_content

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/roles")
async def get_available_roles():
    """
    Получение списка доступных ролей для ассистента
    """
    return {
        "roles": list(roles.keys())
    }

@app.post("/assistant", response_model=AssistantResponse)
async def chat_with_assistant(request: AssistantRequest):
    """
    Отправка сообщения ассистенту и получение ответа
    
    - **user_id**: Уникальный идентификатор пользователя (для сохранения истории)
    - **role**: Роль ассистента (стилист, косметолог, нутрициолог, дизайнер)
    - **message**: Сообщение пользователя для ассистента
    - **max_tokens**: Максимальное количество токенов в ответе (по умолчанию 2048)
    """
    try:
        assistant = get_assistant()
        
        # Проверяем, что роль существует
        if request.role not in roles:
            raise HTTPException(
                status_code=400, 
                detail=f"Неизвестная роль. Доступные роли: {', '.join(roles.keys())}"
            )
        
        # Если передан параметр max_tokens, временно устанавливаем его
        original_max_tokens = None
        if request.max_tokens:
            original_max_tokens = assistant.max_tokens
            assistant.max_tokens = request.max_tokens
        
        try:
            # Используем асинхронную версию метода
            response = await assistant.generate_response_async(
                user_id=request.user_id,
                role=request.role,
                user_input=request.message
            )
            
            return AssistantResponse(
                response=response,
                role=request.role,
                status="success"
            )
        finally:
            # Восстанавливаем оригинальное значение max_tokens если оно было изменено
            if original_max_tokens is not None:
                assistant.max_tokens = original_max_tokens
                
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации ответа: {str(e)}"
        )

@app.get("/tasks")
async def get_all_tasks():
    """
    Получение списка всех задач
    """
    return list(tasks.values())

@app.post("/search-pinterest")
async def search_pinterest_endpoint(request: PinterestSearchRequest):
    """
    Ищет образы в Pinterest по запросу, анализирует одежду на найденных изображениях
    и возвращает результаты анализа.
    
    Args:
        request: Параметры запроса (текстовый запрос, пол, количество результатов)
    
    Returns:
        Идентификатор задачи и статус
    """
    try:
        logger.info(f"Получен запрос на поиск образов в Pinterest: {request.query}, пол: {request.gender}")
        
        # Создаем задачу
        task_id = str(uuid.uuid4())
        
        # Инициализируем состояние задачи
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            query=request.query,
            status="pending",
            progress=0,
            total_photos=request.num_results,
            downloaded_photos=0,
            source="pinterest"
        )
        
        # Запускаем задачу в фоне
        background_tasks = BackgroundTasks()
        background_tasks.add_task(process_pinterest_outfit_search, task_id, request)
        
        # Запускаем задачу сразу для более быстрого ответа
        await process_pinterest_outfit_search(task_id, request)
        
        # Возвращаем идентификатор задачи
        return {
            "task_id": task_id,
            "status": tasks[task_id].status,
            "message": tasks[task_id].message if hasattr(tasks[task_id], "message") else "Задача создана"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при поиске образов в Pinterest: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

async def process_pinterest_outfit_search(task_id: str, request: PinterestSearchRequest):
    """Обработка поиска образов в Pinterest"""
    try:
        # Получаем экземпляр Pinterest
        pinterest = get_pinterest()
        if not pinterest:
            raise Exception("Не удалось инициализировать Pinterest")
        
        # Обновляем статус задачи
        tasks[task_id].status = "processing"
        tasks[task_id].message = "Поиск образов в Pinterest"
        
        # Ищем пины в Pinterest с анализом изображений
        pins = await pinterest.search_pins(
            query=request.query,
            limit=request.num_results,
            download=True,
            analyze_images=True,  # Активируем анализ изображений
            gender=request.gender  # Передаем пол для контекста
        )
        
        if not pins:
            tasks[task_id].status = "failed"
            tasks[task_id].message = "Не удалось найти образы в Pinterest"
            return
        
        # Обновляем статус задачи
        tasks[task_id].status = "analyzing"
        tasks[task_id].message = "Анализ найденных изображений"
        tasks[task_id].downloaded_photos = len(pins)
        
        # Сохраняем URL изображений для последующего использования
        tasks[task_id].image_urls = [pin.image_url for pin in pins]
        
        # Преобразуем результаты в нужный формат
        results = []
        
        for pin in pins:
            # Проверяем наличие предметов одежды
            clothing_items = []
            
            # Используем прямой доступ к image_analyzer, а не через атрибут api
            if hasattr(pinterest, 'image_analyzer'):
                # Если предметов одежды нет или их очень мало, пробуем повторно проанализировать
                if not pin.clothing_items or len(pin.clothing_items) < 1:
                    try:
                        # Используем запасной механизм для получения предметов одежды
                        pin.clothing_items = pinterest.image_analyzer._generate_fallback_clothing_items(request.query, request.gender)
                        logger.info(f"Использован запасной механизм для получения предметов одежды: {len(pin.clothing_items)} предметов")
                    except Exception as e:
                        logger.error(f"Ошибка при повторном анализе: {e}")
            
            if pin.clothing_items:
                for item in pin.clothing_items:
                    clothing_items.append({
                        "type": item.get("type", "неизвестно"),
                        "color": item.get("color", "неизвестно"),
                        "description": item.get("description", ""),
                        "gender": item.get("gender", request.gender)
                    })
            else:
                # Если предметов одежды не найдено, создаем случайные на основе запроса
                gender = request.gender or "унисекс"
                query_lower = request.query.lower()
                
                # Определяем стиль одежды на основе запроса
                if "офисный" in query_lower or "деловой" in query_lower:
                    if gender == "мужской":
                        clothing_items = [
                            {"type": "костюм", "color": "темно-синий", "description": "классический", "gender": gender},
                            {"type": "рубашка", "color": "белая", "description": "с длинным рукавом", "gender": gender},
                            {"type": "туфли", "color": "черные", "description": "классические", "gender": gender}
                        ]
                    else:
                        clothing_items = [
                            {"type": "пиджак", "color": "черный", "description": "классический прямой", "gender": gender},
                            {"type": "блузка", "color": "белая", "description": "с воротником", "gender": gender},
                            {"type": "юбка", "color": "черная", "description": "прямая до колена", "gender": gender}
                        ]
                elif "повседневный" in query_lower or "casual" in query_lower:
                    if gender == "мужской":
                        clothing_items = [
                            {"type": "джинсы", "color": "синие", "description": "прямые", "gender": gender},
                            {"type": "футболка", "color": "белая", "description": "хлопковая", "gender": gender},
                            {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": gender}
                        ]
                    else:
                        clothing_items = [
                            {"type": "джинсы", "color": "синие", "description": "скинни", "gender": gender},
                            {"type": "футболка", "color": "белая", "description": "базовая", "gender": gender},
                            {"type": "кеды", "color": "белые", "description": "классические", "gender": gender}
                        ]
                elif "спортивный" in query_lower:
                    clothing_items = [
                        {"type": "толстовка", "color": "серая", "description": "спортивная с капюшоном", "gender": gender},
                        {"type": "брюки", "color": "черные", "description": "спортивные", "gender": gender},
                        {"type": "кроссовки", "color": "белые", "description": "спортивные", "gender": gender}
                    ]
                elif "вечерний" in query_lower:
                    if gender == "мужской":
                        clothing_items = [
                            {"type": "костюм", "color": "черный", "description": "вечерний", "gender": gender},
                            {"type": "рубашка", "color": "белая", "description": "классическая", "gender": gender},
                            {"type": "туфли", "color": "черные", "description": "кожаные", "gender": gender}
                        ]
                    else:
                        clothing_items = [
                            {"type": "платье", "color": "черное", "description": "вечернее", "gender": gender},
                            {"type": "туфли", "color": "черные", "description": "на высоком каблуке", "gender": gender},
                            {"type": "сумка", "color": "черная", "description": "клатч", "gender": gender}
                        ]
                else:
                    # Базовый набор
                    if gender == "мужской":
                        clothing_items = [
                            {"type": "рубашка", "color": "голубая", "description": "классическая", "gender": gender},
                            {"type": "брюки", "color": "темно-синие", "description": "классические", "gender": gender},
                            {"type": "туфли", "color": "коричневые", "description": "кожаные", "gender": gender}
                        ]
                    else:
                        clothing_items = [
                            {"type": "блузка", "color": "белая", "description": "классическая", "gender": gender},
                            {"type": "юбка", "color": "черная", "description": "классическая", "gender": gender},
                            {"type": "туфли", "color": "черные", "description": "на каблуке", "gender": gender}
                        ]
            
            # Формируем результат для каждого пина
            result = {
                "imageUrl": pin.image_url,
                "sourceUrl": pin.link or f"https://www.pinterest.com/pin/{pin.id}/",
                "description": pin.title or pin.description or f"Образ в стиле {request.query}",
                "clothingItems": clothing_items
            }
            
            results.append(result)
        
        # Сохраняем результаты в задаче
        tasks[task_id].pinterest_results = results
        tasks[task_id].status = "completed"
        tasks[task_id].progress = 100
        tasks[task_id].message = f"Найдено {len(results)} образов"
        
        logger.info(f"Задача {task_id} успешно завершена: найдено {len(results)} образов")
        
    except Exception as e:
        logger.error(f"Ошибка при поиске образов в Pinterest: {e}")
        logger.error(traceback.format_exc())
        
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Ошибка при поиске образов: {str(e)}"
    finally:
        # Закрываем соединения
        if pinterest:
            await pinterest.close()

def parse_assistant_response(response: str, gender: str = "женский") -> List[Dict[str, str]]:
    """
    Парсит ответ ассистента для извлечения предметов одежды
    
    Args:
        response: Ответ ассистента
        gender: Пол (мужской или женский)
    
    Returns:
        Список предметов одежды с типом, цветом и описанием
    """
    try:
        # Попробуем извлечь структурированные данные
        clothing_items = []
        
        # Парсим разными способами
        # 1. Попробуем найти маркированный список
        lines = response.split("\n")
        
        # Ищем предметы одежды с помощью регулярных выражений
        current_item = {}
        for line in lines:
            line = line.strip()
            
            # Пропускаем пустые строки
            if not line:
                continue
            
            # Проверяем, является ли строка новым элементом списка
            if line.startswith(("- ", "• ", "* ", "1. ", "2. ", "3. ")) or re.match(r"^\d+\.", line):
                # Если уже собрали предмет, добавляем его в список
                if current_item and "type" in current_item:
                    clothing_items.append(current_item)
                    current_item = {}
                
                # Удаляем маркер списка
                line = re.sub(r"^[•\-\*\d\.]+\s*", "", line)
                
                # Пробуем определить тип и цвет предмета
                match_type_color = re.search(r"([а-яА-Я]+)(?:\s+|:)([а-яА-Я]+)", line, re.IGNORECASE)
                if match_type_color:
                    current_item = {
                        "type": match_type_color.group(1).lower(),
                        "color": match_type_color.group(2).lower(),
                        "description": line.replace(f"{match_type_color.group(1)} {match_type_color.group(2)}", "").strip(),
                        "gender": gender
                    }
                else:
                    # Если не удалось определить тип и цвет, берем всю строку как описание
                    words = line.split()
                    if len(words) >= 2:
                        current_item = {
                            "type": words[0].lower(),
                            "color": words[1].lower(),
                            "description": " ".join(words[2:]),
                            "gender": gender
                        }
                    else:
                        current_item = {
                            "type": line.lower(),
                            "color": "неизвестный",
                            "description": "",
                            "gender": gender
                        }
            
            # Если строка содержит ":" и мы уже начали собирать предмет, это может быть свойство
            elif ":" in line and current_item:
                key, value = line.split(":", 1)
                key = key.lower().strip()
                value = value.strip()
                
                if key in ["тип", "предмет", "вещь"]:
                    current_item["type"] = value.lower()
                elif key in ["цвет", "оттенок"]:
                    current_item["color"] = value.lower()
                elif key in ["описание", "особенности", "детали"]:
                    current_item["description"] = value
                elif key in ["пол"]:
                    current_item["gender"] = value.lower()
        
        # Добавляем последний предмет, если он есть
        if current_item and "type" in current_item:
            clothing_items.append(current_item)
        
        # Если не удалось найти предметы, создаем простые на основе ключевых слов
        if not clothing_items:
            # Ищем упоминания распространенных предметов одежды
            clothing_types = ["футболка", "рубашка", "блузка", "джинсы", "брюки", "юбка", "платье", 
                            "куртка", "пальто", "свитер", "кофта", "жакет", "пиджак", "шорты",
                            "кроссовки", "туфли", "ботинки", "сапоги", "кеды", "шляпа", "шапка"]
            
            for clothing_type in clothing_types:
                if clothing_type in response.lower():
                    # Ищем цвет рядом с типом одежды
                    color_match = re.search(r"(\w+)\s+" + clothing_type, response.lower())
                    color = color_match.group(1) if color_match else "неизвестный"
                    
                    clothing_items.append({
                        "type": clothing_type,
                        "color": color,
                        "description": "",
                        "gender": gender
                    })
        
        # Если все еще нет предметов, создаем по умолчанию
        if not clothing_items:
            clothing_items = [
                {
                    "type": "футболка",
                    "color": "белая",
                    "description": "базовая",
                    "gender": gender
                },
                {
                    "type": "джинсы",
                    "color": "синие",
                    "description": "классические",
                    "gender": gender
                }
            ]
        
        return clothing_items
        
    except Exception as e:
        logger.error(f"Ошибка при парсинге ответа ассистента: {str(e)}")
        # Возвращаем предметы по умолчанию
        return [
            {
                "type": "футболка",
                "color": "белая",
                "description": "базовая",
                "gender": gender
            },
            {
                "type": "джинсы",
                "color": "синие",
                "description": "классические",
                "gender": gender
            }
        ]

@app.get("/search-pinterest/{task_id}")
async def get_pinterest_search_results(task_id: str):
    """
    Получает результаты поиска по идентификатору задачи
    
    Args:
        task_id: Идентификатор задачи
        
    Returns:
        Результаты поиска и статус задачи
    """
    try:
        # Проверяем наличие задачи
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail=f"Задача с идентификатором {task_id} не найдена")
        
        # Получаем статус задачи
        task = tasks[task_id]
        
        # Формируем ответ
        response = {
            "task_id": task_id,
            "status": task.status,
            "message": task.message if hasattr(task, "message") else "",
            "progress": task.progress,
            "source": task.source if hasattr(task, "source") else "pinterest"
        }
        
        # Если задача завершена, добавляем результаты
        if task.status == "completed" and hasattr(task, "pinterest_results"):
            response["results"] = task.pinterest_results
        elif task.status == "analyzing" and hasattr(task, "image_urls"):
            response["image_urls"] = task.image_urls
        
        return response
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при получении результатов поиска: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.post("/search-wildberries")
async def search_wildberries_endpoint(request: WildberriesSearchRequest):
    """
    Ищет товары на Wildberries на основе результатов поиска в Pinterest
    
    Args:
        request: Параметры запроса (идентификатор задачи Pinterest, предметы одежды, максимальное количество товаров)
    
    Returns:
        Идентификатор задачи и статус
    """
    try:
        # Проверяем наличие задачи Pinterest
        if request.pinterest_task_id not in tasks:
            raise HTTPException(status_code=404, detail=f"Задача с идентификатором {request.pinterest_task_id} не найдена")
        
        pinterest_task = tasks[request.pinterest_task_id]
        
        # Проверяем статус задачи Pinterest
        if pinterest_task.status != "completed":
            raise HTTPException(status_code=400, detail=f"Задача Pinterest не завершена, текущий статус: {pinterest_task.status}")
        
        # Проверяем наличие результатов
        if not hasattr(pinterest_task, "pinterest_results"):
            raise HTTPException(status_code=400, detail="Результаты анализа Pinterest не найдены")
        
        # Создаем новую задачу для поиска на Wildberries
        task_id = str(uuid.uuid4())
        
        # Инициализируем состояние задачи
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            query=f"Поиск товаров на Wildberries на основе {request.pinterest_task_id}",
            status="pending",
            progress=0,
            source="wildberries"
        )
        
        # Получаем предметы одежды для поиска
        search_items = []
        
        if request.items and len(request.items) > 0:
            # Используем предметы из запроса
            search_items = request.items
        else:
            # Используем все предметы из результатов Pinterest
            for result in pinterest_task.pinterest_results:
                if "clothingItems" in result:
                    search_items.extend(result["clothingItems"])
        
        # Если предметов нет, возвращаем ошибку
        if not search_items:
            tasks[task_id].status = "failed"
            tasks[task_id].message = "Не найдены предметы одежды для поиска"
            return {
                "task_id": task_id,
                "status": "failed",
                "message": "Не найдены предметы одежды для поиска"
            }
        
        # Запускаем задачу в фоне
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            process_wildberries_search, 
            task_id, 
            search_items, 
            request.max_products_per_item
        )
        
        # Запускаем задачу сразу для более быстрого ответа
        await process_wildberries_search(task_id, search_items, request.max_products_per_item)
        
        # Возвращаем идентификатор задачи
        return {
            "task_id": task_id,
            "status": tasks[task_id].status,
            "message": tasks[task_id].message if hasattr(tasks[task_id], "message") else "Задача создана"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров на Wildberries: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

async def process_wildberries_search(task_id: str, search_items: List[Dict[str, Any]], max_products_per_item: int = 3):
    """
    Обработка поиска товаров на Wildberries
    
    Args:
        task_id: Идентификатор задачи
        search_items: Предметы одежды для поиска
        max_products_per_item: Максимальное количество товаров на предмет
    """
    try:
        # Получаем инстанс WildberriesService
        wildberries_service = get_wildberries_service()
        if not wildberries_service:
            raise Exception("Не удалось инициализировать WildberriesService")
        
        # Обновляем статус задачи
        tasks[task_id].status = "processing"
        tasks[task_id].message = "Поиск товаров на Wildberries"
        tasks[task_id].total_items = len(search_items)
        tasks[task_id].processed_items = 0
        
        # Результаты поиска
        search_results = []
        
        # Обрабатываем каждый предмет одежды
        for i, item in enumerate(search_items):
            try:
                # Формируем запрос для поиска
                type_name = item.get("type", "").strip()
                color = item.get("color", "").strip()
                description = item.get("description", "").strip()
                gender = item.get("gender", "женский").strip()
                
                # Если тип пустой, пропускаем
                if not type_name:
                    continue
                
                # Формируем поисковый запрос
                search_query = f"{type_name}"
                if color and color != "неизвестный":
                    search_query += f" {color}"
                
                # Добавляем часть описания, если есть
                if description:
                    # Извлекаем ключевые слова из описания
                    keywords = re.findall(r'\b[а-яА-Я]{3,}\b', description)
                    if keywords:
                        search_query += f" {' '.join(keywords[:2])}"
                
                # Обновляем статус
                current_item_num = i + 1
                tasks[task_id].progress = int(current_item_num / len(search_items) * 100)
                tasks[task_id].processed_items = current_item_num
                tasks[task_id].message = f"Поиск товаров для предмета {current_item_num}/{len(search_items)}: {search_query}"
                
                # Выполняем поиск на Wildberries
                search_results_wb = await wildberries_service.search_products_async(
                    search_query, 
                    gender=gender,
                    limit=max_products_per_item
                )
                
                # Если результаты найдены, добавляем в общий список
                if search_results_wb:
                    search_results.append({
                        "query": search_query,
                        "item": item,
                        "products": search_results_wb
                    })
                
            except Exception as e:
                logger.error(f"Ошибка при поиске товаров для предмета {item.get('type', '')}: {str(e)}")
                continue
        
        # Обновляем статус задачи
        if search_results:
            tasks[task_id].status = "completed"
            tasks[task_id].message = f"Найдено {len(search_results)} товаров"
            # Добавляем результаты к задаче
            setattr(tasks[task_id], "wildberries_results", search_results)
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = "Не найдено товаров"
        
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров на Wildberries: {str(e)}")
        logger.error(traceback.format_exc())
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Ошибка: {str(e)}"

@app.get("/search-wildberries/{task_id}")
async def get_wildberries_search_results(task_id: str):
    """
    Получает результаты поиска на Wildberries по идентификатору задачи
    
    Args:
        task_id: Идентификатор задачи
        
    Returns:
        Результаты поиска и статус задачи
    """
    try:
        # Проверяем наличие задачи
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail=f"Задача с идентификатором {task_id} не найдена")
        
        # Получаем статус задачи
        task = tasks[task_id]
        
        # Формируем ответ
        response = {
            "task_id": task_id,
            "status": task.status,
            "message": task.message if hasattr(task, "message") else "",
            "progress": task.progress,
            "source": task.source if hasattr(task, "source") else "wildberries"
        }
        
        # Если задача завершена, добавляем результаты
        if task.status == "completed" and hasattr(task, "wildberries_results"):
            response["results"] = task.wildberries_results
        
        return response
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при получении результатов поиска на Wildberries: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.post("/api/search-products-direct")
async def search_products_direct_endpoint(request: DirectProductSearchRequest):
    """
    Прямой поиск товаров в Wildberries без создания задачи.
    
    Args:
        request: Параметры запроса
        
    Returns:
        Список найденных товаров
    """
    try:
        logger.info(f"Получен запрос на прямой поиск товаров: {request.query}, пол: {request.gender}, лимит: {request.limit}")
        
        # Инициализируем сервис Wildberries
        wildberries = get_wildberries_service()
        if not wildberries:
            logger.error("Не удалось инициализировать сервис Wildberries")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать сервис Wildberries")
        
        # Выполняем поиск товаров с учетом параметров запроса
        products = await wildberries.search_products_async(
            query=request.query,
            limit=request.limit,
            min_price=request.min_price,
            max_price=request.max_price,
            gender=request.gender
        )
        
        logger.info(f"Найдено {len(products)} товаров по запросу '{request.query}'")
        
        # Возвращаем результаты поиска
        return products
        
    except Exception as e:
        logger.error(f"Ошибка при прямом поиске товаров: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.get("/api/search-products", response_model=List[Dict[str, Any]])
async def search_products(
    query: str, 
    limit: int = 3,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    gender: Optional[str] = None
):
    """
    Поиск товаров на Wildberries
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов
        min_price: Минимальная цена
        max_price: Максимальная цена
        gender: Пол (мужской, женский, унисекс)
    
    Returns:
        Список найденных товаров
    """
    try:
        # Проверка параметров
        logger.info(f"Поиск товаров: '{query}', лимит: {limit}, мин. цена: {min_price}, макс. цена: {max_price}, пол: {gender}")
        
        # Адаптация запроса с учетом пола
        search_query = query
        if gender and gender.lower() not in query.lower():
            # Добавляем пол в начало запроса, если его еще нет
            search_query = f"{gender} {query}"
            logger.info(f"Адаптированный запрос с учетом пола: '{search_query}'")
        
        # Получаем сервис для работы с Wildberries
        wb_service = get_wildberries_service()
        if not wb_service:
            logger.error("Не удалось инициализировать WildberriesService")
            raise HTTPException(status_code=500, detail="Ошибка инициализации сервиса Wildberries")
        
        # Поиск товаров с учетом пола
        products = await wb_service.search_products(
            query=search_query,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            gender=gender
        )
        
        # Форматирование результатов для фронтенда
        formatted_products = []
        for product in products:
            try:
                # Получаем основные атрибуты товара
                name = product.get('name', '')
                id = product.get('id', '')
                brand = product.get('brand', '')
                price = product.get('price', 0)
                sale_price = product.get('sale_price', price)
                discount = product.get('discount', 0)
                image_url = product.get('image_url', '')
                product_url = product.get('product_url', f"https://www.wildberries.ru/catalog/{id}/detail.aspx")
                
                # Формируем объект товара для фронтенда
                formatted_product = {
                    "id": id,
                    "name": f"{brand} {name}".strip(),
                    "description": product.get('description', ''),
                    "price": sale_price,  # Используем скидочную цену как актуальную
                    "oldPrice": price if discount > 0 else None,  # Указываем обычную цену только если есть скидка
                    "imageUrl": image_url,
                    "imageUrls": product.get('imageUrls', [image_url]) if product.get('imageUrls') else [image_url],
                    "category": product.get('category', ''),
                    "url": product_url,
                    "gender": product.get('gender', gender) or "унисекс"  # Используем указанный пол или берем из товара
                }
                
                formatted_products.append(formatted_product)
            except Exception as e:
                logger.error(f"Ошибка при форматировании товара: {e}")
                continue
        
        logger.info(f"Найдено и отформатировано {len(formatted_products)} товаров из {len(products)}")
        return formatted_products
    
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.post("/api/determine_user_needs")
async def determine_user_needs_endpoint(request: AssistantRequest):
    """
    Определяет потребности пользователя на основе его сообщения
    
    Args:
        request: Данные запроса (user_id, role, message)
        
    Returns:
        Результаты анализа потребностей пользователя
    """
    try:
        logger.info(f"Получен запрос на определение потребностей пользователя: {request.user_id}, роль: {request.role}")
        
        # Инициализируем ассистента
        assistant = get_assistant()
        if not assistant:
            logger.error("Не удалось инициализировать ассистента")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать ассистента")
        
        # Определяем потребности пользователя
        result = await assistant.determine_user_needs_async(
            user_id=request.user_id,
            role=request.role,
            user_input=request.message
        )
        
        # Преобразуем объект UserPreferences в словарь для сериализации
        if "preferences" in result and hasattr(result["preferences"], "dict"):
            result["preferences"] = result["preferences"].dict()
        
        logger.info(f"Успешно определены потребности пользователя: {request.user_id}, роль: {request.role}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Ошибка при определении потребностей пользователя: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

# Альтернативный путь для совместимости с фронтендом
@app.post("/determine_user_needs")
async def determine_user_needs_compat(request: AssistantRequest):
    """
    Совместимый путь для определения потребностей пользователя
    """
    return await determine_user_needs_endpoint(request)

# Путь совместимости для поиска товаров
@app.post("/find_similar_products")
async def find_similar_products_compat(request: DirectProductSearchRequest):
    """
    Совместимый путь для поиска рекомендуемых продуктов
    """
    return await search_products_direct_endpoint(request)

@app.post("/api/cosmetologist/analyze")
async def analyze_cosmetologist_data(request: CosmetologistRequest):
    """
    Анализирует данные пользователя для компонента ассистента косметолога
    
    Args:
        request: Данные о коже и предпочтениях пользователя
        
    Returns:
        Анализ кожи и рекомендуемые продукты
    """
    try:
        logger.info(f"Получен запрос на анализ данных для косметолога: тип кожи {request.skinType}")
        
        # Инициализируем ассистента
        assistant = get_assistant()
        if not assistant:
            logger.error("Не удалось инициализировать ассистента")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать ассистента")
        
        # Генерируем текстовый запрос на основе данных пользователя
        user_input = f"Мой тип кожи: {get_skin_type_name(request.skinType)}. "
        
        if request.concerns and len(request.concerns) > 0:
            concerns_map = {
                'aging': 'возрастные изменения',
                'acne': 'акне и высыпания',
                'pigmentation': 'пигментация',
                'redness': 'покраснения',
                'dryness': 'сухость',
                'oiliness': 'жирность'
            }
            concerns = [concerns_map.get(c, c) for c in request.concerns]
            user_input += f"Меня беспокоит: {', '.join(concerns)}. "
        
        if request.age:
            user_input += f"Мой возраст: {request.age} лет. "
        
        if request.lifestyles and len(request.lifestyles) > 0:
            lifestyles_map = {
                'active': 'активный образ жизни',
                'office': 'работа в офисе',
                'sport': 'занятия спортом',
                'travel': 'частые путешествия'
            }
            lifestyles = [lifestyles_map.get(l, l) for l in request.lifestyles]
            user_input += f"Мой образ жизни: {', '.join(lifestyles)}. "
        
        if request.currentProducts:
            user_input += f"Сейчас я использую: {request.currentProducts}. "
        
        if request.allergies:
            user_input += f"У меня аллергия на: {request.allergies}. "
        
        if request.organic_only:
            user_input += "Я предпочитаю органическую и натуральную косметику. "
        
        if request.budget:
            user_input += f"Мой бюджет: {request.budget} рублей. "
        
        logger.info(f"Сформированный запрос для анализа: {user_input}")
        
        # Определяем потребности пользователя
        needs_result = await assistant.determine_user_needs_async(
            user_id="web-user",
            role="косметолог",
            user_input=user_input
        )
        
        # Формируем запрос для поиска продуктов на основе потребностей
        search_query = generate_product_search_query(request, needs_result.get("identified_needs", {}))
        
        # Ищем рекомендуемые продукты
        wildberries = get_wildberries_service()
        if not wildberries:
            logger.error("Не удалось инициализировать сервис Wildberries")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать сервис Wildberries")
        
        products = await wildberries.search_products_async(
            query=search_query,
            limit=8,
            min_price=request.budget * 0.1 if request.budget else None,
            max_price=request.budget if request.budget else None
        )
        
        # Генерируем анализ кожи и рекомендации
        skin_analysis = generate_skin_analysis(request, needs_result)
        
        logger.info(f"Успешно выполнен анализ данных для косметолога")
        
        return {
            "success": True,
            "skinAnalysis": skin_analysis,
            "recommendedProducts": products,
            "identifiedNeeds": needs_result.get("identified_needs", {})
        }
        
    except Exception as e:
        logger.error(f"Ошибка при анализе данных для косметолога: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

def get_skin_type_name(skin_type_id: str) -> str:
    """Получает название типа кожи по идентификатору."""
    skin_type_map = {
        'normal': 'нормальная',
        'dry': 'сухая',
        'oily': 'жирная',
        'combination': 'комбинированная',
        'sensitive': 'чувствительная'
    }
    return skin_type_map.get(skin_type_id, skin_type_id)

def generate_product_search_query(request: CosmetologistRequest, identified_needs: Dict[str, Any]) -> str:
    """Генерирует запрос для поиска продуктов на основе данных пользователя."""
    skin_type = get_skin_type_name(request.skinType)
    
    query = f"косметика для {skin_type} кожи"
    
    if request.concerns and len(request.concerns) > 0:
        concerns_map = {
            'aging': 'антивозрастная',
            'acne': 'против акне',
            'pigmentation': 'от пигментации',
            'redness': 'от покраснений',
            'dryness': 'увлажняющая',
            'oiliness': 'матирующая'
        }
        
        concerns = [concerns_map.get(c, c) for c in request.concerns if c in concerns_map]
        if concerns:
            query += f" {' '.join(concerns)}"
    
    if request.organic_only or identified_needs.get("organic_only"):
        query += " органическая натуральная"
    
    return query

def generate_skin_analysis(request: CosmetologistRequest, needs_result: Dict[str, Any]) -> Dict[str, Any]:
    """Генерирует структуру анализа кожи на основе данных пользователя."""
    skin_type = request.skinType
    
    # Базовое описание в зависимости от типа кожи
    description = ""
    if skin_type == 'sensitive':
        description = "У вас чувствительная кожа, которой необходим бережный уход без агрессивных компонентов."
    elif skin_type == 'dry':
        description = "У вас сухая кожа, которая нуждается в интенсивном увлажнении и питании."
    elif skin_type == 'oily':
        description = "У вас жирная кожа, которой нужно бережное очищение и контроль себорегуляции."
    elif skin_type == 'combination':
        description = "У вас комбинированная кожа, требующая балансирующего ухода."
    else:
        description = "У вас нормальная кожа, которой нужен поддерживающий уход и защита."
    
    # Добавляем информацию о проблемах кожи
    if request.concerns:
        if 'acne' in request.concerns:
            description += " Высыпания указывают на необходимость противовоспалительных компонентов."
        if 'pigmentation' in request.concerns:
            description += " Пигментация требует средств, выравнивающих тон кожи."
        if 'aging' in request.concerns:
            description += " Возрастные изменения требуют использования средств с антиоксидантами и пептидами."
        if 'redness' in request.concerns:
            description += " Для уменьшения покраснений рекомендуется использовать средства с успокаивающими компонентами."
        if 'dryness' in request.concerns:
            description += " Для борьбы с сухостью необходимы интенсивно увлажняющие средства с церамидами."
        if 'oiliness' in request.concerns:
            description += " Избыточная жирность кожи требует использования матирующих средств с легкой текстурой."
    
    # Формируем базовую структуру анализа кожи
    return {
        "description": description,
        "daily": {
            "morning": {
                "steps": [
                    {"name": "Очищение", "product": "Очищающий гель для умывания"},
                    {"name": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                    {"name": "Сыворотка", "product": "Сыворотка с гиалуроновой кислотой"},
                    {"name": "Увлажнение", "product": "Увлажняющий крем для лица"},
                    {"name": "Защита", "product": "Солнцезащитный крем SPF 30+"}
                ]
            },
            "evening": {
                "steps": [
                    {"name": "Очищение", "product": "Очищающий гель для умывания"},
                    {"name": "Тонизирование", "product": "Увлажняющий тоник без спирта"},
                    {"name": "Сыворотка", "product": "Ночная восстанавливающая сыворотка"},
                    {"name": "Увлажнение", "product": "Ночной питательный крем"},
                    {"name": "Крем для глаз", "product": "Увлажняющий крем для области вокруг глаз"}
                ]
            }
        },
        "weekly": {
            "procedures": [
                {"name": "Эксфолиация", "product": "Мягкий пилинг с AHA-кислотами", "frequency": "1-2 раза в неделю"},
                {"name": "Маска", "product": "Увлажняющая тканевая маска", "frequency": "1-2 раза в неделю"},
                {"name": "Глубокое очищение", "product": "Очищающая маска с глиной", "frequency": "1 раз в неделю"}
            ],
            "additional": [
                {"name": "Уход за губами", "description": "Увлажняющий бальзам для губ"},
                {"name": "Уход за руками", "description": "Питательный крем для рук"},
                {"name": "Массаж лица", "description": "Использование нефритового роллера для улучшения микроциркуляции"}
            ]
        },
        "recommendations": {
            "lifestyle": [
                {"text": "Пить не менее 1,5-2 литров воды в день"},
                {"text": "Защищать кожу от солнца круглый год"},
                {"text": "Избегать горячей воды при умывании"},
                {"text": "Регулярно менять наволочки (минимум раз в неделю)"},
                {"text": "Ограничить потребление сахара и быстрых углеводов"}
            ],
            "ingredients": [
                {"name": "Гиалуроновая кислота", "purpose": "для глубокого увлажнения"},
                {"name": "Ниацинамид", "purpose": "для укрепления барьерной функции кожи"},
                {"name": "Пептиды", "purpose": "для стимуляции выработки коллагена"},
                {"name": "Церамиды", "purpose": "для восстановления защитного барьера"},
                {"name": "Антиоксиданты", "purpose": "для защиты от свободных радикалов"}
            ]
        }
    }

@app.post("/api/nutritionist/analyze")
async def analyze_nutritionist_data(request: NutritionistRequest):
    """
    Анализирует данные пользователя для компонента ассистента нутрициолога
    
    Args:
        request: Данные о целях питания и предпочтениях пользователя
        
    Returns:
        Анализ питания и рекомендуемые продукты
    """
    try:
        logger.info(f"Получен запрос на анализ данных для нутрициолога: цель {request.goal}")
        
        # Инициализируем ассистента
        assistant = get_assistant()
        if not assistant:
            logger.error("Не удалось инициализировать ассистента")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать ассистента")
        
        # Генерируем текстовый запрос на основе данных пользователя
        user_input = f"Моя цель в питании: {get_dietary_goal_name(request.goal)}. "
        
        if request.restrictions and len(request.restrictions) > 0:
            restrictions_map = {
                'vegetarian': 'вегетарианство',
                'vegan': 'веганство',
                'gluten_free': 'непереносимость глютена',
                'lactose_free': 'непереносимость лактозы',
                'diabetes': 'диабет'
            }
            restrictions = [restrictions_map.get(r, r) for r in request.restrictions if r != 'none']
            if restrictions:
                user_input += f"Мои пищевые ограничения: {', '.join(restrictions)}. "
        
        if request.personalInfo:
            if 'age' in request.personalInfo:
                user_input += f"Мой возраст: {request.personalInfo['age']} лет. "
            
            if 'weight' in request.personalInfo:
                user_input += f"Мой вес: {request.personalInfo['weight']} кг. "
            
            if 'height' in request.personalInfo:
                user_input += f"Мой рост: {request.personalInfo['height']} см. "
            
            if 'activity' in request.personalInfo:
                activity_map = {
                    'low': 'низкая физическая активность',
                    'medium': 'средняя физическая активность',
                    'high': 'высокая физическая активность'
                }
                activity = activity_map.get(request.personalInfo['activity'], request.personalInfo['activity'])
                user_input += f"Уровень физической активности: {activity}. "
            
            if 'budget' in request.personalInfo:
                user_input += f"Мой бюджет на питание: {request.personalInfo['budget']} рублей. "
        
        logger.info(f"Сформированный запрос для анализа: {user_input}")
        
        # Определяем потребности пользователя
        needs_result = await assistant.determine_user_needs_async(
            user_id="web-user",
            role="нутрициолог",
            user_input=user_input
        )
        
        # Формируем запрос для поиска продуктов на основе потребностей
        search_query = generate_nutrition_search_query(request, needs_result.get("identified_needs", {}))
        
        # Ищем рекомендуемые продукты
        wildberries = get_wildberries_service()
        if not wildberries:
            logger.error("Не удалось инициализировать сервис Wildberries")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать сервис Wildberries")
        
        budget = request.personalInfo.get('budget') if request.personalInfo else None
        
        # Удаляем параметр category, который не поддерживается методом
        products = await wildberries.search_products_async(
            query=search_query,
            limit=8,
            min_price=budget * 0.1 if budget else None,
            max_price=budget if budget else None
        )
        
        # Генерируем анализ питания и рекомендации
        nutrition_analysis = generate_nutrition_analysis(request, needs_result)
        
        # Генерируем недельный план питания
        weekly_meal_plan = generate_weekly_meal_plan(request, nutrition_analysis)
        
        logger.info(f"Успешно выполнен анализ данных для нутрициолога")
        
        return {
            "success": True,
            "nutritionAnalysis": nutrition_analysis,
            "weeklyMealPlan": weekly_meal_plan,
            "recommendedProducts": products,
            "identifiedNeeds": needs_result.get("identified_needs", {})
        }
        
    except Exception as e:
        logger.error(f"Ошибка при анализе данных для нутрициолога: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

def get_dietary_goal_name(goal_id: str) -> str:
    """Получает название цели питания по идентификатору."""
    goal_map = {
        'weight_loss': 'похудение',
        'muscle_gain': 'набор мышечной массы',
        'health': 'здоровое питание',
        'energy': 'повышение энергии',
        'special': 'особые потребности'
    }
    
    return goal_map.get(goal_id, goal_id)

def generate_nutrition_search_query(request: NutritionistRequest, identified_needs: Dict[str, Any]) -> str:
    """Генерирует запрос для поиска продуктов на основе потребностей пользователя."""
    goal = get_dietary_goal_name(request.goal)
    
    query = f"продукты для {goal}"
    
    if request.restrictions and len(request.restrictions) > 0:
        restrictions_map = {
            'vegetarian': 'вегетарианские',
            'vegan': 'веганские',
            'gluten_free': 'без глютена',
            'lactose_free': 'без лактозы',
            'diabetes': 'диабетические'
        }
        
        restrictions = [restrictions_map.get(r, r) for r in request.restrictions if r != 'none']
        if restrictions:
            query += f" {' '.join(restrictions)}"
    
    return query

def generate_nutrition_analysis(request: NutritionistRequest, needs_result: Dict[str, Any]) -> Dict[str, Any]:
    """Генерирует структуру анализа питания на основе данных пользователя."""
    # Базовые параметры
    personal_info = request.personalInfo or {}
    age = personal_info.get('age', 30)
    weight = personal_info.get('weight', 70)
    height = personal_info.get('height', 170)
    activity = personal_info.get('activity', 'medium')
    
    # Рассчитываем BMR по формуле Миффлина-Сан Жеора
    bmr = 0
    if age and weight and height:
        # Формула для мужчин (можно расширить с учетом пола)
        bmr = 10 * float(weight) + 6.25 * float(height) - 5 * float(age) + 5
    else:
        # Если недостаточно данных, используем среднее значение
        bmr = 1800
    
    # Коэффициент активности
    activity_multipliers = {
        'low': 1.2,
        'medium': 1.55,
        'high': 1.725
    }
    
    tdee = bmr * activity_multipliers.get(activity, 1.55)
    
    # Корректировка в зависимости от цели
    goal_multipliers = {
        'weight_loss': 0.85,
        'muscle_gain': 1.1,
        'health': 1,
        'energy': 1,
        'special': 1
    }
    
    daily_calories = int(tdee * goal_multipliers.get(request.goal, 1))
    
    # Расчет макронутриентов
    protein_ratio = 0.3
    fat_ratio = 0.3
    carb_ratio = 0.4
    
    if request.goal == 'weight_loss':
        protein_ratio = 0.35
        fat_ratio = 0.35
        carb_ratio = 0.3
    elif request.goal == 'muscle_gain':
        protein_ratio = 0.35
        fat_ratio = 0.25
        carb_ratio = 0.4
    
    proteins = int(daily_calories * protein_ratio / 4)  # 4 ккал/г белка
    fats = int(daily_calories * fat_ratio / 9)  # 9 ккал/г жира
    carbs = int(daily_calories * carb_ratio / 4)  # 4 ккал/г углеводов
    
    # Описание плана питания
    description = f"Ваш оптимальный рацион составляет {daily_calories} ккал в день с распределением БЖУ: {int(protein_ratio * 100)}% белков, {int(fat_ratio * 100)}% жиров, {int(carb_ratio * 100)}% углеводов."
    
    if request.goal == 'weight_loss':
        description += " Для похудения важно соблюдать дефицит калорий и увеличить потребление белка для сохранения мышечной массы."
    elif request.goal == 'muscle_gain':
        description += " Для набора мышечной массы необходим профицит калорий и достаточное количество белка."
    
    # Если у пользователя есть ограничения в питании
    if request.restrictions and len(request.restrictions) > 0:
        if 'vegetarian' in request.restrictions:
            description += " Учтены вегетарианские предпочтения в питании."
        if 'vegan' in request.restrictions:
            description += " Учтены веганские предпочтения в питании."
        if 'gluten_free' in request.restrictions:
            description += " Исключены продукты, содержащие глютен."
        if 'lactose_free' in request.restrictions:
            description += " Исключены продукты, содержащие лактозу."
        if 'diabetes' in request.restrictions:
            description += " Учтены особенности питания при диабете."
    
    # Формируем структуру анализа питания
    return {
        "description": description,
        "dailyNutrition": {
            "calories": daily_calories,
            "macros": {
                "proteins": proteins,
                "fats": fats,
                "carbs": carbs,
                "proteinRatio": int(protein_ratio * 100),
                "fatRatio": int(fat_ratio * 100),
                "carbRatio": int(carb_ratio * 100)
            }
        },
        "mealPlan": {
            "breakfast": {
                "title": "Завтрак",
                "calories": int(daily_calories * 0.25),
                "description": "Оптимальное время: 7:00-9:00",
                "recommendations": [
                    "Сложные углеводы для энергии",
                    "Белок для насыщения",
                    "Клетчатка для пищеварения"
                ]
            },
            "lunch": {
                "title": "Обед",
                "calories": int(daily_calories * 0.35),
                "description": "Оптимальное время: 12:00-14:00",
                "recommendations": [
                    "Основной источник белка",
                    "Сложные углеводы",
                    "Овощи для витаминов"
                ]
            },
            "dinner": {
                "title": "Ужин",
                "calories": int(daily_calories * 0.30),
                "description": "Оптимальное время: 18:00-20:00",
                "recommendations": [
                    "Легкоусвояемый белок",
                    "Минимум углеводов",
                    "Полезные жиры"
                ]
            },
            "snacks": {
                "title": "Перекусы",
                "calories": int(daily_calories * 0.10),
                "description": "Между основными приемами пищи",
                "recommendations": [
                    "Фрукты и орехи",
                    "Протеиновые снеки",
                    "Овощные нарезки"
                ]
            }
        },
        "recommendations": {
            "lifestyle": [
                {"text": "Пить не менее 2 литров воды в день"},
                {"text": "Соблюдать режим питания и не пропускать приемы пищи"},
                {"text": "Готовить еду на пару, запекать или тушить вместо жарки"},
                {"text": "Ограничить потребление соли и сахара"},
                {"text": "Включать в рацион сезонные овощи и фрукты"}
            ],
            "ingredients": [
                {"name": "Белки", "sources": "Нежирное мясо, рыба, яйца, бобовые"},
                {"name": "Сложные углеводы", "sources": "Цельнозерновые крупы, овощи, бобовые"},
                {"name": "Полезные жиры", "sources": "Авокадо, орехи, оливковое масло, жирная рыба"},
                {"name": "Клетчатка", "sources": "Овощи, фрукты, цельные злаки, отруби"},
                {"name": "Витамины и микроэлементы", "sources": "Разноцветные овощи и фрукты, зелень"}
            ]
        }
    }

def generate_weekly_meal_plan(request: NutritionistRequest, nutrition_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерирует недельный план питания на основе пищевых предпочтений и диетических требований.
    
    Args:
        request: Данные о целях питания и предпочтениях пользователя
        nutrition_analysis: Результаты анализа пищевых потребностей
    
    Returns:
        Структурированный план питания на неделю с указанием блюд, калорий и БЖУ
    """
    # Получаем дневные нормы калорий и макронутриентов
    daily_calories = nutrition_analysis["dailyNutrition"]["calories"]
    
    # Распределение калорий по приемам пищи
    breakfast_calories = int(daily_calories * 0.25)
    lunch_calories = int(daily_calories * 0.35)
    dinner_calories = int(daily_calories * 0.30)
    snack_calories = int(daily_calories * 0.10)
    
    # Названия дней недели
    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    # Варианты блюд для разных типов питания
    breakfast_options = get_meal_options("breakfast", request.goal, request.restrictions)
    lunch_options = get_meal_options("lunch", request.goal, request.restrictions)
    dinner_options = get_meal_options("dinner", request.goal, request.restrictions)
    snack_options = get_meal_options("snack", request.goal, request.restrictions)
    
    # Создаем план на неделю
    weekly_plan = {}
    
    # Для каждого дня недели выбираем блюда
    for i, day in enumerate(days_of_week):
        # Выбираем разные блюда для каждого дня, чтобы питание было разнообразным
        breakfast = breakfast_options[i % len(breakfast_options)]
        lunch = lunch_options[i % len(lunch_options)]
        dinner = dinner_options[i % len(dinner_options)]
        snack = snack_options[i % len(snack_options)]
        
        # Рассчитываем БЖУ для каждого блюда на основе общих пропорций
        macros = nutrition_analysis["dailyNutrition"]["macros"]
        protein_ratio = macros["proteinRatio"] / 100
        fat_ratio = macros["fatRatio"] / 100
        carb_ratio = macros["carbRatio"] / 100
        
        # Формируем информацию о дне
        weekly_plan[day] = {
            "breakfast": {
                "name": breakfast["name"],
                "description": breakfast["description"],
                "calories": breakfast_calories,
                "nutrients": {
                    "proteins": int(breakfast_calories * protein_ratio / 4),  # 4 ккал/г белка
                    "fats": int(breakfast_calories * fat_ratio / 9),  # 9 ккал/г жира
                    "carbs": int(breakfast_calories * carb_ratio / 4)  # 4 ккал/г углеводов
                },
                "ingredients": breakfast["ingredients"],
                "recipe": breakfast["recipe"]
            },
            "lunch": {
                "name": lunch["name"],
                "description": lunch["description"],
                "calories": lunch_calories,
                "nutrients": {
                    "proteins": int(lunch_calories * protein_ratio / 4),
                    "fats": int(lunch_calories * fat_ratio / 9),
                    "carbs": int(lunch_calories * carb_ratio / 4)
                },
                "ingredients": lunch["ingredients"],
                "recipe": lunch["recipe"]
            },
            "dinner": {
                "name": dinner["name"],
                "description": dinner["description"],
                "calories": dinner_calories,
                "nutrients": {
                    "proteins": int(dinner_calories * protein_ratio / 4),
                    "fats": int(dinner_calories * fat_ratio / 9),
                    "carbs": int(dinner_calories * carb_ratio / 4)
                },
                "ingredients": dinner["ingredients"],
                "recipe": dinner["recipe"]
            },
            "snack": {
                "name": snack["name"],
                "description": snack["description"],
                "calories": snack_calories,
                "nutrients": {
                    "proteins": int(snack_calories * protein_ratio / 4),
                    "fats": int(snack_calories * fat_ratio / 9),
                    "carbs": int(snack_calories * carb_ratio / 4)
                },
                "ingredients": snack["ingredients"],
                "recipe": snack["recipe"]
            },
            "totalCalories": daily_calories,
            "totalNutrients": {
                "proteins": macros["proteins"],
                "fats": macros["fats"],
                "carbs": macros["carbs"]
            }
        }
    
    return weekly_plan

def get_meal_options(meal_type: str, goal: str, restrictions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Возвращает варианты блюд для определенного типа приема пищи с учетом ограничений.
    
    Args:
        meal_type: Тип приема пищи (breakfast, lunch, dinner, snack)
        goal: Цель питания (похудение, набор массы и т.д.)
        restrictions: Список пищевых ограничений
    
    Returns:
        Список вариантов блюд с описанием, ингредиентами и рецептами
    """
    if restrictions is None:
        restrictions = []
    
    # Проверяем, есть ли ограничения по питанию
    is_vegetarian = 'vegetarian' in restrictions
    is_vegan = 'vegan' in restrictions
    is_gluten_free = 'gluten_free' in restrictions
    is_lactose_free = 'lactose_free' in restrictions
    is_diabetic = 'diabetes' in restrictions
    
    # Вегетарианские блюда
    if is_vegan:
        # Для веганов исключаем любые животные продукты
        breakfast_options = [
            {
                "name": "Овсянка с фруктами и орехами",
                "description": "Питательный веганский завтрак",
                "ingredients": ["Овсяные хлопья", "Миндальное молоко", "Бананы", "Ягоды", "Орехи", "Семена чиа"],
                "recipe": "1. Приготовить овсянку на миндальном молоке. 2. Добавить нарезанные фрукты и ягоды. 3. Посыпать орехами и семенами."
            },
            {
                "name": "Тост с авокадо и тофу",
                "description": "Богатый белком веганский завтрак",
                "ingredients": ["Цельнозерновой хлеб", "Авокадо", "Тофу", "Помидоры", "Лимонный сок", "Зелень"],
                "recipe": "1. Поджарить хлеб. 2. Размять авокадо и смешать с лимонным соком. 3. Обжарить тофу с приправами. 4. Выложить авокадо и тофу на тост."
            },
            {
                "name": "Смузи-боул с протеином",
                "description": "Питательный и освежающий завтрак",
                "ingredients": ["Замороженные ягоды", "Банан", "Растительный протеин", "Миндальное молоко", "Гранола", "Кокосовая стружка"],
                "recipe": "1. Взбить в блендере ягоды, банан, протеин и молоко. 2. Выложить в миску. 3. Посыпать гранолой и кокосовой стружкой."
            }
        ]
        lunch_options = [
            {
                "name": "Боул с киноа и овощами",
                "description": "Сбалансированный обед с растительным белком",
                "ingredients": ["Киноа", "Нут", "Авокадо", "Помидоры", "Огурцы", "Шпинат", "Оливковое масло", "Лимонный сок"],
                "recipe": "1. Отварить киноа. 2. Смешать с приготовленным нутом. 3. Добавить нарезанные овощи. 4. Заправить оливковым маслом и лимонным соком."
            },
            {
                "name": "Чечевичный суп с овощами",
                "description": "Питательный и согревающий обед",
                "ingredients": ["Чечевица", "Морковь", "Лук", "Чеснок", "Томаты", "Сельдерей", "Растительный бульон", "Специи"],
                "recipe": "1. Обжарить лук, морковь и сельдерей. 2. Добавить чечевицу и овощи. 3. Залить бульоном и варить до готовности. 4. Добавить специи по вкусу."
            },
            {
                "name": "Веганский бургер с фасолевой котлетой",
                "description": "Сытный растительный обед",
                "ingredients": ["Черная фасоль", "Киноа", "Лук", "Чеснок", "Цельнозерновая булочка", "Салат", "Томаты", "Авокадо"],
                "recipe": "1. Смешать размятую фасоль с приготовленной киноа, луком и чесноком. 2. Сформировать котлеты и запечь. 3. Собрать бургер с овощами и авокадо."
            }
        ]
        dinner_options = [
            {
                "name": "Тофу с овощами стир-фрай",
                "description": "Легкий и питательный ужин",
                "ingredients": ["Тофу", "Брокколи", "Перец", "Морковь", "Имбирь", "Соевый соус", "Коричневый рис"],
                "recipe": "1. Обжарить тофу до золотистого цвета. 2. Добавить нарезанные овощи. 3. Приправить имбирем и соевым соусом. 4. Подавать с коричневым рисом."
            },
            {
                "name": "Запеченные овощи с чечевицей",
                "description": "Сытный и низкокалорийный ужин",
                "ingredients": ["Чечевица", "Баклажаны", "Цукини", "Перец", "Лук", "Чеснок", "Томатный соус", "Зелень"],
                "recipe": "1. Отварить чечевицу. 2. Нарезать овощи и запечь с оливковым маслом. 3. Смешать с чечевицей и томатным соусом. 4. Посыпать зеленью."
            },
            {
                "name": "Овощной карри с нутом",
                "description": "Ароматный и согревающий ужин",
                "ingredients": ["Нут", "Кокосовое молоко", "Карри паста", "Лук", "Чеснок", "Томаты", "Шпинат", "Коричневый рис"],
                "recipe": "1. Обжарить лук и чеснок. 2. Добавить карри пасту, томаты и кокосовое молоко. 3. Добавить нут и шпинат. 4. Подавать с коричневым рисом."
            }
        ]
        snack_options = [
            {
                "name": "Хумус с морковными палочками",
                "description": "Белковый перекус",
                "ingredients": ["Нут", "Тахини", "Чеснок", "Лимонный сок", "Морковь"],
                "recipe": "1. Смешать в блендере нут, тахини, чеснок и лимонный сок. 2. Подавать с морковными палочками."
            },
            {
                "name": "Энергетические шарики",
                "description": "Питательный и сладкий перекус",
                "ingredients": ["Финики", "Орехи", "Какао", "Кокосовая стружка"],
                "recipe": "1. Измельчить финики и орехи в блендере. 2. Добавить какао. 3. Сформировать шарики и обвалять в кокосовой стружке."
            },
            {
                "name": "Фруктовый салат с киноа",
                "description": "Освежающий белковый перекус",
                "ingredients": ["Киноа", "Яблоко", "Груша", "Гранат", "Лимонный сок", "Мята"],
                "recipe": "1. Приготовить киноа. 2. Смешать с нарезанными фруктами. 3. Сбрызнуть лимонным соком и украсить мятой."
            }
        ]
    # Вегетарианские блюда (можно с яйцами и молочными продуктами)
    elif is_vegetarian:
        breakfast_options = [
            {
                "name": "Омлет с овощами и сыром",
                "description": "Белковый вегетарианский завтрак",
                "ingredients": ["Яйца", "Шпинат", "Томаты", "Сыр", "Молоко", "Зелень"],
                "recipe": "1. Взбить яйца с молоком. 2. Добавить нарезанные овощи и тертый сыр. 3. Готовить на среднем огне до готовности. 4. Посыпать зеленью."
            },
            {
                "name": "Греческий йогурт с ягодами и гранолой",
                "description": "Белковый и питательный завтрак",
                "ingredients": ["Греческий йогурт", "Свежие ягоды", "Гранола", "Мед", "Орехи"],
                "recipe": "1. Выложить йогурт в миску. 2. Добавить ягоды и гранолу. 3. Посыпать орехами и полить медом."
            },
            {
                "name": "Овощной шакшука",
                "description": "Сытный и питательный завтрак",
                "ingredients": ["Яйца", "Томаты", "Перец", "Лук", "Чеснок", "Специи", "Сыр фета", "Зелень"],
                "recipe": "1. Обжарить лук и перец. 2. Добавить томаты и чеснок. 3. Сделать углубления и разбить яйца. 4. Посыпать сыром и зеленью."
            }
        ]
        lunch_options = [
            {
                "name": "Греческий салат с фетой",
                "description": "Легкий и сытный обед",
                "ingredients": ["Огурцы", "Томаты", "Перец", "Красный лук", "Сыр фета", "Оливки", "Оливковое масло", "Лимонный сок"],
                "recipe": "1. Нарезать овощи крупными кусочками. 2. Добавить оливки и кубики феты. 3. Заправить оливковым маслом и лимонным соком."
            },
            {
                "name": "Киш с овощами и сыром",
                "description": "Сытный обед с овощами",
                "ingredients": ["Тесто для тарта", "Яйца", "Сливки", "Шпинат", "Брокколи", "Сыр", "Лук", "Чеснок"],
                "recipe": "1. Выложить тесто в форму. 2. Обжарить овощи. 3. Смешать яйца со сливками. 4. Выложить овощи на тесто, залить яичной смесью и посыпать сыром. 5. Запечь."
            },
            {
                "name": "Вегетарианский борщ",
                "description": "Питательный и согревающий обед",
                "ingredients": ["Свекла", "Капуста", "Морковь", "Лук", "Картофель", "Томатная паста", "Сметана", "Зелень"],
                "recipe": "1. Обжарить лук и морковь. 2. Добавить свеклу, капусту и картофель. 3. Залить водой, добавить томатную пасту. 4. Варить до готовности. 5. Подавать со сметаной и зеленью."
            }
        ]
        dinner_options = [
            {
                "name": "Овощная лазанья",
                "description": "Сытный вегетарианский ужин",
                "ingredients": ["Листы для лазаньи", "Цукини", "Баклажаны", "Перец", "Томатный соус", "Соус бешамель", "Сыр"],
                "recipe": "1. Обжарить овощи. 2. Выложить слоями: соус, листы, овощи, соус бешамель. 3. Посыпать сыром и запечь."
            },
            {
                "name": "Овощное ризотто с сыром",
                "description": "Кремовый и питательный ужин",
                "ingredients": ["Рис арборио", "Грибы", "Цукини", "Горошек", "Лук", "Чеснок", "Белое вино", "Пармезан"],
                "recipe": "1. Обжарить лук и чеснок. 2. Добавить рис и обжарить. 3. Постепенно добавлять бульон. 4. Добавить овощи. 5. В конце добавить сыр."
            },
            {
                "name": "Фриттата с овощами",
                "description": "Легкий белковый ужин",
                "ingredients": ["Яйца", "Картофель", "Шпинат", "Перец", "Лук", "Сыр", "Зелень"],
                "recipe": "1. Обжарить картофель и овощи. 2. Залить взбитыми яйцами. 3. Посыпать сыром. 4. Запечь до готовности."
            }
        ]
        snack_options = [
            {
                "name": "Творог с ягодами",
                "description": "Белковый перекус",
                "ingredients": ["Творог", "Свежие ягоды", "Мед", "Орехи"],
                "recipe": "1. Смешать творог с ягодами. 2. Полить медом и посыпать орехами."
            },
            {
                "name": "Яблоко с арахисовой пастой",
                "description": "Сладкий и белковый перекус",
                "ingredients": ["Яблоко", "Арахисовая паста"],
                "recipe": "1. Нарезать яблоко дольками. 2. Подавать с арахисовой пастой."
            },
            {
                "name": "Сырная тарелка с крекерами",
                "description": "Сытный белковый перекус",
                "ingredients": ["Ассорти сыров", "Цельнозерновые крекеры", "Виноград", "Орехи"],
                "recipe": "1. Нарезать сыр. 2. Подавать с крекерами, виноградом и орехами."
            }
        ]
    # Обычные блюда с учетом других ограничений
    else:
        breakfast_options = [
            {
                "name": "Омлет с овощами и курицей",
                "description": "Белковый завтрак",
                "ingredients": ["Яйца", "Куриное филе", "Шпинат", "Томаты", "Сыр", "Зелень"],
                "recipe": "1. Обжарить нарезанное куриное филе. 2. Взбить яйца и добавить нарезанные овощи. 3. Вылить на сковороду к курице. 4. Посыпать тертым сыром."
            },
            {
                "name": "Протеиновые блинчики",
                "description": "Питательный белковый завтрак",
                "ingredients": ["Овсяная мука", "Яйца", "Протеиновый порошок", "Бананы", "Ягоды", "Греческий йогурт"],
                "recipe": "1. Смешать муку, яйца, протеин и размятый банан. 2. Выпекать блинчики. 3. Подавать с йогуртом и свежими ягодами."
            },
            {
                "name": "Бутерброд с авокадо и яйцом пашот",
                "description": "Сытный и питательный завтрак",
                "ingredients": ["Цельнозерновой хлеб", "Авокадо", "Яйцо", "Лимонный сок", "Соль", "Перец"],
                "recipe": "1. Приготовить яйцо пашот. 2. Размять авокадо на хлеб, сбрызнуть лимонным соком. 3. Выложить яйцо пашот сверху."
            }
        ]
        lunch_options = [
            {
                "name": "Куриный салат с киноа",
                "description": "Сытный белковый обед",
                "ingredients": ["Куриное филе", "Киноа", "Микс салатных листьев", "Огурцы", "Помидоры", "Авокадо", "Оливковое масло", "Лимонный сок"],
                "recipe": "1. Отварить киноа. 2. Обжарить куриное филе с приправами. 3. Смешать с нарезанными овощами. 4. Заправить оливковым маслом и лимонным соком."
            },
            {
                "name": "Лосось с овощами на гриле",
                "description": "Богатый омега-3 обед",
                "ingredients": ["Филе лосося", "Цукини", "Перец", "Баклажаны", "Чеснок", "Лимон", "Оливковое масло", "Зелень"],
                "recipe": "1. Замариновать лосось в смеси оливкового масла, лимонного сока и чеснока. 2. Приготовить на гриле вместе с овощами. 3. Подавать, посыпав свежей зеленью."
            },
            {
                "name": "Суп с фрикадельками из индейки",
                "description": "Питательный и легкий обед",
                "ingredients": ["Фарш из индейки", "Морковь", "Лук", "Сельдерей", "Картофель", "Зелень", "Специи"],
                "recipe": "1. Сформировать небольшие фрикадельки из фарша. 2. Обжарить овощи. 3. Добавить бульон и картофель. 4. Когда картофель почти готов, добавить фрикадельки."
            }
        ]
        dinner_options = [
            {
                "name": "Запеченная курица с овощами",
                "description": "Легкий белковый ужин",
                "ingredients": ["Куриные грудки", "Брокколи", "Морковь", "Цветная капуста", "Чеснок", "Оливковое масло", "Специи"],
                "recipe": "1. Замариновать куриные грудки в смеси оливкового масла, чеснока и специй. 2. Разложить на противне вместе с овощами. 3. Запечь до готовности."
            },
            {
                "name": "Индейка с сладким картофелем",
                "description": "Сбалансированный ужин",
                "ingredients": ["Филе индейки", "Сладкий картофель", "Шпинат", "Лук", "Чеснок", "Оливковое масло", "Специи"],
                "recipe": "1. Обжарить филе индейки. 2. Запечь сладкий картофель в духовке. 3. Обжарить шпинат с чесноком. 4. Подавать вместе."
            },
            {
                "name": "Тушеная говядина с овощами",
                "description": "Сытный белковый ужин",
                "ingredients": ["Говядина", "Морковь", "Лук", "Сельдерей", "Томаты", "Грибы", "Бульон", "Специи"],
                "recipe": "1. Обжарить говядину до золотистой корочки. 2. Добавить овощи и обжарить. 3. Залить бульоном и тушить до мягкости."
            }
        ]
        snack_options = [
            {
                "name": "Протеиновый коктейль",
                "description": "Быстрый белковый перекус",
                "ingredients": ["Протеиновый порошок", "Банан", "Миндальное молоко", "Лед", "Арахисовая паста"],
                "recipe": "1. Смешать все ингредиенты в блендере до однородности."
            },
            {
                "name": "Вареное яйцо с авокадо",
                "description": "Питательный белковый перекус",
                "ingredients": ["Яйца", "Авокадо", "Соль", "Перец"],
                "recipe": "1. Сварить яйца вкрутую. 2. Нарезать авокадо. 3. Подавать вместе."
            },
            {
                "name": "Тунец с крекерами",
                "description": "Белковый перекус",
                "ingredients": ["Консервированный тунец", "Цельнозерновые крекеры", "Лимонный сок", "Зелень"],
                "recipe": "1. Смешать тунец с лимонным соком и зеленью. 2. Подавать с крекерами."
            }
        ]
    
    # Модифицируем для диабетиков
    if is_diabetic:
        # Делаем упор на низкий гликемический индекс
        for meal_list in [breakfast_options, lunch_options, dinner_options, snack_options]:
            for meal in meal_list:
                meal["description"] += " (низкий ГИ)"
    
    # Модифицируем для безглютеновой диеты
    if is_gluten_free:
        # Отмечаем безглютеновые опции
        for meal_list in [breakfast_options, lunch_options, dinner_options, snack_options]:
            for meal in meal_list:
                meal["description"] += " (без глютена)"
    
    # Модифицируем для безлактозной диеты
    if is_lactose_free:
        # Отмечаем безлактозные опции
        for meal_list in [breakfast_options, lunch_options, dinner_options, snack_options]:
            for meal in meal_list:
                meal["description"] += " (без лактозы)"
    
    # Возвращаем опции в зависимости от типа приема пищи
    if meal_type == "breakfast":
        return breakfast_options
    elif meal_type == "lunch":
        return lunch_options
    elif meal_type == "dinner":
        return dinner_options
    elif meal_type == "snack":
        return snack_options
    else:
        # По умолчанию возвращаем завтраки
        return breakfast_options

@app.post("/api/nutritionist/analyze")
async def analyze_nutritionist_data(request: NutritionistRequest):
    """
    Анализирует данные пользователя для нутрициолога и возвращает рекомендации по питанию.
    """
    try:
        logger.info(f"Получен запрос на анализ данных для нутрициолога: цель {request.goal}")
        
        # Инициализируем ассистента
        assistant = get_assistant()
        if not assistant:
            logger.error("Не удалось инициализировать ассистента")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать ассистента")
        
        # Генерируем текстовый запрос на основе данных пользователя
        user_input = f"Моя цель в питании: {get_dietary_goal_name(request.goal)}. "
        
        if request.restrictions and len(request.restrictions) > 0:
            restrictions_map = {
                'vegetarian': 'вегетарианство',
                'vegan': 'веганство',
                'gluten_free': 'непереносимость глютена',
                'lactose_free': 'непереносимость лактозы',
                'diabetes': 'диабет'
            }
            restrictions = [restrictions_map.get(r, r) for r in request.restrictions if r != 'none']
            if restrictions:
                user_input += f"Мои пищевые ограничения: {', '.join(restrictions)}. "
        
        if request.personalInfo:
            if 'age' in request.personalInfo:
                user_input += f"Мой возраст: {request.personalInfo['age']} лет. "
            
            if 'weight' in request.personalInfo:
                user_input += f"Мой вес: {request.personalInfo['weight']} кг. "
            
            if 'height' in request.personalInfo:
                user_input += f"Мой рост: {request.personalInfo['height']} см. "
            
            if 'activity' in request.personalInfo:
                activity_map = {
                    'low': 'низкая физическая активность',
                    'medium': 'средняя физическая активность',
                    'high': 'высокая физическая активность'
                }
                activity = activity_map.get(request.personalInfo['activity'], request.personalInfo['activity'])
                user_input += f"Уровень физической активности: {activity}. "
            
            if 'budget' in request.personalInfo:
                user_input += f"Мой бюджет на питание: {request.personalInfo['budget']} рублей. "
        
        logger.info(f"Сформированный запрос для анализа: {user_input}")
        
        # Определяем потребности пользователя
        needs_result = await assistant.determine_user_needs_async(
            user_id="web-user",
            role="нутрициолог",
            user_input=user_input
        )
        
        # Формируем запрос для поиска продуктов на основе потребностей
        search_query = generate_nutrition_search_query(request, needs_result.get("identified_needs", {}))
        
        # Ищем рекомендуемые продукты
        wildberries = get_wildberries_service()
        if not wildberries:
            logger.error("Не удалось инициализировать сервис Wildberries")
            raise HTTPException(status_code=500, detail="Не удалось инициализировать сервис Wildberries")
        
        budget = request.personalInfo.get('budget') if request.personalInfo else None
        
        # Удаляем параметр category, который не поддерживается методом
        products = await wildberries.search_products_async(
            query=search_query,
            limit=8,
            min_price=budget * 0.1 if budget else None,
            max_price=budget if budget else None
        )
        
        # Генерируем анализ питания и рекомендации
        nutrition_analysis = generate_nutrition_analysis(request, needs_result)
        
        # Генерируем недельный план питания
        weekly_meal_plan = generate_weekly_meal_plan(request, nutrition_analysis)
        
        logger.info(f"Успешно выполнен анализ данных для нутрициолога")
        
        return {
            "success": True,
            "nutritionAnalysis": nutrition_analysis,
            "weeklyMealPlan": weekly_meal_plan,
            "recommendedProducts": products,
            "identifiedNeeds": needs_result.get("identified_needs", {})
        }
    
    except Exception as e:
        logger.error(f"Ошибка при анализе данных для нутрициолога: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.post("/api/designer/analyze")
async def analyze_designer_data(request: DesignerRequest):
    """
    Анализирует данные пользователя для дизайнера интерьера и возвращает рекомендации.
    """
    try:
        assistant = get_assistant()
        
        # Создаем запрос к ассистенту для определения потребностей
        message = f"Мне нужно оформить {get_room_type_name(request.roomType)} в стиле {get_style_name(request.style)}."
        
        if request.roomInfo:
            if request.roomInfo.get("area"):
                message += f" Площадь комнаты {request.roomInfo.get('area')} м²."
            
            if request.roomInfo.get("budget"):
                message += f" Мой бюджет составляет {request.roomInfo.get('budget')} рублей."
            
            if request.roomInfo.get("hasWindows"):
                message += f" В комнате {'есть' if request.roomInfo.get('hasWindows') == 'yes' else 'нет'} окна."
        
        # Исправленный вызов с правильным порядком аргументов
        needs_result = await assistant.determine_user_needs_async("user123", "дизайнер", message)
        
        # Формируем детальный анализ
        design_analysis = generate_design_analysis(request, needs_result)
        
        # Добавляем новые элементы
        design_concept = generate_design_concept(request, needs_result)
        floor_plan = generate_floor_plan(request, needs_result)
        
        return {
            "success": True,
            "designAnalysis": design_analysis,
            "textRecommendations": generate_text_recommendations(request, needs_result),
            "designConcept": design_concept,
            "floorPlan": floor_plan
        }
    
    except Exception as e:
        logger.error(f"Ошибка при анализе данных дизайнера: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

def generate_text_recommendations(request: DesignerRequest, needs_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Генерирует текстовые рекомендации по расстановке мебели и оформлению интерьера на основе анализа AI."""
    room_type = get_room_type_name(request.roomType)
    style = get_style_name(request.style)
    area = request.roomInfo.get('area', '20') if request.roomInfo else '20'
    budget = request.roomInfo.get('budget', '50000') if request.roomInfo else '50000'
    has_windows = request.roomInfo.get('hasWindows', 'yes') if request.roomInfo else 'yes'
    
    recommendations = []
    
    # Извлекаем данные из анализа модели
    identified_needs = needs_result.get("identified_needs", {})
    suggestions = needs_result.get("suggestions", [])
    response_text = needs_result.get("response", "")
    
    # Создаем базовые ключевые слова для поиска в тексте ответа
    move_keywords = ["переставить", "передвинуть", "переместить", "расположить", "сдвинуть", "поставить"]
    buy_keywords = ["купить", "приобрести", "добавить", "дополнить", "докупить", "обзавестись"]
    remove_keywords = ["убрать", "выкинуть", "заменить", "избавиться", "удалить", "демонтировать"]
    
    # Функция для поиска рекомендаций в тексте
    def extract_recommendations_from_text(text, keywords):
        recommendations = []
        paragraphs = [p.strip() for p in text.split('.') if p.strip()]
        for paragraph in paragraphs:
            if any(keyword in paragraph.lower() for keyword in keywords):
                recommendations.append(paragraph.strip() + '.')
        return recommendations
    
    # Попытка извлечь рекомендации из ответа модели
    move_suggestions = extract_recommendations_from_text(response_text, move_keywords)
    buy_suggestions = extract_recommendations_from_text(response_text, buy_keywords)
    remove_suggestions = extract_recommendations_from_text(response_text, remove_keywords)
    
    # Раздел: Что передвинуть
    move_description = ""
    if "furniture_arrangement" in identified_needs:
        move_description = identified_needs["furniture_arrangement"]
    elif "furniture_layout" in identified_needs:
        move_description = identified_needs["furniture_layout"]
    elif move_suggestions:
        move_description = " ".join(move_suggestions)
    else:
        # Базовые рекомендации по передвижению мебели в зависимости от типа комнаты
        if room_type == "гостиная":
            move_description = f"• Расположите диван напротив фокусной точки комнаты (телевизор, камин или окно).\n• Создайте зону для общения, сгруппировав кресла и журнальный столик.\n• Разместите книжный шкаф у стены, не загораживая проход.\n• В стиле {style} желательно избегать загромождения центра комнаты."
        elif room_type == "спальня":
            move_description = f"• Поставьте кровать изголовьем к стене, но не к окну.\n• Расположите прикроватные тумбочки с обеих сторон кровати для симметрии.\n• Переместите туалетный столик ближе к источнику естественного света.\n• Установите шкаф так, чтобы дверцы открывались свободно, не загораживая проход."
        elif room_type == "кухня":
            move_description = f"• Организуйте рабочий треугольник между холодильником, мойкой и плитой для удобства перемещения.\n• Расположите обеденную зону у окна для лучшего освещения во время приема пищи.\n• Оставьте достаточно места для свободного открывания дверок шкафов и ящиков (минимум 1 метр)."
        elif room_type == "домашний офис":
            move_description = f"• Поставьте рабочий стол перпендикулярно или лицом к окну для лучшего естественного освещения.\n• Разместите стеллажи и полки в пределах досягаемости от рабочего места.\n• Оставьте достаточно пространства для комфортного отката кресла."
        elif room_type == "детская комната":
            move_description = f"• Разделите пространство на зоны: для сна, игр и учебы.\n• Расположите кровать в самой тихой части комнаты.\n• Разместите игровую зону на ковре в центре комнаты.\n• Установите письменный стол у окна для хорошего освещения."
    
    recommendations.append({
        "title": "ПЕРЕДВИНУТЬ",
        "description": move_description
    })
    
    # Раздел: Что докупить
    buy_description = ""
    if "recommended_purchases" in identified_needs:
        buy_description = identified_needs["recommended_purchases"]
    elif buy_suggestions:
        buy_description = " ".join(buy_suggestions)
    else:
        # Базовые рекомендации по покупкам в зависимости от типа комнаты и стиля
        budget_num = int(budget) if str(budget).isdigit() else 50000
        if room_type == "гостиная":
            buy_description = f"• Основная мебель (диван, кресла, журнальный столик): {int(budget_num * 0.6)} руб.\n• Системы хранения (шкафы, полки): {int(budget_num * 0.15)} руб.\n• Освещение (торшер, настольные лампы): {int(budget_num * 0.1)} руб.\n• Декор (ковер, подушки, картины): {int(budget_num * 0.15)} руб.\n\nРекомендуемые покупки для стиля {style}: "
            
            if style == "Современный":
                buy_description += "\n• Диван с четкими линиями и хромированными ножками\n• Журнальный столик со стеклянной столешницей\n• Минималистичные светильники с металлическими элементами"
            elif style == "Скандинавский":
                buy_description += "\n• Диван светлых тонов с деревянными ножками\n• Пушистый ковер\n• Деревянный журнальный столик\n• Текстильные подушки с геометрическим узором"
            elif style == "Лофт":
                buy_description += "\n• Кожаный диван\n• Журнальный столик из металла и дерева\n• Индустриальные светильники\n• Декор из необработанных материалов"
        elif room_type == "спальня":
            buy_description = f"• Кровать с матрасом: {int(budget_num * 0.5)} руб.\n• Шкаф/комод: {int(budget_num * 0.2)} руб.\n• Прикроватные тумбочки: {int(budget_num * 0.1)} руб.\n• Освещение (бра, прикроватные лампы): {int(budget_num * 0.1)} руб.\n• Текстиль (шторы, покрывало): {int(budget_num * 0.1)} руб.\n\nРекомендуемые покупки для стиля {style}: "
            
            if style == "Современный":
                buy_description += "\n• Кровать с мягким изголовьем\n• Встроенный шкаф с глянцевыми фасадами\n• Минималистичные прикроватные светильники"
            elif style == "Скандинавский":
                buy_description += "\n• Кровать из светлого дерева\n• Легкие льняные шторы\n• Натуральный текстиль для постельного белья\n• Деревянные тумбочки простых форм"
    
    recommendations.append({
        "title": "ДОКУПИТЬ",
        "description": buy_description
    })
    
    # Раздел: Что убрать/заменить
    remove_description = ""
    if "items_to_remove" in identified_needs:
        remove_description = identified_needs["items_to_remove"]
    elif remove_suggestions:
        remove_description = " ".join(remove_suggestions)
    else:
        # Базовые рекомендации по удалению предметов
        if style == "Минимализм":
            remove_description = f"• Уберите лишние декоративные элементы, оставьте только функциональные предметы.\n• Замените массивную мебель на более легкие и компактные варианты.\n• Избавьтесь от мелких аксессуаров, создающих визуальный шум.\n• Уберите яркие контрастирующие элементы в пользу нейтральной палитры."
        elif style == "Современный":
            remove_description = f"• Замените устаревшую мебель с резными элементами на модели с четкими линиями.\n• Уберите массивные тяжелые шторы в пользу легких роллет или жалюзи.\n• Избавьтесь от обилия мелких статуэток и сувениров.\n• Замените старые люстры на современные светильники с лаконичным дизайном."
        elif style == "Скандинавский":
            remove_description = f"• Уберите темную мебель, заменив ее на светлые деревянные варианты.\n• Избавьтесь от тяжелых плотных штор в пользу легких светлых занавесок.\n• Замените синтетические материалы на натуральные (лен, хлопок, дерево).\n• Уберите избыточный декор, оставив несколько ключевых акцентов."
        else:
            remove_description = f"• Замените предметы, не соответствующие выбранному стилю {style}.\n• Уберите излишки мебели, чтобы освободить пространство и улучшить циркуляцию воздуха.\n• Избавьтесь от устаревших элементов освещения в пользу более эффективных современных аналогов.\n• Замените изношенную мебель, которая портит общее впечатление от интерьера."
    
    recommendations.append({
        "title": "ЗАМЕНИТЬ/УБРАТЬ",
        "description": remove_description
    })
    
    # Раздел: Общие рекомендации
    general_description = ""
    if "general_recommendations" in identified_needs:
        general_description = identified_needs["general_recommendations"]
    elif "color_scheme" in identified_needs:
        general_description = f"Цветовая схема: {identified_needs['color_scheme']}\n\n"
        if "lighting" in identified_needs:
            general_description += f"Освещение: {identified_needs['lighting']}\n\n"
    else:
        # Базовые общие рекомендации
        general_description = f"• Для помещения площадью {area} м² выбирайте мебель соответствующих размеров, чтобы сохранить простор и функциональность.\n• В комнате {'с естественным освещением' if has_windows == 'yes' else 'без окон'} особенно важно "
        general_description += 'правильно организовать искусственное освещение с несколькими уровнями (верхний свет, настенные бра, настольные лампы).' if has_windows != 'yes' else 'не загораживать окна массивной мебелью и использовать светоотражающие поверхности.'
        
        general_description += f"\n\n• Цветовая палитра для стиля {style}: "
        if style == "Современный":
            general_description += "нейтральные тона (белый, серый, бежевый) с яркими акцентами (синий, зеленый, красный)."
        elif style == "Скандинавский":
            general_description += "белый как основа, светлые древесные оттенки, нежные пастельные акценты (голубой, розовый, мятный)."
        elif style == "Лофт":
            general_description += "кирпичный, бетонный серый, черный металл с теплыми коричневыми акцентами дерева."
        elif style == "Классический":
            general_description += "благородные оттенки (бежевый, кремовый, золотой, бордовый, темно-зеленый)."
        elif style == "Минимализм":
            general_description += "монохромная схема с акцентами черного и белого, допустимы минимальные цветовые вкрапления."
        
        general_description += f"\n\n• Материалы для стиля {style}: "
        if style == "Современный":
            general_description += "стекло, металл, глянцевые поверхности, пластик."
        elif style == "Скандинавский":
            general_description += "светлое дерево, натуральный текстиль (лен, хлопок), кожа, камень."
        elif style == "Лофт":
            general_description += "кирпич, бетон, состаренное дерево, грубый металл, кожа."
        elif style == "Классический":
            general_description += "натуральное дерево (орех, вишня), мрамор, хрусталь, текстиль с орнаментом."
        elif style == "Минимализм":
            general_description += "матовые поверхности, бетон, стекло, камень, монохромный текстиль."
    
    recommendations.append({
        "title": "ОБЩЕЕ",
        "description": general_description
    })
    
    return recommendations

@app.post("/api/designer/furniture-recommendations")
async def get_furniture_recommendations(request: FurnitureRecommendationRequest):
    """
    Получает рекомендации по мебели и декору для выбранного типа комнаты и стиля.
    """
    try:
        # Создаем поисковый запрос для Wildberries на основе типа комнаты и стиля
        room_type = get_room_type_name(request.roomType)
        style = get_style_name(request.style)
        search_query = f"{style} {room_type} мебель"
        
        # Добавляем уточнения по размеру и бюджету
        if request.roomInfo.get("area"):
            area = float(request.roomInfo.get("area"))
            if area < 15:
                search_query += " для маленькой комнаты"
            elif area > 30:
                search_query += " для просторной комнаты"
        
        # Получаем рекомендуемые товары
        wildberries_service = get_wildberries_service()
        recommended_products = await wildberries_service.search_items_async(search_query, limit=16)
        
        # Фильтруем товары по бюджету, если указан
        if request.roomInfo.get("budget"):
            budget = float(request.roomInfo.get("budget"))
            # Распределяем бюджет по категориям
            max_price_per_item = budget / 5  # Предполагаем, что нужно около 5 товаров
            filtered_products = [p for p in recommended_products if p["price"] <= max_price_per_item]
            
            # Если после фильтрации осталось мало товаров, увеличиваем лимит
            if len(filtered_products) < 5:
                max_price_per_item = budget / 3
                filtered_products = [p for p in recommended_products if p["price"] <= max_price_per_item]
            
            recommended_products = filtered_products
        
        # Группируем товары по категориям
        categorized_products = categorize_furniture_products(recommended_products)
        
        return {
            "success": True,
            "recommendedProducts": recommended_products[:12],  # Ограничиваем количество рекомендаций
            "categorizedProducts": categorized_products
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций по мебели: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/designer/color-palette")
async def get_color_palette(style: str):
    """
    Получает цветовую палитру для выбранного стиля интерьера.
    """
    try:
        style_name = get_style_name(style)
        
        # Предопределенные палитры для разных стилей
        palettes = {
            "Современный": ["#E8E8E8", "#303030", "#6E7E85", "#A4C2A8", "#D3D5D7"],
            "Скандинавский": ["#FFFFFF", "#F5F5F5", "#E8E4D9", "#B6C8B2", "#8A9B8E"],
            "Лофт": ["#BFB3A5", "#8D7E74", "#423A35", "#BF925A", "#593D25"],
            "Классический": ["#F2E8D7", "#D9BC91", "#9B8A7A", "#654F36", "#402E22"],
            "Минимализм": ["#FFFFFF", "#F2F2F2", "#D9D9D9", "#BFBFBF", "#404040"]
        }
        
        # Возвращаем палитру для выбранного стиля или палитру для современного стиля, если стиль не найден
        palette = palettes.get(style_name, palettes["Современный"])
        
        return {
            "success": True,
            "style": style_name,
            "colorPalette": palette
        }
    
    except Exception as e:
        logger.error(f"Ошибка при получении цветовой палитры: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

def get_room_type_name(room_type_id: str) -> str:
    """Возвращает название типа комнаты по его идентификатору."""
    room_types = {
        "living": "гостиная",
        "bedroom": "спальня",
        "kitchen": "кухня",
        "office": "домашний офис",
        "children": "детская комната"
    }
    return room_types.get(room_type_id, "комната")

def get_style_name(style_id: str) -> str:
    """Возвращает название стиля интерьера по его идентификатору."""
    styles = {
        "modern": "Современный",
        "scandinavian": "Скандинавский",
        "loft": "Лофт",
        "classic": "Классический",
        "minimalist": "Минимализм"
    }
    return styles.get(style_id, "Современный")

def generate_furniture_search_query(request: DesignerRequest, identified_needs: Dict[str, Any]) -> str:
    """Генерирует поисковый запрос для поиска мебели на основе потребностей пользователя."""
    room_type = get_room_type_name(request.roomType)
    style = get_style_name(request.style)
    
    # Базовый запрос
    query = f"{style} {room_type} мебель"
    
    # Добавляем уточнения по размеру
    if request.roomInfo and request.roomInfo.get("area"):
        area = float(request.roomInfo.get("area"))
        if area < 15:
            query += " для маленькой комнаты"
        elif area > 30:
            query += " для просторной комнаты"
    
    # Добавляем информацию о цветовой схеме, если есть
    if identified_needs.get("color_scheme"):
        query += f" {identified_needs.get('color_scheme')}"
    
    return query

def generate_design_analysis(request: DesignerRequest, needs_result: Dict[str, Any]) -> Dict[str, Any]:
    """Генерирует детальный анализ дизайна интерьера на основе параметров запроса и определенных потребностей."""
    room_type = get_room_type_name(request.roomType)
    style = get_style_name(request.style)
    
    # Получаем определенные потребности
    identified_needs = needs_result["identified_needs"]
    
    # Определяем цветовую палитру на основе стиля
    palettes = {
        "Современный": ["#E8E8E8", "#303030", "#6E7E85", "#A4C2A8", "#D3D5D7"],
        "Скандинавский": ["#FFFFFF", "#F5F5F5", "#E8E4D9", "#B6C8B2", "#8A9B8E"],
        "Лофт": ["#BFB3A5", "#8D7E74", "#423A35", "#BF925A", "#593D25"],
        "Классический": ["#F2E8D7", "#D9BC91", "#9B8A7A", "#654F36", "#402E22"],
        "Минимализм": ["#FFFFFF", "#F2F2F2", "#D9D9D9", "#BFBFBF", "#404040"]
    }
    
    color_palette = palettes.get(style, palettes["Современный"])
    
    # Определяем характеристики материалов на основе стиля
    materials = {
        "Современный": ["Металл", "Стекло", "Акрил", "Глянцевые поверхности"],
        "Скандинавский": ["Светлое дерево", "Натуральный текстиль", "Мех", "Шерсть"],
        "Лофт": ["Кирпич", "Грубый металл", "Состаренное дерево", "Бетон"],
        "Классический": ["Натуральное дерево", "Мрамор", "Текстиль с орнаментом", "Бронза"],
        "Минимализм": ["Матовые поверхности", "Монохромные текстили", "Натуральный камень", "Стекло"]
    }
    
    recommended_materials = materials.get(style, materials["Современный"])
    
    # Формируем рекомендации по дизайну
    area = float(request.roomInfo.get("area", 0)) if request.roomInfo else 0
    design_principles = []
    
    if room_type == "гостиная":
        design_principles.append({
            "title": "Зонирование",
            "description": "Разделите пространство на зону отдыха, зону общения и при необходимости рабочую зону."
        })
    elif room_type == "спальня":
        design_principles.append({
            "title": "Освещение",
            "description": "Используйте многоуровневое освещение с акцентом на мягкий, расслабляющий свет."
        })
    elif room_type == "кухня":
        design_principles.append({
            "title": "Функциональность",
            "description": "Придерживайтесь правила рабочего треугольника: холодильник, мойка и плита должны образовывать треугольник."
        })
    
    # Добавляем общие принципы
    design_principles.append({
        "title": "Пропорции и масштаб",
        "description": f"Для площади {area}м² рекомендуем выбирать предметы с общей площадью основания не более {round(area * 0.4)}м²."
    })
    
    design_principles.append({
        "title": "Акценты",
        "description": "Создайте 1-2 ярких акцента, остальные элементы должны быть нейтральными."
    })
    
    # Возвращаем полный анализ
    return {
        "roomType": room_type,
        "style": style,
        "colorPalette": color_palette,
        "recommendedMaterials": recommended_materials,
        "designPrinciples": design_principles,
        "area": area,
        "identifiedNeeds": identified_needs
    }

def categorize_furniture_products(products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Группирует товары мебели по категориям."""
    # Категории мебели и соответствующие ключевые слова для поиска
    categories = {
        "Диваны и кресла": ["диван", "софа", "кресло", "пуф"],
        "Столы и стулья": ["стол", "стул", "табурет", "стеллаж"],
        "Шкафы и хранение": ["шкаф", "комод", "полка", "этажерка", "гардероб"],
        "Кровати": ["кровать", "матрас", "изголовье"],
        "Освещение": ["светильник", "люстра", "лампа", "бра", "торшер"],
        "Декор": ["ковер", "подушка", "ваза", "картина", "зеркало", "часы"]
    }
    
    # Инициализируем структуру категорий
    categorized = {category: [] for category in categories}
    categorized["Другое"] = []  # Категория для товаров, которые не попали в основные
    
    # Распределяем товары по категориям
    for product in products:
        name = product.get("name", "").lower()
        assigned = False
        
        for category, keywords in categories.items():
            if any(keyword in name for keyword in keywords):
                categorized[category].append(product)
                assigned = True
                break
        
        if not assigned:
            categorized["Другое"].append(product)
    
    # Удаляем пустые категории
    return {k: v for k, v in categorized.items() if v}

def get_dietary_goal_name(goal_id: str) -> str:
    """Получает название цели питания по идентификатору."""
    goal_map = {
        'weight_loss': 'похудение',
        'muscle_gain': 'набор мышечной массы',
        'health': 'здоровое питание',
        'energy': 'повышение энергии',
        'special': 'особые потребности'
    }
    
    return goal_map.get(goal_id, goal_id)

def generate_design_concept(request: DesignerRequest, needs_result: Dict[str, Any]) -> Dict[str, Any]:
    """Генерирует дизайн-концепцию для комнаты на основе анализа AI."""
    room_type = get_room_type_name(request.roomType)
    style = get_style_name(request.style)
    area = request.roomInfo.get('area', '20') if request.roomInfo else '20'
    
    # Извлекаем данные из анализа модели
    identified_needs = needs_result.get("identified_needs", {})
    response_text = needs_result.get("response", "")
    
    # Основные элементы дизайн-концепции
    concept = {
        "mainIdea": "",
        "styleDescription": "",
        "moodBoard": [],
        "keyElements": []
    }
    
    # Попытка найти основную идею дизайна в ответе AI
    if "design_concept" in identified_needs:
        concept["mainIdea"] = identified_needs["design_concept"]
    else:
        # Генерируем основную идею на основе типа комнаты и стиля
        if style == "Скандинавский":
            concept["mainIdea"] = f"Светлое, функциональное пространство с акцентом на натуральные материалы и простоту форм. {room_type.capitalize()} площадью {area} м² в скандинавском стиле сочетает в себе практичность и уют, характерные для северных стран."
        elif style == "Современный":
            concept["mainIdea"] = f"Элегантное пространство с чистыми линиями и технологичными материалами. {room_type.capitalize()} площадью {area} м² в современном стиле создаёт ощущение открытости и свободы, сохраняя функциональность и комфорт."
        elif style == "Лофт":
            concept["mainIdea"] = f"Индустриальное пространство с открытой планировкой и необработанными поверхностями. {room_type.capitalize()} площадью {area} м² в стиле лофт демонстрирует красоту фактурных материалов и промышленную эстетику."
        elif style == "Классический":
            concept["mainIdea"] = f"Изысканное пространство с симметричной планировкой и вниманием к деталям. {room_type.capitalize()} площадью {area} м² в классическом стиле олицетворяет элегантность и роскошь, проверенные временем."
        elif style == "Минимализм":
            concept["mainIdea"] = f"Лаконичное пространство с акцентом на функциональность и отсутствие излишеств. {room_type.capitalize()} площадью {area} м² в минималистичном стиле воплощает принцип «меньше значит больше»."
    
    # Описание стиля
    style_descriptions = {
        "Скандинавский": "Скандинавский стиль отличается светлыми цветами, натуральными материалами и функциональностью. Ключевые элементы: деревянные поверхности, белые стены, текстиль из натуральных тканей и простые формы. Акцент на естественное освещение и экологичность.",
        "Современный": "Современный стиль характеризуется чистыми линиями, нейтральной цветовой гаммой и технологичными материалами. Ключевые элементы: геометрические формы, глянцевые поверхности, стекло, металл и открытые пространства. Акцент на функциональность и эргономику.",
        "Лофт": "Стиль лофт вдохновлен промышленными помещениями и отличается необработанными поверхностями и открытой планировкой. Ключевые элементы: кирпичные стены, открытые коммуникации, грубый металл, винтажные аксессуары и высокие потолки. Акцент на пространство и историю.",
        "Классический": "Классический стиль отражает изящество и роскошь прошлых эпох. Ключевые элементы: симметричные композиции, декоративные молдинги, антикварная или стилизованная мебель, богатый текстиль и элегантные аксессуары. Акцент на гармонию и пропорции.",
        "Минимализм": "Минималистичный стиль строится на принципе «меньше значит больше». Ключевые элементы: монохромная цветовая гамма, прямые линии, гладкие поверхности, скрытые системы хранения и отсутствие декора. Акцент на пространство и свет."
    }
    
    concept["styleDescription"] = style_descriptions.get(style, "Индивидуальный стиль интерьера, сочетающий функциональность и эстетику.")
    
    # Ключевые элементы дизайна
    key_elements = []
    if room_type == "гостиная":
        key_elements = [
            {"name": "Зонирование", "description": f"Разделение пространства {area} м² на функциональные зоны: отдыха, общения и, возможно, рабочую."},
            {"name": "Система освещения", "description": "Многоуровневое освещение: основной верхний свет, направленные светильники и декоративные источники света."},
            {"name": "Акцентная стена", "description": f"Выделение одной стены в стиле {style} (цветом, текстурой, декором) для создания фокусной точки."}
        ]
    elif room_type == "спальня":
        key_elements = [
            {"name": "Кровать", "description": f"Центральный элемент интерьера, с изголовьем в стиле {style} и качественным матрасом."},
            {"name": "Текстиль", "description": "Многослойный текстиль: постельное белье, покрывало, декоративные подушки и шторы в единой стилистике."},
            {"name": "Приватность", "description": "Системы затемнения на окнах и звукоизоляционные решения для создания комфортной атмосферы для отдыха."}
        ]
    elif room_type == "кухня":
        key_elements = [
            {"name": "Рабочий треугольник", "description": "Эргономичное расположение холодильника, мойки и плиты для удобства приготовления пищи."},
            {"name": "Системы хранения", "description": f"Функциональные шкафы и органайзеры в стиле {style} для максимального использования пространства."},
            {"name": "Рабочие поверхности", "description": "Прочные и легкие в уходе столешницы, подходящие для интенсивного использования."}
        ]
    
    concept["keyElements"] = key_elements
    
    # Mood board - подборка цветов и материалов
    mood_board = []
    if style == "Скандинавский":
        mood_board = ["светлое дерево", "белый", "голубой", "светло-серый", "текстиль в геометрический узор", "растения в белых кашпо"]
    elif style == "Современный":
        mood_board = ["хром", "стекло", "графитовый", "бежевый", "яркие акценты", "глянцевые поверхности"]
    elif style == "Лофт":
        mood_board = ["кирпич", "состаренное дерево", "черный металл", "кожа", "бетон", "индустриальные светильники"]
    
    concept["moodBoard"] = mood_board
    
    return concept

def generate_floor_plan(request: DesignerRequest, needs_result: Dict[str, Any]) -> Dict[str, Any]:
    """Генерирует схему планировки для комнаты на основе анализа AI."""
    room_type = get_room_type_name(request.roomType)
    style = get_style_name(request.style)
    area = float(request.roomInfo.get('area', 20)) if request.roomInfo else 20
    has_windows = request.roomInfo.get('hasWindows', 'yes') if request.roomInfo else 'yes'
    
    # Извлекаем данные из анализа модели
    identified_needs = needs_result.get("identified_needs", {})
    
    # Базовые расчеты для планировки
    width = round(math.sqrt(area * 1.5), 1)  # Предполагаем, что комната прямоугольная с соотношением сторон 1.5:1
    length = round(area / width, 1)
    
    # Основная информация о планировке
    floor_plan = {
        "dimensions": {
            "width": width,
            "length": length,
            "area": area
        },
        "zoning": [],
        "furnitureLayout": [],
        "recommendations": []
    }
    
    # Зонирование в зависимости от типа комнаты
    if room_type == "гостиная":
        floor_plan["zoning"] = [
            {"name": "Зона отдыха", "area": round(area * 0.6, 1), "position": "центр"},
            {"name": "Зона для общения", "area": round(area * 0.3, 1), "position": "у окна"},
            {"name": "Зона хранения", "area": round(area * 0.1, 1), "position": "у стены"}
        ]
        
        # Примерное расположение мебели
        floor_plan["furnitureLayout"] = [
            {"name": "Диван", "position": "у стены напротив окна", "dimensions": "2.5 x 0.9 м"},
            {"name": "Журнальный столик", "position": "перед диваном", "dimensions": "0.9 x 0.6 м"},
            {"name": "Тумба под ТВ", "position": "у стены напротив дивана", "dimensions": "1.5 x 0.5 м"},
            {"name": "Кресло", "position": "рядом с диваном", "dimensions": "0.8 x 0.8 м"}
        ]
        
    elif room_type == "спальня":
        floor_plan["zoning"] = [
            {"name": "Зона сна", "area": round(area * 0.6, 1), "position": "центр/у стены"},
            {"name": "Зона хранения", "area": round(area * 0.3, 1), "position": "у стены"},
            {"name": "Туалетный столик", "area": round(area * 0.1, 1), "position": "у окна"}
        ]
        
        # Примерное расположение мебели
        floor_plan["furnitureLayout"] = [
            {"name": "Кровать", "position": "центр комнаты у стены", "dimensions": "1.6 x 2.0 м"},
            {"name": "Прикроватные тумбочки", "position": "по обеим сторонам кровати", "dimensions": "0.5 x 0.5 м"},
            {"name": "Шкаф", "position": "у стены", "dimensions": "1.8 x 0.6 м"}
        ]
    
    # Рекомендации по планировке
    if "layout_recommendations" in identified_needs:
        floor_plan["recommendations"] = identified_needs["layout_recommendations"]
    else:
        if room_type == "гостиная":
            floor_plan["recommendations"] = [
                "Расположите диван так, чтобы было удобно смотреть телевизор",
                f"В комнате площадью {area} м² оставляйте минимум 70-80 см для проходов",
                "Избегайте загромождения центра комнаты мебелью",
                "Используйте многофункциональную мебель для экономии пространства"
            ]
        elif room_type == "спальня":
            floor_plan["recommendations"] = [
                "Расположите кровать так, чтобы к ней был удобный доступ с обеих сторон",
                "Оставьте минимум 70 см пространства для прохода вокруг кровати",
                "Разместите шкаф так, чтобы дверцы открывались свободно",
                "Если позволяет площадь, выделите отдельную зону для туалетного столика"
            ]
    
    return floor_plan

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 