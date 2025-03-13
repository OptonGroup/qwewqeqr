from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uvicorn
import os
import uuid
import logging
import shutil
import time
from pathlib import Path
from bank_statement_parser import BankStatementParser
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bank_api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создаем директории для файлов
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("static/visualizations", exist_ok=True)

# Модели данных
class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    file_name: str
    upload_time: str
    progress: int = 0
    message: Optional[str] = None
    result_path: Optional[str] = None
    
class AnalysisResult(BaseModel):
    metadata: Dict[str, Any]
    total_expenses: float
    total_income: float
    balance: float
    category_spending: List[Dict[str, Any]]
    monthly_trend: List[Dict[str, Any]]
    visualizations: Dict[str, str]

# Создаем FastAPI приложение
app = FastAPI(
    title="Bank Statement Parser API",
    description="API для анализа банковских выписок Тинькофф",
    version="1.0.0"
)

# Добавляем поддержку CORS для всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Хранилище задач
tasks: Dict[str, TaskStatus] = {}

# Экземпляр парсера банковских выписок
parser = BankStatementParser(cache_dir="bank_statements_cache")

# Проверка здоровья API
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Сервер работает"}

# Загрузка банковской выписки
@app.post("/upload")
async def upload_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Проверяем формат файла
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.pdf', '.txt']:
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы PDF и TXT")
    
    # Генерируем уникальный идентификатор для задачи
    task_id = str(uuid.uuid4())
    safe_filename = f"{task_id}{file_extension}"
    
    # Сохраняем файл
    file_path = os.path.join("uploads", safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Создаем запись о задаче
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="pending",
        file_name=file.filename,
        upload_time=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Запускаем обработку в фоновом режиме
    background_tasks.add_task(process_statement, task_id, file_path)
    
    return {"task_id": task_id, "status": "pending", "message": "Файл загружен, начинается обработка"}

# Фоновая обработка выписки
async def process_statement(task_id: str, file_path: str):
    try:
        # Обновляем статус задачи
        tasks[task_id].status = "processing"
        tasks[task_id].progress = 10
        
        # Определяем тип файла
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Парсим выписку
        transactions_df = None
        if file_extension == '.pdf':
            transactions_df = parser.parse_pdf_statement(file_path)
        elif file_extension == '.txt':
            # Читаем текстовый файл
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            # Извлекаем транзакции из текста
            transactions = parser._extract_transactions_from_text(text)
            # Извлекаем метаданные из текста
            metadata = parser._extract_statement_metadata(text)
            
            # Если транзакции найдены, создаем DataFrame
            if transactions:
                import pandas as pd
                transactions_df = pd.DataFrame(transactions)
            
        tasks[task_id].progress = 40
        
        # Если транзакции не найдены
        if transactions_df is None or transactions_df.empty:
            tasks[task_id].status = "failed"
            tasks[task_id].message = "Не удалось найти транзакции в файле выписки"
            return
        
        # Анализируем расходы по категориям
        category_spending = parser.analyze_spending_by_category(transactions_df)
        tasks[task_id].progress = 60
        
        # Анализируем тренды расходов по месяцам
        monthly_trend = parser.get_monthly_spending_trend(transactions_df)
        tasks[task_id].progress = 70
        
        # Создаем отчет о расходах
        report_dir = Path("reports") / task_id
        os.makedirs(report_dir, exist_ok=True)
        
        report = parser.generate_spending_report(
            transactions_df, 
            output_dir=str(report_dir),
            report_type="full"
        )
        tasks[task_id].progress = 90
        
        # Сохраняем результаты в JSON-файл
        result_path = report_dir / "report.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Обновляем статус задачи
        tasks[task_id].status = "completed"
        tasks[task_id].progress = 100
        tasks[task_id].result_path = str(result_path)
        tasks[task_id].message = "Анализ успешно выполнен"
        
    except Exception as e:
        logger.error(f"Ошибка при обработке выписки: {str(e)}")
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"Ошибка при обработке: {str(e)}"

# Получение статуса задачи
@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return tasks[task_id]

# Получение результатов анализа
@app.get("/results/{task_id}")
async def get_analysis_results(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    task = tasks[task_id]
    
    if task.status != "completed":
        return {"status": task.status, "message": task.message or "Задача еще выполняется"}
    
    # Загружаем JSON-файл с результатами
    result_path = task.result_path
    try:
        with open(result_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        
        return report
    except Exception as e:
        logger.error(f"Ошибка при загрузке результатов: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке результатов анализа")

# Получение списка всех задач
@app.get("/tasks")
async def get_all_tasks():
    return list(tasks.values())

# Получение визуализации расходов
@app.get("/visualization/{task_id}/{viz_type}")
async def get_visualization(task_id: str, viz_type: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    task = tasks[task_id]
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Анализ еще не завершен")
    
    # Загружаем JSON-файл с результатами
    result_path = task.result_path
    try:
        with open(result_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        
        if "visualization_files" not in report:
            raise HTTPException(status_code=404, detail="Визуализации не найдены")
        
        if viz_type not in report["visualization_files"]:
            raise HTTPException(status_code=404, detail=f"Визуализация типа {viz_type} не найдена")
        
        viz_path = report["visualization_files"][viz_type]
        return FileResponse(viz_path)
    except Exception as e:
        logger.error(f"Ошибка при загрузке визуализации: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке визуализации")

# Удаление задачи
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Удаляем связанные файлы
    task = tasks[task_id]
    
    # Удаляем исходный файл выписки
    uploads_dir = Path("uploads")
    for ext in ['.pdf', '.txt']:
        file_path = uploads_dir / f"{task_id}{ext}"
        if file_path.exists():
            file_path.unlink()
    
    # Удаляем отчет и визуализации
    if task.result_path:
        report_dir = Path(task.result_path).parent
        if report_dir.exists():
            shutil.rmtree(report_dir)
    
    # Удаляем задачу из хранилища
    del tasks[task_id]
    
    return {"status": "success", "message": "Задача удалена"}

# Запуск сервера для разработки
if __name__ == "__main__":
    uvicorn.run("bank_api:app", host="0.0.0.0", port=8000, reload=True) 