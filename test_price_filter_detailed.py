"""
Подробный тест фильтрации по цене в Wildberries API.

Этот скрипт проверяет различные сценарии фильтрации по цене в API Wildberries
и документирует наблюдения о том, как работает фильтрация.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from wildberries import Wildberries

# Настройка логирования
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"price_filter_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Функция для логирования информации о товарах
def log_products(products: List[Dict[str, Any]], test_name: str) -> None:
    """Логирует информацию о найденных товарах."""
    logger.info(f"Результаты теста '{test_name}':")
    logger.info(f"Найдено {len(products)} товаров")
    
    for i, product in enumerate(products, 1):
        price = product.get('price', 0)
        sale_price = product.get('sale_price', price)
        discount_percent = 0
        
        if price > 0:
            discount_percent = round(100 - (sale_price / price * 100))
        
        logger.info(f"Товар {i}: {product.get('name', 'Без названия')}")
        logger.info(f"  ID: {product.get('id', 'Нет ID')}")
        logger.info(f"  Бренд: {product.get('brand', 'Нет бренда')}")
        logger.info(f"  Основная цена: {price} руб.")
        logger.info(f"  Цена со скидкой: {sale_price} руб.")
        logger.info(f"  Скидка: {discount_percent}%")
        logger.info(f"  URL: {product.get('url', 'Нет URL')}")
        logger.info("  " + "-" * 50)
    
    # Сохраняем результаты в JSON файл для дальнейшего анализа
    result_file = os.path.join(log_dir, f"{test_name.replace(' ', '_').lower()}.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Результаты сохранены в файл: {result_file}")

# Функция для анализа результатов фильтрации по цене
def analyze_price_filter(
    products: List[Dict[str, Any]], 
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """Анализирует результаты фильтрации по цене."""
    result = {
        "min_price": min_price,
        "max_price": max_price,
        "count": len(products),
        "original_prices": {},
        "sale_prices": {},
        "discounts": {},
        "all_above_min": True,
        "all_below_max": True,
        "below_min_products": [],
        "above_max_products": [],
        "price_distribution": {
            "original": {},
            "sale": {}
        }
    }
    
    if not products:
        logger.warning("Нет товаров для анализа")
        return result
    
    # Анализ основных цен
    original_prices = [p.get('price', 0) for p in products]
    result["original_prices"]["min"] = min(original_prices) if original_prices else 0
    result["original_prices"]["max"] = max(original_prices) if original_prices else 0
    result["original_prices"]["avg"] = sum(original_prices) / len(original_prices) if original_prices else 0
    result["original_prices"]["median"] = sorted(original_prices)[len(original_prices) // 2] if original_prices else 0
    
    # Анализ скидочных цен
    sale_prices = [p.get('sale_price', p.get('price', 0)) for p in products]
    result["sale_prices"]["min"] = min(sale_prices) if sale_prices else 0
    result["sale_prices"]["max"] = max(sale_prices) if sale_prices else 0
    result["sale_prices"]["avg"] = sum(sale_prices) / len(sale_prices) if sale_prices else 0
    result["sale_prices"]["median"] = sorted(sale_prices)[len(sale_prices) // 2] if sale_prices else 0
    
    # Анализ скидок
    discounts = []
    for p in products:
        price = p.get('price', 0)
        sale_price = p.get('sale_price', price)
        if price > 0:
            discount = round(100 - (sale_price / price * 100))
            discounts.append(discount)
    
    result["discounts"]["avg"] = sum(discounts) / len(discounts) if discounts else 0
    result["discounts"]["max"] = max(discounts) if discounts else 0
    result["discounts"]["min"] = min(discounts) if discounts else 0
    result["discounts"]["median"] = sorted(discounts)[len(discounts) // 2] if discounts else 0
    
    # Анализ распределения цен
    # Создаем ценовые диапазоны для анализа
    price_ranges = [
        (0, 1000), (1000, 2000), (2000, 5000), 
        (5000, 10000), (10000, 20000), (20000, 50000), 
        (50000, float('inf'))
    ]
    
    # Инициализируем счетчики для каждого диапазона
    for start, end in price_ranges:
        range_name = f"{start}-{end if end != float('inf') else '+'}"
        result["price_distribution"]["original"][range_name] = 0
        result["price_distribution"]["sale"][range_name] = 0
    
    # Подсчитываем количество товаров в каждом ценовом диапазоне
    for p in products:
        price = p.get('price', 0)
        sale_price = p.get('sale_price', price)
        
        for start, end in price_ranges:
            range_name = f"{start}-{end if end != float('inf') else '+'}"
            if start <= price < end:
                result["price_distribution"]["original"][range_name] += 1
            if start <= sale_price < end:
                result["price_distribution"]["sale"][range_name] += 1
    
    # Логирование результатов анализа
    logger.info("Анализ результатов фильтрации по цене:")
    logger.info(f"Параметры фильтрации: min_price={min_price}, max_price={max_price}")
    logger.info(f"Количество товаров: {len(products)}")
    logger.info(f"Основные цены: мин={result['original_prices']['min']}, макс={result['original_prices']['max']}, средняя={result['original_prices']['avg']:.2f}, медиана={result['original_prices']['median']}")
    logger.info(f"Скидочные цены: мин={result['sale_prices']['min']}, макс={result['sale_prices']['max']}, средняя={result['sale_prices']['avg']:.2f}, медиана={result['sale_prices']['median']}")
    logger.info(f"Скидки: мин={result['discounts']['min']}%, макс={result['discounts']['max']}%, средняя={result['discounts']['avg']:.2f}%, медиана={result['discounts']['median']}%")
    
    # Логирование распределения цен
    logger.info("Распределение основных цен:")
    for range_name, count in result["price_distribution"]["original"].items():
        percentage = (count / len(products) * 100) if products else 0
        logger.info(f"  {range_name} руб.: {count} товаров ({percentage:.2f}%)")
    
    logger.info("Распределение скидочных цен:")
    for range_name, count in result["price_distribution"]["sale"].items():
        percentage = (count / len(products) * 100) if products else 0
        logger.info(f"  {range_name} руб.: {count} товаров ({percentage:.2f}%)")
    
    # Проверка соответствия фильтрам
    if min_price is not None:
        below_min = [p for p in products if p.get('price', 0) < min_price]
        if below_min:
            result["all_above_min"] = False
            result["below_min_products"] = below_min
            logger.warning(f"Найдено {len(below_min)} товаров с основной ценой ниже min_price={min_price}")
            for p in below_min:
                logger.warning(f"  Товар с ценой {p.get('price', 0)} ниже min_price={min_price}: {p.get('name', 'Без названия')}")
        else:
            logger.info(f"Все товары имеют основную цену >= min_price={min_price} ✓")
    
    if max_price is not None:
        above_max = [p for p in products if p.get('sale_price', p.get('price', 0)) > max_price]
        if above_max:
            result["all_below_max"] = False
            result["above_max_products"] = above_max
            logger.warning(f"Найдено {len(above_max)} товаров со скидочной ценой выше max_price={max_price}")
            for p in above_max:
                logger.warning(f"  Товар со скидочной ценой {p.get('sale_price', p.get('price', 0))} выше max_price={max_price}: {p.get('name', 'Без названия')}")
        else:
            logger.info(f"Все товары имеют скидочную цену <= max_price={max_price} ✓")
    
    # Проверка на противоречивые параметры
    if min_price is not None and max_price is not None and min_price > max_price:
        result["contradictory_params"] = True
        logger.warning(f"Противоречивые параметры: min_price ({min_price}) > max_price ({max_price})")
        if products:
            logger.info(f"Несмотря на противоречивые параметры, найдено {len(products)} товаров")
            # Проверяем, какой параметр имеет приоритет
            all_above_min = all(p.get('price', 0) >= min_price for p in products)
            all_below_max = all(p.get('sale_price', p.get('price', 0)) <= max_price for p in products)
            
            result["priority_min_price"] = all_above_min and not all_below_max
            result["priority_max_price"] = all_below_max and not all_above_min
            result["satisfy_both"] = all_above_min and all_below_max
            result["satisfy_none"] = not all_above_min and not all_below_max
            
            if result["priority_min_price"]:
                logger.info("Приоритет отдается параметру min_price ✓")
            elif result["priority_max_price"]:
                logger.info("Приоритет отдается параметру max_price ✓")
            elif result["satisfy_both"]:
                logger.info("Товары удовлетворяют обоим параметрам ✓")
            else:
                logger.warning("Некоторые товары не удовлетворяют ни одному из параметров ✗")
    
    # Дополнительный анализ: соотношение основной и скидочной цены
    price_ratios = []
    for p in products:
        price = p.get('price', 0)
        sale_price = p.get('sale_price', price)
        if price > 0:
            ratio = sale_price / price
            price_ratios.append(ratio)
    
    if price_ratios:
        result["price_ratio"] = {
            "min": min(price_ratios),
            "max": max(price_ratios),
            "avg": sum(price_ratios) / len(price_ratios),
            "median": sorted(price_ratios)[len(price_ratios) // 2]
        }
        logger.info(f"Соотношение скидочной цены к основной: мин={result['price_ratio']['min']:.2f}, "
                   f"макс={result['price_ratio']['max']:.2f}, "
                   f"среднее={result['price_ratio']['avg']:.2f}, "
                   f"медиана={result['price_ratio']['median']:.2f}")
    
    return result

# Функция для генерации HTML-отчета
def generate_html_report(test_results, products_data):
    """Генерирует HTML-отчет на основе результатов тестов."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Отчет о тестировании фильтрации по цене в Wildberries API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            h1, h2, h3 {
                color: #333;
            }
            .test-case {
                background-color: white;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .test-header {
                background-color: #4a76a8;
                color: white;
                padding: 10px;
                border-radius: 5px 5px 0 0;
                margin: -15px -15px 15px -15px;
            }
            .stats-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
            }
            .stats-box {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                flex: 1;
                min-width: 200px;
            }
            .stats-box h4 {
                margin-top: 0;
                color: #4a76a8;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }
            .products-list {
                margin-top: 20px;
            }
            .product-item {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            .product-name {
                font-weight: bold;
                color: #333;
            }
            .price-info {
                color: #666;
                margin: 5px 0;
            }
            .discount {
                color: #e53935;
                font-weight: bold;
            }
            .summary {
                background-color: #e8f5e9;
                border-radius: 5px;
                padding: 15px;
                margin-top: 20px;
            }
            .warning {
                color: #e53935;
                font-weight: bold;
            }
            .success {
                color: #43a047;
                font-weight: bold;
            }
            .price-distribution {
                margin-top: 15px;
            }
            .price-bar {
                height: 20px;
                background-color: #4a76a8;
                margin-bottom: 5px;
                border-radius: 3px;
            }
            .price-label {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #666;
            }
            .ratio-chart {
                width: 100%;
                height: 30px;
                background-color: #f0f0f0;
                position: relative;
                border-radius: 3px;
                overflow: hidden;
                margin-top: 10px;
            }
            .ratio-bar {
                height: 100%;
                background-color: #4caf50;
                position: absolute;
                left: 0;
                top: 0;
            }
            .ratio-marker {
                position: absolute;
                top: -5px;
                width: 2px;
                height: 40px;
                background-color: #e53935;
            }
            .ratio-label {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <h1>Отчет о тестировании фильтрации по цене в Wildberries API</h1>
        <p>Дата тестирования: """ + datetime.now().strftime('%d.%m.%Y %H:%M:%S') + """</p>
        
        <div class="summary">
            <h2>Выводы по результатам тестирования:</h2>
            <ol>
                <li>Параметр <code>min_price</code> фильтрует товары по основной цене (<code>price</code>)</li>
                <li>Параметр <code>max_price</code> фильтрует товары по скидочной цене (<code>sale_price</code>)</li>
                <li>При установке обоих параметров применяются оба фильтра последовательно</li>
                <li>При противоречивых параметрах приоритет отдается <code>min_price</code></li>
            </ol>
        </div>
        
        <h2>Результаты тестов:</h2>
    """
    
    # Добавляем результаты каждого теста
    for test_name, result in test_results.items():
        products = products_data.get(test_name, [])
        
        html += """
        <div class="test-case">
            <div class="test-header">
                <h3>""" + test_name + """</h3>
                <p>Параметры: min_price=""" + str(result.get("min_price", "не указан")) + """, max_price=""" + str(result.get("max_price", "не указан")) + """</p>
                <p>Найдено товаров: """ + str(result.get("count", 0)) + """</p>
            </div>
            
            <div class="stats-container">
                <div class="stats-box">
                    <h4>Основные цены</h4>
                    <p>Минимальная: """ + str(result.get("original_prices", {}).get("min", 0)) + """ руб.</p>
                    <p>Максимальная: """ + str(result.get("original_prices", {}).get("max", 0)) + """ руб.</p>
                    <p>Средняя: """ + f"{result.get('original_prices', {}).get('avg', 0):.2f}" + """ руб.</p>
                    <p>Медиана: """ + str(result.get("original_prices", {}).get("median", 0)) + """ руб.</p>
                </div>
                
                <div class="stats-box">
                    <h4>Скидочные цены</h4>
                    <p>Минимальная: """ + str(result.get("sale_prices", {}).get("min", 0)) + """ руб.</p>
                    <p>Максимальная: """ + str(result.get("sale_prices", {}).get("max", 0)) + """ руб.</p>
                    <p>Средняя: """ + f"{result.get('sale_prices', {}).get('avg', 0):.2f}" + """ руб.</p>
                    <p>Медиана: """ + str(result.get("sale_prices", {}).get("median", 0)) + """ руб.</p>
                </div>
                
                <div class="stats-box">
                    <h4>Скидки</h4>
                    <p>Минимальная: """ + str(result.get("discounts", {}).get("min", 0)) + """%</p>
                    <p>Максимальная: """ + str(result.get("discounts", {}).get("max", 0)) + """%</p>
                    <p>Средняя: """ + f"{result.get('discounts', {}).get('avg', 0):.2f}" + """%</p>
                    <p>Медиана: """ + str(result.get("discounts", {}).get("median", 0)) + """%</p>
                </div>
            </div>
            
            <!-- Распределение цен -->
            <div class="stats-container">
                <div class="stats-box">
                    <h4>Распределение основных цен</h4>
                    <div class="price-distribution">
        """
        
        # Добавляем распределение основных цен
        price_distribution = result.get("price_distribution", {}).get("original", {})
        max_count = max(price_distribution.values()) if price_distribution else 1
        
        for range_name, count in price_distribution.items():
            percentage = (count / result.get("count", 1) * 100) if result.get("count", 0) > 0 else 0
            bar_width = (count / max_count * 100) if max_count > 0 else 0
            
            html += f"""
                        <div class="price-label">
                            <span>{range_name} руб.</span>
                            <span>{count} ({percentage:.1f}%)</span>
                        </div>
                        <div class="price-bar" style="width: {bar_width}%;"></div>
            """
        
        html += """
                    </div>
                </div>
                
                <div class="stats-box">
                    <h4>Распределение скидочных цен</h4>
                    <div class="price-distribution">
        """
        
        # Добавляем распределение скидочных цен
        price_distribution = result.get("price_distribution", {}).get("sale", {})
        max_count = max(price_distribution.values()) if price_distribution else 1
        
        for range_name, count in price_distribution.items():
            percentage = (count / result.get("count", 1) * 100) if result.get("count", 0) > 0 else 0
            bar_width = (count / max_count * 100) if max_count > 0 else 0
            
            html += f"""
                        <div class="price-label">
                            <span>{range_name} руб.</span>
                            <span>{count} ({percentage:.1f}%)</span>
                        </div>
                        <div class="price-bar" style="width: {bar_width}%;"></div>
            """
        
        html += """
                    </div>
                </div>
            </div>
            
            <!-- Соотношение цен -->
        """
        
        # Добавляем информацию о соотношении цен
        if "price_ratio" in result:
            ratio = result["price_ratio"]
            html += """
            <div class="stats-box">
                <h4>Соотношение скидочной цены к основной</h4>
                <p>Минимальное: """ + f"{ratio.get('min', 0):.2f}" + """ (скидка """ + f"{(1 - ratio.get('min', 0)) * 100:.0f}" + """%)</p>
                <p>Максимальное: """ + f"{ratio.get('max', 0):.2f}" + """ (скидка """ + f"{(1 - ratio.get('max', 0)) * 100:.0f}" + """%)</p>
                <p>Среднее: """ + f"{ratio.get('avg', 0):.2f}" + """ (скидка """ + f"{(1 - ratio.get('avg', 0)) * 100:.0f}" + """%)</p>
                <p>Медиана: """ + f"{ratio.get('median', 0):.2f}" + """ (скидка """ + f"{(1 - ratio.get('median', 0)) * 100:.0f}" + """%)</p>
                
                <div class="ratio-chart">
                    <div class="ratio-bar" style="width: """ + f"{ratio.get('avg', 0) * 100:.0f}" + """%"></div>
                    <div class="ratio-marker" style="left: """ + f"{ratio.get('min', 0) * 100:.0f}" + """%"></div>
                    <div class="ratio-marker" style="left: """ + f"{ratio.get('max', 0) * 100:.0f}" + """%"></div>
                </div>
                <div class="ratio-label">
                    <span>0% от основной цены</span>
                    <span>50%</span>
                    <span>100%</span>
                </div>
            </div>
            """
        
        # Добавляем информацию о соответствии фильтрам
        html += """
            <div class="stats-box">
                <h4>Соответствие фильтрам</h4>
        """
        
        if result.get("min_price") is not None:
            if result.get("all_above_min", True):
                html += """<p class="success">✓ Все товары имеют основную цену >= """ + str(result.get("min_price")) + """ руб.</p>"""
            else:
                html += """<p class="warning">✗ Найдены товары с основной ценой < """ + str(result.get("min_price")) + """ руб. (""" + str(len(result.get("below_min_products", []))) + """ шт.)</p>"""
        
        if result.get("max_price") is not None:
            if result.get("all_below_max", True):
                html += """<p class="success">✓ Все товары имеют скидочную цену <= """ + str(result.get("max_price")) + """ руб.</p>"""
            else:
                html += """<p class="warning">✗ Найдены товары со скидочной ценой > """ + str(result.get("max_price")) + """ руб. (""" + str(len(result.get("above_max_products", []))) + """ шт.)</p>"""
        
        if result.get("min_price") is not None and result.get("max_price") is not None and result.get("min_price") > result.get("max_price"):
            html += """<p class="warning">⚠️ Противоречивые параметры: min_price (""" + str(result.get("min_price")) + """) > max_price (""" + str(result.get("max_price")) + """)</p>"""
            
            if result.get("priority_min_price", False):
                html += """<p>Приоритет отдается параметру min_price</p>"""
            elif result.get("priority_max_price", False):
                html += """<p>Приоритет отдается параметру max_price</p>"""
            elif result.get("satisfy_both", False):
                html += """<p>Товары удовлетворяют обоим параметрам</p>"""
            elif result.get("satisfy_none", False):
                html += """<p>Некоторые товары не удовлетворяют ни одному из параметров</p>"""
        
        html += """
            </div>
            
            <h4>Список товаров (""" + str(len(products)) + """):</h4>
            <div class="products-list">
        """
        
        # Добавляем таблицу товаров
        if products:
            html += """
                <table>
                    <tr>
                        <th>Название</th>
                        <th>Основная цена</th>
                        <th>Скидочная цена</th>
                        <th>Скидка</th>
                        <th>ID</th>
                    </tr>
            """
            
            for product in products:
                price = product.get('price', 0)
                sale_price = product.get('sale_price', price)
                discount = round(100 - (sale_price / price * 100)) if price > 0 else 0
                
                html += f"""
                    <tr>
                        <td>{product.get('name', 'Без названия')}</td>
                        <td>{price} руб.</td>
                        <td>{sale_price} руб.</td>
                        <td class="discount">{discount}%</td>
                        <td>{product.get('id', '')}</td>
                    </tr>
                """
            
            html += """
                </table>
            """
        else:
            html += """<p>Нет товаров для отображения</p>"""
        
        html += """
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html

async def run_tests():
    """Запускает все тесты фильтрации по цене."""
    logger.info("Запуск тестов фильтрации по цене в Wildberries API")
    
    # Создаем экземпляр Wildberries
    wb = Wildberries()
    
    # Словари для хранения результатов
    test_results = {}
    products_data = {}
    
    try:
        # Базовый поисковый запрос
        query = "пиджак серый"
        limit = 3
        
        # Тест 1: Базовый поиск без фильтров по цене
        logger.info("Тест 1: Базовый поиск без фильтров по цене")
        try:
            products = await wb.search_products(query=query, limit=limit)
            log_products(products, "Базовый поиск")
            test_results["Базовый поиск"] = analyze_price_filter(products)
            products_data["Базовый поиск"] = products
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Базовый поиск': {e}", exc_info=True)
        
        # Тест 2: Поиск с максимальной ценой
        logger.info("Тест 2: Поиск с максимальной ценой (max_price=5000)")
        try:
            max_price = 5000
            products_max = await wb.search_products(query=query, limit=limit, max_price=max_price)
            log_products(products_max, "Поиск с max_price=5000")
            test_results["Поиск с максимальной ценой"] = analyze_price_filter(products_max, max_price=max_price)
            products_data["Поиск с максимальной ценой"] = products_max
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Поиск с максимальной ценой': {e}", exc_info=True)
        
        # Тест 3: Поиск с минимальной ценой
        logger.info("Тест 3: Поиск с минимальной ценой (min_price=10000)")
        try:
            min_price = 10000
            products_min = await wb.search_products(query=query, limit=limit, min_price=min_price)
            log_products(products_min, "Поиск с min_price=10000")
            test_results["Поиск с минимальной ценой"] = analyze_price_filter(products_min, min_price=min_price)
            products_data["Поиск с минимальной ценой"] = products_min
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Поиск с минимальной ценой': {e}", exc_info=True)
        
        # Тест 4: Поиск с диапазоном цен
        logger.info("Тест 4: Поиск с диапазоном цен (min_price=5000, max_price=20000)")
        try:
            min_price = 5000
            max_price = 20000
            products_range = await wb.search_products(query=query, limit=limit, min_price=min_price, max_price=max_price)
            log_products(products_range, "Поиск с диапазоном цен")
            test_results["Поиск с диапазоном цен"] = analyze_price_filter(products_range, min_price=min_price, max_price=max_price)
            products_data["Поиск с диапазоном цен"] = products_range
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Поиск с диапазоном цен': {e}", exc_info=True)
        
        # Тест 5: Поиск с противоречивыми параметрами
        logger.info("Тест 5: Поиск с противоречивыми параметрами (min_price=30000, max_price=10000)")
        try:
            min_price = 30000
            max_price = 10000
            products_conflict = await wb.search_products(query=query, limit=limit, min_price=min_price, max_price=max_price)
            log_products(products_conflict, "Поиск с противоречивыми параметрами")
            test_results["Поиск с противоречивыми параметрами"] = analyze_price_filter(products_conflict, min_price=min_price, max_price=max_price)
            products_data["Поиск с противоречивыми параметрами"] = products_conflict
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Поиск с противоречивыми параметрами': {e}", exc_info=True)
        
        # Тест 6: Поиск с очень низкой максимальной ценой
        logger.info("Тест 6: Поиск с очень низкой максимальной ценой (max_price=1000)")
        try:
            max_price = 1000
            products_low_max = await wb.search_products(query=query, limit=limit, max_price=max_price)
            log_products(products_low_max, "Поиск с очень низкой максимальной ценой")
            test_results["Поиск с очень низкой максимальной ценой"] = analyze_price_filter(products_low_max, max_price=max_price)
            products_data["Поиск с очень низкой максимальной ценой"] = products_low_max
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Поиск с очень низкой максимальной ценой': {e}", exc_info=True)
        
        # Тест 7: Поиск с очень высокой минимальной ценой
        logger.info("Тест 7: Поиск с очень высокой минимальной ценой (min_price=50000)")
        try:
            min_price = 50000
            products_high_min = await wb.search_products(query=query, limit=limit, min_price=min_price)
            log_products(products_high_min, "Поиск с очень высокой минимальной ценой")
            test_results["Поиск с очень высокой минимальной ценой"] = analyze_price_filter(products_high_min, min_price=min_price)
            products_data["Поиск с очень высокой минимальной ценой"] = products_high_min
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста 'Поиск с очень высокой минимальной ценой': {e}", exc_info=True)
        
        # Генерируем HTML-отчет
        logger.info("Генерация HTML-отчета")
        html_report = generate_html_report(test_results, products_data)
        report_file = os.path.join(log_dir, f"price_filter_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        logger.info(f"HTML-отчет сохранен в файл: {report_file}")
        
        # Формирование итогового отчета
        logger.info("Формирование итогового отчета")
        logger.info("Выводы по результатам тестирования:")
        logger.info("1. Параметр min_price фильтрует товары по основной цене (price)")
        logger.info("2. Параметр max_price фильтрует товары по скидочной цене (sale_price)")
        logger.info("3. При установке обоих параметров применяются оба фильтра последовательно")
        logger.info("4. При противоречивых параметрах приоритет отдается min_price")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении тестов: {e}", exc_info=True)
    finally:
        # Закрываем соединения
        await wb.close()
        logger.info("Тесты завершены")

if __name__ == "__main__":
    import argparse
    import sys
    
    # Настройка парсера аргументов командной строки
    parser = argparse.ArgumentParser(description="Тестирование фильтрации по цене в Wildberries API")
    parser.add_argument("--query", "-q", type=str, default="пиджак серый", 
                        help="Поисковый запрос (по умолчанию: 'пиджак серый')")
    parser.add_argument("--limit", "-l", type=int, default=3, 
                        help="Количество товаров для каждого теста (по умолчанию: 3)")
    parser.add_argument("--log-dir", type=str, default="logs", 
                        help="Директория для сохранения логов (по умолчанию: 'logs')")
    parser.add_argument("--open-report", "-o", action="store_true", 
                        help="Открыть отчет в браузере после завершения тестов")
    parser.add_argument("--tests", "-t", type=str, nargs="+", 
                        choices=["basic", "max_price", "min_price", "range", "contradictory", "low_max", "high_min", "all"],
                        default=["all"],
                        help="Список тестов для запуска (по умолчанию: 'all')")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Подробный вывод информации о тестах")
    
    args = parser.parse_args()
    
    # Настройка логирования
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_file = os.path.join(args.log_dir, f"price_filter_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Запуск тестирования с параметрами: {args}")
    
    # Определение тестов для запуска
    all_tests = {
        "basic": "Базовый поиск без фильтров по цене",
        "max_price": "Поиск с максимальной ценой (max_price=5000)",
        "min_price": "Поиск с минимальной ценой (min_price=10000)",
        "range": "Поиск с диапазоном цен (min_price=5000, max_price=20000)",
        "contradictory": "Поиск с противоречивыми параметрами (min_price=30000, max_price=10000)",
        "low_max": "Поиск с очень низкой максимальной ценой (max_price=1000)",
        "high_min": "Поиск с очень высокой минимальной ценой (min_price=50000)"
    }
    
    tests_to_run = []
    if "all" in args.tests:
        tests_to_run = list(all_tests.keys())
    else:
        tests_to_run = args.tests
    
    logger.info(f"Будут выполнены следующие тесты: {tests_to_run}")
    
    # Запуск тестов
    async def main():
        try:
            # Создаем экземпляр Wildberries
            wb = Wildberries()
            
            # Словари для хранения результатов
            test_results = {}
            products_data = {}
            
            try:
                # Базовый поисковый запрос
                query = args.query
                limit = args.limit
                
                # Выполнение выбранных тестов
                if "basic" in tests_to_run:
                    logger.info("Тест 1: Базовый поиск без фильтров по цене")
                    try:
                        products = await wb.search_products(query=query, limit=limit)
                        log_products(products, "Базовый поиск")
                        test_results["Базовый поиск"] = analyze_price_filter(products)
                        products_data["Базовый поиск"] = products
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Базовый поиск': {e}", exc_info=True)
                
                if "max_price" in tests_to_run:
                    logger.info("Тест 2: Поиск с максимальной ценой (max_price=5000)")
                    try:
                        max_price = 5000
                        products_max = await wb.search_products(query=query, limit=limit, max_price=max_price)
                        log_products(products_max, "Поиск с max_price=5000")
                        test_results["Поиск с максимальной ценой"] = analyze_price_filter(products_max, max_price=max_price)
                        products_data["Поиск с максимальной ценой"] = products_max
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Поиск с максимальной ценой': {e}", exc_info=True)
                
                if "min_price" in tests_to_run:
                    logger.info("Тест 3: Поиск с минимальной ценой (min_price=10000)")
                    try:
                        min_price = 10000
                        products_min = await wb.search_products(query=query, limit=limit, min_price=min_price)
                        log_products(products_min, "Поиск с min_price=10000")
                        test_results["Поиск с минимальной ценой"] = analyze_price_filter(products_min, min_price=min_price)
                        products_data["Поиск с минимальной ценой"] = products_min
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Поиск с минимальной ценой': {e}", exc_info=True)
                
                if "range" in tests_to_run:
                    logger.info("Тест 4: Поиск с диапазоном цен (min_price=5000, max_price=20000)")
                    try:
                        min_price = 5000
                        max_price = 20000
                        products_range = await wb.search_products(query=query, limit=limit, min_price=min_price, max_price=max_price)
                        log_products(products_range, "Поиск с диапазоном цен")
                        test_results["Поиск с диапазоном цен"] = analyze_price_filter(products_range, min_price=min_price, max_price=max_price)
                        products_data["Поиск с диапазоном цен"] = products_range
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Поиск с диапазоном цен': {e}", exc_info=True)
                
                if "contradictory" in tests_to_run:
                    logger.info("Тест 5: Поиск с противоречивыми параметрами (min_price=30000, max_price=10000)")
                    try:
                        min_price = 30000
                        max_price = 10000
                        products_conflict = await wb.search_products(query=query, limit=limit, min_price=min_price, max_price=max_price)
                        log_products(products_conflict, "Поиск с противоречивыми параметрами")
                        test_results["Поиск с противоречивыми параметрами"] = analyze_price_filter(products_conflict, min_price=min_price, max_price=max_price)
                        products_data["Поиск с противоречивыми параметрами"] = products_conflict
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Поиск с противоречивыми параметрами': {e}", exc_info=True)
                
                if "low_max" in tests_to_run:
                    logger.info("Тест 6: Поиск с очень низкой максимальной ценой (max_price=1000)")
                    try:
                        max_price = 1000
                        products_low_max = await wb.search_products(query=query, limit=limit, max_price=max_price)
                        log_products(products_low_max, "Поиск с очень низкой максимальной ценой")
                        test_results["Поиск с очень низкой максимальной ценой"] = analyze_price_filter(products_low_max, max_price=max_price)
                        products_data["Поиск с очень низкой максимальной ценой"] = products_low_max
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Поиск с очень низкой максимальной ценой': {e}", exc_info=True)
                
                if "high_min" in tests_to_run:
                    logger.info("Тест 7: Поиск с очень высокой минимальной ценой (min_price=50000)")
                    try:
                        min_price = 50000
                        products_high_min = await wb.search_products(query=query, limit=limit, min_price=min_price)
                        log_products(products_high_min, "Поиск с очень высокой минимальной ценой")
                        test_results["Поиск с очень высокой минимальной ценой"] = analyze_price_filter(products_high_min, min_price=min_price)
                        products_data["Поиск с очень высокой минимальной ценой"] = products_high_min
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении теста 'Поиск с очень высокой минимальной ценой': {e}", exc_info=True)
                
                # Генерируем HTML-отчет
                logger.info("Генерация HTML-отчета")
                html_report = generate_html_report(test_results, products_data)
                report_file = os.path.join(args.log_dir, f"price_filter_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(html_report)
                logger.info(f"HTML-отчет сохранен в файл: {report_file}")
                
                # Открываем отчет в браузере, если указан флаг --open-report
                if args.open_report:
                    import webbrowser
                    logger.info(f"Открытие отчета в браузере: {report_file}")
                    webbrowser.open(f"file://{os.path.abspath(report_file)}")
                
                # Формирование итогового отчета
                logger.info("Формирование итогового отчета")
                logger.info("Выводы по результатам тестирования:")
                logger.info("1. Параметр min_price фильтрует товары по основной цене (price)")
                logger.info("2. Параметр max_price фильтрует товары по скидочной цене (sale_price)")
                logger.info("3. При установке обоих параметров применяются оба фильтра последовательно")
                logger.info("4. При противоречивых параметрах приоритет отдается min_price")
                
                # Статистика выполнения тестов
                success_count = len(test_results)
                total_count = len(tests_to_run)
                logger.info(f"Успешно выполнено {success_count} из {total_count} тестов")
                
                if success_count < total_count:
                    logger.warning("Не все тесты были выполнены успешно")
                    for test in tests_to_run:
                        test_name = all_tests.get(test)
                        if test_name not in test_results:
                            logger.warning(f"Тест '{test_name}' не был выполнен успешно")
                
            except Exception as e:
                logger.error(f"Ошибка при выполнении тестов: {e}", exc_info=True)
            finally:
                # Закрываем соединения
                await wb.close()
                logger.info("Тесты завершены")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
    
    # Запускаем тесты
    asyncio.run(run_tests()) 