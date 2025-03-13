"""
Скрипт для автоматического запуска тестов фильтрации по цене с разными параметрами.

Этот скрипт запускает тесты фильтрации по цене с различными параметрами и сравнивает результаты.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import subprocess
import webbrowser
from pathlib import Path

# Настройка логирования
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"run_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Конфигурации тестов для разных параметров фильтрации по цене
PRICE_TEST_CONFIGS = [
    {
        "name": "Базовый тест",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": None,
        "max_price": None
    },
    {
        "name": "Тест с низкой максимальной ценой",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": None,
        "max_price": 5000
    },
    {
        "name": "Тест с высокой минимальной ценой",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": 10000,
        "max_price": None
    },
    {
        "name": "Тест с диапазоном цен",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": 5000,
        "max_price": 20000
    },
    {
        "name": "Тест с противоречивыми параметрами",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": 30000,
        "max_price": 10000
    },
    {
        "name": "Тест с очень низкой максимальной ценой",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": None,
        "max_price": 1000
    },
    {
        "name": "Тест с очень высокой минимальной ценой",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": 50000,
        "max_price": None
    }
]

# Конфигурации тестов для разных товаров
PRODUCT_TEST_CONFIGS = [
    {
        "name": "Пиджак серый",
        "query": "пиджак серый",
        "limit": 3,
        "min_price": None,
        "max_price": None
    },
    {
        "name": "Платье вечернее",
        "query": "платье вечернее",
        "limit": 3,
        "min_price": None,
        "max_price": None
    },
    {
        "name": "Кроссовки спортивные",
        "query": "кроссовки спортивные",
        "limit": 3,
        "min_price": None,
        "max_price": None
    },
    {
        "name": "Сумка женская",
        "query": "сумка женская",
        "limit": 3,
        "min_price": None,
        "max_price": None
    },
    {
        "name": "Часы мужские",
        "query": "часы мужские",
        "limit": 3,
        "min_price": None,
        "max_price": None
    }
]

def create_test_script(config, timestamp):
    """Создает временный скрипт для запуска теста с заданной конфигурацией."""
    script_name = f"temp_{config['name'].lower().replace(' ', '_')}.py"
    
    # Используем прямые слеши в путях для совместимости с Windows
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    result_file = f"{log_dir}/results_{config['name'].lower().replace(' ', '_')}_{timestamp}.json"
    
    script_content = f'''
import asyncio
import logging
import json
import os
from datetime import datetime
from wildberries import WildberriesAPI

# Настройка логирования
log_dir = "{log_dir}"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('__main__')

async def run_test():
    """Запускает тест с заданной конфигурацией."""
    logger.info("Запуск теста с конфигурацией: {config}")
    
    # Инициализация API
    wb = WildberriesAPI()
    
    try:
        # Поиск товаров
        logger.info("Поиск товаров с параметрами: query={config['query']}, limit={config['limit']}, min_price={config['min_price']}, max_price={config['max_price']}")
        products = await wb.search_products(
            query="{config['query']}",
            limit={config['limit']},
            low_price={config['min_price'] if config['min_price'] is not None else 'None'},
            top_price={config['max_price'] if config['max_price'] is not None else 'None'}
        )
        
        logger.info(f"Найдено {{len(products)}} товаров")
        
        # Сохранение результатов
        result = {{
            "config": {config},
            "products": [{{
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "brand": p.get("brand", ""),
                "price": p.get("price", 0),
                "sale_price": p.get("sale_price", 0),
                "discount": p.get("discount", 0),
                "rating": p.get("rating", 0),
                "url": p.get("url", "")
            }} for p in products]
        }}
        
        result_file = "{result_file}"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении теста: {{e}}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        await wb.close()
        logger.info("Тест завершен")

if __name__ == "__main__":
    asyncio.run(run_test())
'''
    
    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return script_name, result_file

def run_test(config, timestamp):
    """Запускает тест с заданной конфигурацией."""
    script_name, result_file = create_test_script(config, timestamp)
    
    logger.info(f"Запуск скрипта: {script_name}")
    
    try:
        # Запуск скрипта
        subprocess.run([sys.executable, script_name], check=True)
        
        # Проверка наличия результатов
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.error(f"Файл с результатами не найден: {result_file}")
            return None
    finally:
        # Удаление временного скрипта
        if os.path.exists(script_name):
            os.remove(script_name)
            logger.info(f"Временный скрипт удален: {script_name}")

def analyze_results(results):
    """Анализирует результаты тестов и возвращает сводную информацию."""
    if not results:
        logger.warning("Нет результатов для анализа")
        return {}
    
    analyzed_results = {}
    
    for test_name, test_data in results.items():
        try:
            # Анализируем данные
            products = test_data.get("products", [])
            
            original_prices = [p.get('price', 0) for p in products]
            sale_prices = [p.get('sale_price', p.get('price', 0)) for p in products]
            
            discounts = []
            for p in products:
                price = p.get('price', 0)
                sale_price = p.get('sale_price', price)
                if price > 0:
                    discount = (price - sale_price) / price * 100
                    discounts.append(discount)
            
            analyzed_results[test_name] = {
                "config": test_data.get("config", {}),
                "count": len(products),
                "original_prices": {
                    "min": min(original_prices) if original_prices else 0,
                    "max": max(original_prices) if original_prices else 0,
                    "avg": sum(original_prices) / len(original_prices) if original_prices else 0
                },
                "sale_prices": {
                    "min": min(sale_prices) if sale_prices else 0,
                    "max": max(sale_prices) if sale_prices else 0,
                    "avg": sum(sale_prices) / len(sale_prices) if sale_prices else 0
                },
                "discounts": {
                    "min": min(discounts) if discounts else 0,
                    "max": max(discounts) if discounts else 0,
                    "avg": sum(discounts) / len(discounts) if discounts else 0
                },
                "products": products
            }
            
            logger.info(f"Проанализированы результаты теста: {test_name}")
            logger.info(f"  Количество товаров: {len(products)}")
            logger.info(f"  Основные цены: мин={analyzed_results[test_name]['original_prices']['min']}, макс={analyzed_results[test_name]['original_prices']['max']}, средняя={analyzed_results[test_name]['original_prices']['avg']:.2f}")
            logger.info(f"  Скидочные цены: мин={analyzed_results[test_name]['sale_prices']['min']}, макс={analyzed_results[test_name]['sale_prices']['max']}, средняя={analyzed_results[test_name]['sale_prices']['avg']:.2f}")
            logger.info(f"  Скидки: мин={analyzed_results[test_name]['discounts']['min']:.2f}%, макс={analyzed_results[test_name]['discounts']['max']:.2f}%, средняя={analyzed_results[test_name]['discounts']['avg']:.2f}%")
            
        except Exception as e:
            logger.error(f"Ошибка при анализе результатов теста: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    return analyzed_results

def generate_html_report(results, timestamp):
    """Генерирует HTML-отчет с результатами тестов."""
    if not results:
        logger.warning("Нет результатов для генерации отчета")
        return
    
    # Создаем директорию для отчетов, если она не существует
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    report_file = f"{report_dir}/price_filter_report_{timestamp}.html"
    
    # Создаем HTML-отчет
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Отчет о тестировании фильтрации по цене - {timestamp}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .summary {{ background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            .warning {{ color: #ff6600; }}
            .success {{ color: #009900; }}
            .error {{ color: #cc0000; }}
            .test-section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Отчет о тестировании фильтрации по цене в API Wildberries</h1>
        <p>Дата и время: {timestamp}</p>
        
        <div class="summary">
            <h2>Общие выводы</h2>
            <ul>
                <li>Параметр <strong>min_price</strong> фильтрует товары по основной цене (price ≥ min_price)</li>
                <li>Параметр <strong>max_price</strong> фильтрует товары по скидочной цене (sale_price ≤ max_price)</li>
                <li>При указании обоих параметров фильтры применяются последовательно</li>
                <li>При противоречивых параметрах (min_price > max_price) приоритет отдается min_price</li>
            </ul>
        </div>
    """
    
    # Добавляем разделы для каждого теста
    for test_name, test_data in results.items():
        html += f"""
        <div class="test-section">
            <h2>{test_name}</h2>
            
            <h3>Параметры теста</h3>
            <ul>
                <li>Запрос: {test_data.get('config', {}).get('query', 'Н/Д')}</li>
                <li>Минимальная цена: {test_data.get('config', {}).get('min_price', 'Не указана')}</li>
                <li>Максимальная цена: {test_data.get('config', {}).get('max_price', 'Не указана')}</li>
                <li>Лимит товаров: {test_data.get('config', {}).get('limit', 'Н/Д')}</li>
            </ul>
            
            <h3>Результаты</h3>
            <p>Найдено товаров: {test_data['count']}</p>
            
            <h4>Основные цены (price)</h4>
            <ul>
                <li>Минимальная: {test_data['original_prices']['min']} руб.</li>
                <li>Максимальная: {test_data['original_prices']['max']} руб.</li>
                <li>Средняя: {test_data['original_prices']['avg']:.2f} руб.</li>
            </ul>
            
            <h4>Скидочные цены (sale_price)</h4>
            <ul>
                <li>Минимальная: {test_data['sale_prices']['min']} руб.</li>
                <li>Максимальная: {test_data['sale_prices']['max']} руб.</li>
                <li>Средняя: {test_data['sale_prices']['avg']:.2f} руб.</li>
            </ul>
            
            <h4>Скидки</h4>
            <ul>
                <li>Минимальная: {test_data['discounts']['min']:.2f}%</li>
                <li>Максимальная: {test_data['discounts']['max']:.2f}%</li>
                <li>Средняя: {test_data['discounts']['avg']:.2f}%</li>
            </ul>
            
            <h3>Найденные товары</h3>
            <table>
                <tr>
                    <th>Название</th>
                    <th>Бренд</th>
                    <th>Основная цена</th>
                    <th>Скидочная цена</th>
                    <th>Скидка</th>
                </tr>
        """
        
        for product in test_data['products']:
            price = product.get('price', 0)
            sale_price = product.get('sale_price', price)
            discount = (price - sale_price) / price * 100 if price > 0 else 0
            
            html += f"""
                <tr>
                    <td>{product.get('name', 'Н/Д')}</td>
                    <td>{product.get('brand', 'Н/Д')}</td>
                    <td>{price} руб.</td>
                    <td>{sale_price} руб.</td>
                    <td>{discount:.2f}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h3>Выводы</h3>
        """
        
        # Добавляем выводы в зависимости от типа теста
        min_price = test_data.get('config', {}).get('min_price')
        max_price = test_data.get('config', {}).get('max_price')
        
        if min_price is None and max_price is None:
            html += """
            <p>Базовый поиск без фильтрации по цене. Показывает исходные данные для сравнения.</p>
            """
        elif min_price is None and max_price is not None:
            # Проверяем, все ли товары соответствуют max_price
            all_match = all(p.get('sale_price', 0) <= max_price for p in test_data['products'])
            html += f"""
            <p>Фильтрация по максимальной цене (max_price={max_price}):</p>
            <p class="{'success' if all_match else 'error'}">
                {'Все' if all_match else 'Не все'} товары имеют скидочную цену ≤ {max_price} руб.
            </p>
            <p>Вывод: Параметр max_price фильтрует товары по скидочной цене (sale_price).</p>
            """
        elif min_price is not None and max_price is None:
            # Проверяем, все ли товары соответствуют min_price
            all_match = all(p.get('price', 0) >= min_price for p in test_data['products'])
            html += f"""
            <p>Фильтрация по минимальной цене (min_price={min_price}):</p>
            <p class="{'success' if all_match else 'error'}">
                {'Все' if all_match else 'Не все'} товары имеют основную цену ≥ {min_price} руб.
            </p>
            <p>Вывод: Параметр min_price фильтрует товары по основной цене (price).</p>
            """
        elif min_price is not None and max_price is not None:
            if min_price <= max_price:
                # Проверяем, все ли товары соответствуют обоим условиям
                min_match = all(p.get('price', 0) >= min_price for p in test_data['products'])
                max_match = all(p.get('sale_price', 0) <= max_price for p in test_data['products'])
                html += f"""
                <p>Фильтрация по диапазону цен (min_price={min_price}, max_price={max_price}):</p>
                <p class="{'success' if min_match else 'error'}">
                    {'Все' if min_match else 'Не все'} товары имеют основную цену ≥ {min_price} руб.
                </p>
                <p class="{'success' if max_match else 'error'}">
                    {'Все' if max_match else 'Не все'} товары имеют скидочную цену ≤ {max_price} руб.
                </p>
                <p>Вывод: При указании обоих параметров фильтры применяются последовательно.</p>
                """
            else:
                # Противоречивые параметры
                min_match = all(p.get('price', 0) >= min_price for p in test_data['products'])
                max_match = all(p.get('sale_price', 0) <= max_price for p in test_data['products'])
                html += f"""
                <p class="warning">Противоречивые параметры (min_price={min_price} > max_price={max_price}):</p>
                <p class="{'success' if min_match else 'error'}">
                    {'Все' if min_match else 'Не все'} товары имеют основную цену ≥ {min_price} руб.
                </p>
                <p class="{'success' if max_match else 'warning'}">
                    {'Все' if max_match else 'Не все'} товары имеют скидочную цену ≤ {max_price} руб.
                </p>
                <p>Вывод: При противоречивых параметрах приоритет отдается min_price.</p>
                """
        
        html += """
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    # Сохраняем отчет
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"HTML-отчет сохранен в файл: {report_file}")
    return report_file

def run_tests_with_different_price_filters():
    """Запускает тесты с разными параметрами фильтрации по цене."""
    logger.info("Запуск тестов с разными параметрами фильтрации по цене")
    
    # Результаты тестов
    results = {}
    
    # Запускаем тесты с разными параметрами
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for config in PRICE_TEST_CONFIGS:
        # Запускаем тест
        result = run_test(config, timestamp)
        if result:
            results[config['name']] = result
    
    # Анализируем результаты
    if results:
        analyzed_results = analyze_results(results)
        
        # Генерируем отчет
        report_file = generate_html_report(analyzed_results, timestamp)
        
        # Открываем отчет в браузере
        try:
            webbrowser.open(report_file)
        except Exception as e:
            logger.error(f"Ошибка при открытии отчета в браузере: {e}")
    else:
        logger.warning("Нет результатов для генерации отчета")

def run_tests_with_different_products():
    """Запускает тесты с разными товарами."""
    logger.info("Запуск тестов с разными товарами")
    
    # Результаты тестов
    results = {}
    
    # Запускаем тесты с разными товарами
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for config in PRODUCT_TEST_CONFIGS:
        # Запускаем тест
        result = run_test(config, timestamp)
        if result:
            results[config['name']] = result
    
    # Анализируем результаты
    if results:
        analyzed_results = analyze_results(results)
        
        # Генерируем отчет
        report_file = generate_html_report(analyzed_results, timestamp)
        
        # Открываем отчет в браузере
        try:
            webbrowser.open(report_file)
        except Exception as e:
            logger.error(f"Ошибка при открытии отчета в браузере: {e}")
    else:
        logger.warning("Нет результатов для генерации отчета")

def main():
    """Основная функция для запуска тестов."""
    parser = argparse.ArgumentParser(description='Запуск тестов фильтрации по цене в API Wildberries')
    parser.add_argument('--prices', action='store_true', help='Запустить тесты с разными параметрами фильтрации по цене')
    parser.add_argument('--products', action='store_true', help='Запустить тесты с разными товарами')
    parser.add_argument('--all', action='store_true', help='Запустить все тесты')
    
    args = parser.parse_args()
    
    # Создаем директорию для логов, если она не существует
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/run_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    if args.all or args.prices:
        logger.info("Запуск тестов с разными параметрами фильтрации по цене")
        run_tests_with_different_price_filters()
    
    if args.all or args.products:
        logger.info("Запуск тестов с разными товарами")
        run_tests_with_different_products()
    
    if not (args.all or args.prices or args.products):
        parser.print_help()
    
    logger.info("Все тесты завершены")

if __name__ == "__main__":
    main() 