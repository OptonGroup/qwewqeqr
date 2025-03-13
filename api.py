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

# Создаем FastAPI приложение
app = FastAPI(
    title="Shopping Assistant API",
    description="API для шопинг-ассистента с поддержкой Pinterest и Wildberries",
    version="1.0.0"
)

# Настраиваем CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники (в продакшн изменить на конкретные домены)
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
    Получает экземпляр PinterestAPI
    
    Returns:
        Экземпляр PinterestAPI или None в случае ошибки
    """
    global _pinterest_instance
    
    try:
        if _pinterest_instance is None:
            _pinterest_instance = PinterestAPI()
        
        return _pinterest_instance
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации PinterestAPI: {str(e)}")
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
        for item in analysis.get("elements", []):
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
        
        response = {
            "elements": clothing_items,
            "analysis": analysis.get("analysis", ""),
            "image_path": f"/static/uploads/{file_name}",
            "gender": gender
        }
        
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
    Возвращает HTML-страницу с интерфейсом для работы с API
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

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
    """
    Обработка поиска образов в Pinterest и анализ одежды на найденных изображениях
    
    Args:
        task_id: Идентификатор задачи
        request: Параметры запроса
    """
    try:
        # Получаем экземпляр Pinterest
        pinterest = get_pinterest()
        if not pinterest:
            raise Exception("Не удалось инициализировать Pinterest")
        
        # Обновляем статус задачи
        tasks[task_id].status = "processing"
        tasks[task_id].message = "Поиск образов в Pinterest"
        
        # Ищем пины в Pinterest
        pins = await pinterest.search_pins(
            query=request.query,
            limit=request.num_results,
            download=True
        )
        
        if not pins:
            tasks[task_id].status = "failed"
            tasks[task_id].message = "Не удалось найти образы в Pinterest"
            return
        
        # Обновляем статус задачи
        tasks[task_id].status = "analyzing"
        tasks[task_id].message = "Анализ найденных образов"
        tasks[task_id].image_urls = [pin.image_url for pin in pins]
        
        # Анализ найденных образов
        pinterest_results = []
        
        # Инициализируем ассистента для анализа образов
        assistant = get_assistant()
        
        # Обрабатываем каждый найденный пин
        for i, pin in enumerate(pins):
            try:
                # Обновляем прогресс
                tasks[task_id].progress = int((i + 1) / len(pins) * 100)
                tasks[task_id].downloaded_photos = i + 1
                
                # Если есть сохраненное изображение, анализируем его
                image_path = pin.saved_path if pin.saved_path else None
                
                if not image_path or not os.path.exists(image_path):
                    continue
                
                # Анализируем изображение
                analysis_result = None
                
                # Сначала пробуем через визуальный анализатор
                if get_visual_analyzer():
                    visual_analyzer = get_visual_analyzer()
                    analysis_result = await visual_analyzer.analyze_image_async(image_path)
                
                # Если анализатор недоступен или результат пуст, используем ассистента
                if not analysis_result or not analysis_result.get("elements"):
                    user_id = f"pinterest_{task_id}_{i}"
                    prompt = f"Опиши предметы одежды на этом изображении с Pinterest: \"{pin.title or pin.description or request.query}\". Перечисли все видимые предметы одежды, укажи их типы, цвета и особенности. Ответ должен быть структурированным: каждый предмет отдельно с указанием типа, цвета, описания и пола (мужской или женский)."
                    
                    # Получаем ответ от ассистента
                    response = await assistant.generate_response_async(
                        user_id=user_id,
                        role="стилист",
                        user_input=prompt
                    )
                    
                    # Парсим ответ для извлечения предметов одежды
                    clothing_items = parse_assistant_response(response, gender=request.gender)
                    analysis_text = response
                else:
                    # Используем результаты визуального анализа
                    clothing_items = analysis_result.get("elements", [])
                    analysis_text = analysis_result.get("analysis", "")
                
                # Добавляем результаты анализа
                pinterest_results.append({
                    "imageUrl": pin.image_url,
                    "sourceUrl": pin.source_url or f"https://www.pinterest.com/pin/{pin.id}/",
                    "description": pin.title or pin.description or f"Образ по запросу: {request.query}",
                    "clothingItems": clothing_items
                })
                
            except Exception as e:
                logger.error(f"Ошибка при анализе образа: {str(e)}")
                continue
        
        # Обновляем статус задачи
        tasks[task_id].status = "completed"
        tasks[task_id].message = f"Найдено и проанализировано {len(pinterest_results)} образов"
        
        # Добавляем результаты к задаче
        setattr(tasks[task_id], "pinterest_results", pinterest_results)
        
    except Exception as e:
        logger.error(f"Ошибка при поиске образов в Pinterest: {str(e)}")
        logger.error(traceback.format_exc())
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Ошибка: {str(e)}"

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

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 