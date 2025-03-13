#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестирование парсера банковских выписок на реальном примере выписки Тинькофф.
"""

import os
import pandas as pd
from pathlib import Path
import logging

# Импортируем парсер банковских выписок
from bank_statement_parser import BankStatementParser

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_real_statement.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_real_statement():
    """
    Тестирует парсер на реальном примере выписки.
    """
    try:
        print("Тестирование парсера на реальном примере выписки Тинькофф...")
        
        # Путь к примеру выписки
        test_file_path = "static/bank_statements/examples/tinkoff_example.txt"
        
        # Создаем экземпляр парсера
        parser = BankStatementParser()
        
        # Открываем файл и читаем его содержимое
        with open(test_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Выводим первые несколько строк для отладки
        print("\nПервые 10 строк выписки:")
        for i, line in enumerate(text.split('\n')[:10]):
            print(f"{i+1}: {line}")
        
        # Тестируем извлечение метаданных из выписки
        print("\nИзвлечение метаданных:")
        metadata = parser._extract_statement_metadata(text)
        print("Извлеченные метаданные:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        # Тестируем извлечение транзакций
        print("\nИзвлечение транзакций:")
        transactions = parser._extract_transactions_from_text(text)
        print(f"Извлечено {len(transactions)} транзакций")
        
        if transactions:
            # Выводим первые 5 транзакций для проверки
            print("\nПервые 5 транзакций:")
            for i, transaction in enumerate(transactions[:5]):
                print(f"Транзакция {i+1}:")
                for key, value in transaction.items():
                    print(f"  {key}: {value}")
    
            # Создаем DataFrame из транзакций
            df = pd.DataFrame(transactions)
            
            # Добавляем метаданные
            for key, value in metadata.items():
                df[key] = value
            
            # Анализируем расходы по категориям
            print("\nАнализ расходов по категориям:")
            category_spending = parser.analyze_spending_by_category(df)
            print(category_spending)
            
            # Генерируем отчет
            print("\nГенерация отчета о расходах:")
            report = parser.generate_spending_report(df, output_dir="reports/bank_analytics/real")
            
            print(f"Общая сумма расходов: {report['total_expenses']:.2f} руб.")
            print(f"Отчет сохранен в директории: reports/bank_analytics/real")
            
            # Выводим метаданные из отчета
            print("\nМетаданные в отчете:")
            for key, value in report["metadata"].items():
                print(f"  {key}: {value}")
            
            # Выводим пути к визуализациям
            print("\nСгенерированные визуализации:")
            for desc, path in report["visualization_files"].items():
                print(f"{desc}: {path}")
        else:
            print("Не удалось извлечь транзакции из файла выписки")
        
        print("\nТестирование парсера на реальном примере выписки завершено.")
    except Exception as e:
        logger.exception(f"Произошла ошибка при тестировании: {e}")
        print(f"Произошла ошибка при тестировании: {e}")
        raise

if __name__ == "__main__":
    test_real_statement() 