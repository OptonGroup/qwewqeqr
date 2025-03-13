#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модели Pydantic для валидации результатов тестирования.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator, model_validator
import re

class SizeInfo(BaseModel):
    """
    Модель для информации о размере товара.
    Поддерживает различные форматы данных от Wildberries API.
    """
    name: Optional[str] = Field(None, description="Название размера")
    origName: Optional[str] = Field(None, description="Оригинальное название размера")
    stocks: Optional[List[int]] = Field(None, description="Информация о наличии")
    
    # Дополнительные поля, которые могут присутствовать
    value: Optional[str] = Field(None, description="Значение размера")
    is_available: Optional[bool] = Field(None, description="Доступен ли размер")
    
    class Config:
        # Разрешаем дополнительные поля, не описанные в модели
        extra = "allow"

class Product(BaseModel):
    """
    Модель товара, возвращаемого из API Wildberries.
    """
    name: str = Field(..., description="Название товара")
    brand: Optional[str] = Field(None, description="Бренд товара")
    price: Union[int, float, str] = Field(..., description="Цена товара")
    rating: Optional[Union[float, str]] = Field(None, description="Рейтинг товара")
    url: str = Field(..., description="URL товара")
    image_url: Optional[str] = Field(None, description="URL изображения товара")
    description: Optional[str] = Field(None, description="Описание товара")
    category: Optional[str] = Field(None, description="Категория товара")
    colors: Optional[List[str]] = Field(None, description="Доступные цвета")
    sizes: Optional[List[Union[str, Dict, SizeInfo]]] = Field(None, description="Доступные размеры")
    
    @validator('price')
    def validate_price(cls, v):
        """Приводит цену к числовому формату, если она передана как строка."""
        if isinstance(v, str):
            try:
                # Пытаемся извлечь числовое значение из строки, удаляя нечисловые символы
                v = v.replace(',', '.').replace(' ', '')
                v = ''.join(char for char in v if char.isdigit() or char == '.')
                return float(v)
            except ValueError:
                return v
        return v
    
    @validator('rating')
    def validate_rating(cls, v):
        """Приводит рейтинг к числовому формату, если он передан как строка."""
        if isinstance(v, str):
            try:
                v = v.replace(',', '.').replace(' ', '')
                return float(v)
            except ValueError:
                return v
        return v
    
    @validator('sizes', pre=True)
    def validate_sizes(cls, v):
        """
        Обрабатывает различные форматы размеров.
        Wildberries API может возвращать размеры в разных форматах:
        - Список строк
        - Список словарей
        - Строка с разделителями
        - Вложенная структура данных
        """
        if v is None:
            return []
            
        # Если размеры представлены строкой, пытаемся разбить на отдельные размеры
        if isinstance(v, str):
            # Разделяем по запятым, точкам с запятой или вертикальной черте
            sizes = re.split(r'[,;|]', v)
            return [size.strip() for size in sizes if size.strip()]
            
        # Если размеры представлены в виде простого списка строк
        if isinstance(v, list) and all(isinstance(item, str) for item in v):
            return v
            
        # Если размеры представлены в виде списка словарей или объектов
        if isinstance(v, list):
            processed_sizes = []
            for item in v:
                if isinstance(item, dict):
                    # Пытаемся извлечь информацию о размере из словаря
                    processed_sizes.append(item)
                else:
                    # Преобразуем другие типы в строку
                    processed_sizes.append(str(item))
            return processed_sizes
        
        # В других случаях возвращаем как есть
        return v
    
    class Config:
        # Разрешаем дополнительные поля, не описанные в модели
        extra = "allow"

class SearchResults(BaseModel):
    """
    Модель результатов поиска товаров.
    """
    success: bool = Field(..., description="Признак успешности запроса")
    query: Optional[str] = Field(None, description="Поисковый запрос")
    products: Optional[List[Product]] = Field(None, description="Список найденных товаров")
    image_analysis: Optional[str] = Field(None, description="Результаты анализа изображения")
    recommendations: Optional[str] = Field(None, description="Рекомендации по найденным товарам")
    error: Optional[str] = Field(None, description="Сообщение об ошибке")
    
    @validator('products', pre=True)
    def validate_products(cls, v):
        """Обрабатывает случай, когда products не является списком."""
        if v is None:
            return []
        return v
    
    @model_validator(mode='after')
    def validate_recommendations_quality(self):
        """
        Проверяет качество рекомендаций.
        
        Рекомендации должны содержать информацию о товарах.
        """
        products = self.products or []
        recommendations = self.recommendations
        
        if products and recommendations:
            # Считаем, что рекомендации качественные, если они содержат упоминания 
            # не менее 50% товаров из списка продуктов
            mentioned_products = 0
            
            for product in products:
                if product.name in recommendations or (product.brand and product.brand in recommendations):
                    mentioned_products += 1
            
            # Добавляем информацию о качестве рекомендаций в модель
            self.recommendations_quality = {
                'mentioned_products': mentioned_products,
                'total_products': len(products),
                'percentage': round(mentioned_products / len(products) * 100, 2) if products else 0
            }
            
        return self
    
    class Config:
        # Разрешаем дополнительные поля, не описанные в модели
        extra = "allow"
        
        
