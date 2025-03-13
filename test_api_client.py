#!/usr/bin/env python
"""
Тестовый клиент для API поиска образов в Pinterest и товаров на Wildberries.
"""

import asyncio
import json
import time
import httpx
import argparse
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"

async def search_pinterest(query: str, gender: str = "женский", num_results: int = 3) -> str:
    """
    Выполняет поиск образов в Pinterest
    
    Args:
        query: Поисковый запрос
        gender: Пол (мужской/женский)
        num_results: Количество результатов
        
    Returns:
        Идентификатор задачи
    """
    print(f"Поиск образов в Pinterest: {query}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/search-pinterest",
            json={
                "query": query,
                "gender": gender,
                "num_results": num_results
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Задача создана: {data['task_id']}")
            return data["task_id"]
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")
            return ""

async def get_pinterest_results(task_id: str, wait_for_completion: bool = True) -> Dict[str, Any]:
    """
    Получает результаты поиска в Pinterest
    
    Args:
        task_id: Идентификатор задачи
        wait_for_completion: Ожидать завершения задачи
        
    Returns:
        Результаты поиска
    """
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(f"{BASE_URL}/search-pinterest/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "completed" or not wait_for_completion:
                    return data
                
                print(f"Статус задачи: {data['status']} - {data['message']} - {data['progress']}%")
                time.sleep(1)
            else:
                print(f"Ошибка: {response.status_code} - {response.text}")
                return {}

async def search_wildberries(pinterest_task_id: str, items: List[Dict[str, Any]] = None, max_products_per_item: int = 3) -> str:
    """
    Выполняет поиск товаров на Wildberries
    
    Args:
        pinterest_task_id: Идентификатор задачи Pinterest
        items: Предметы одежды для поиска
        max_products_per_item: Максимальное количество товаров на предмет
        
    Returns:
        Идентификатор задачи
    """
    print(f"Поиск товаров на Wildberries на основе задачи Pinterest: {pinterest_task_id}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/search-wildberries",
            json={
                "pinterest_task_id": pinterest_task_id,
                "items": items,
                "max_products_per_item": max_products_per_item
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Задача создана: {data['task_id']}")
            return data["task_id"]
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")
            return ""

async def get_wildberries_results(task_id: str, wait_for_completion: bool = True) -> Dict[str, Any]:
    """
    Получает результаты поиска на Wildberries
    
    Args:
        task_id: Идентификатор задачи
        wait_for_completion: Ожидать завершения задачи
        
    Returns:
        Результаты поиска
    """
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(f"{BASE_URL}/search-wildberries/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] == "completed" or not wait_for_completion:
                    return data
                
                print(f"Статус задачи: {data['status']} - {data['message']} - {data['progress']}%")
                time.sleep(1)
            else:
                print(f"Ошибка: {response.status_code} - {response.text}")
                return {}

async def full_search_workflow(query: str, gender: str = "женский", num_pinterest_results: int = 3, max_products_per_item: int = 3):
    """
    Выполняет полный процесс поиска: Pinterest -> Анализ образов -> Wildberries
    
    Args:
        query: Поисковый запрос
        gender: Пол (мужской/женский)
        num_pinterest_results: Количество результатов Pinterest
        max_products_per_item: Максимальное количество товаров на предмет
    """
    # Шаг 1: Поиск в Pinterest
    pinterest_task_id = await search_pinterest(query, gender, num_pinterest_results)
    if not pinterest_task_id:
        print("Не удалось создать задачу для поиска в Pinterest")
        return
    
    # Шаг 2: Получение результатов Pinterest
    pinterest_results = await get_pinterest_results(pinterest_task_id)
    if "results" not in pinterest_results:
        print("Не удалось получить результаты поиска в Pinterest")
        return
    
    print(f"Найдено образов в Pinterest: {len(pinterest_results['results'])}")
    
    # Шаг 3: Поиск на Wildberries
    wildberries_task_id = await search_wildberries(pinterest_task_id, max_products_per_item=max_products_per_item)
    if not wildberries_task_id:
        print("Не удалось создать задачу для поиска на Wildberries")
        return
    
    # Шаг 4: Получение результатов Wildberries
    wildberries_results = await get_wildberries_results(wildberries_task_id)
    if "results" not in wildberries_results:
        print("Не удалось получить результаты поиска на Wildberries")
        return
    
    print(f"Найдено товаров на Wildberries: {len(wildberries_results['results'])}")
    
    # Шаг 5: Сохранение результатов в файл
    result_file = f"results_{int(time.time())}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "query": query,
            "gender": gender,
            "pinterest": pinterest_results,
            "wildberries": wildberries_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Результаты сохранены в файл: {result_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Тестовый клиент для API поиска образов")
    parser.add_argument("query", help="Поисковый запрос для Pinterest")
    parser.add_argument("--gender", default="женский", help="Пол (мужской/женский)")
    parser.add_argument("--pinterest-results", type=int, default=3, help="Количество результатов Pinterest")
    parser.add_argument("--products-per-item", type=int, default=3, help="Максимальное количество товаров на предмет")
    
    args = parser.parse_args()
    
    asyncio.run(full_search_workflow(
        args.query,
        args.gender,
        args.pinterest_results,
        args.products_per_item
    )) 