def validate_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Валидирует результаты тестирования с использованием Pydantic моделей.
    
    Args:
        results (Dict[str, Any]): Словарь с результатами тестирования
    
    Returns:
        Dict[str, Any]: Словарь с результатами валидации
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'validated_data': None
    }
    
    try:
        # Пытаемся валидировать результаты через модель Pydantic
        search_results = SearchResults(**results)
        
        # Сохраняем валидированные данные
        validation_result['validated_data'] = search_results.model_dump()
        
        # Добавляем информацию о товарах для удобства анализа
        product_info = []
        if search_results.products:
            for product in search_results.products:
                product_info.append({
                    'name': product.name,
                    'brand': product.brand,
                    'price': product.price,
                    'rating': product.rating,
                    'sizes': product.sizes
                })
        
        validation_result['products_info'] = product_info
        
        # Добавляем информацию о качестве рекомендаций, если она доступна
        if hasattr(search_results, 'recommendations_quality'):
            validation_result['recommendations_quality'] = search_results.recommendations_quality
            
    except Exception as e:
        validation_result['is_valid'] = False
        validation_result['errors'].append(str(e))
    
    return validation_result


def generate_validation_report(validation_result: Dict[str, Any]) -> str:
    """
    Генерирует отчет о валидации результатов в формате Markdown.
    
    Args:
        validation_result (Dict[str, Any]): Результаты валидации
    
    Returns:
        str: Отчет о валидации в формате Markdown
    """
    if not validation_result['is_valid']:
        report = "# Отчет о валидации результатов\n\n"
        report += "## Статус валидации: ОШИБКА\n\n"
        report += "## Ошибки валидации:\n"
        for error in validation_result['errors']:
            report += f"- {error}\n"
        return report
    
    validated_data = validation_result['validated_data']
    
    report = "# Отчет о валидации результатов\n\n"
    report += "## Статус валидации: Успешно\n\n"
    
    report += "## Основная информация:\n"
    report += f"- Успешность запроса: {validated_data.get('success', 'Нет данных')}\n"
    report += f"- Поисковый запрос: {validated_data.get('query', 'None')}\n"
    report += f"- Количество товаров: {len(validated_data.get('products', []))}\n"
    report += f"- Наличие анализа изображения: {'Да' if validated_data.get('image_analysis') else 'Нет'}\n"
    report += f"- Наличие рекомендаций: {'Да' if validated_data.get('recommendations') else 'Нет'}\n"
    
    # Добавляем информацию о качестве рекомендаций, если доступна
    if 'recommendations_quality' in validation_result:
        rec_quality = validation_result['recommendations_quality']
        report += "\n## Оценка качества рекомендаций:\n"
        report += f"- Упомянуто товаров: {rec_quality.get('mentioned_products', 0)} из {rec_quality.get('total_products', 0)} ({rec_quality.get('percentage', 0)}%)\n"
    
    if validated_data.get('products'):
        report += "\n## Информация о товарах:\n"
        for i, product in enumerate(validated_data['products']):
            report += f"### Товар #{i+1}:\n"
            report += f"- Название: {product.get('name', 'Нет данных')}\n"
            report += f"- Бренд: {product.get('brand', 'Нет данных')}\n"
            report += f"- Цена: {product.get('price', 'Нет данных')}\n"
            report += f"- Рейтинг: {product.get('rating', 'Нет данных')}\n"
            
            if product.get('sizes'):
                report += "- Размеры: "
                if isinstance(product['sizes'][0], dict):
                    size_names = [size.get('name', size.get('origName', str(size))) for size in product['sizes']]
                    report += ", ".join(str(s) for s in size_names if s)
                else:
                    report += ", ".join(str(s) for s in product['sizes'])
                report += "\n"
    
    return report 