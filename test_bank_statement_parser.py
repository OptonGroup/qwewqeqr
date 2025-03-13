#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки функциональности парсера банковских выписок.
Генерирует тестовые данные транзакций и проверяет все методы BankStatementParser.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
import csv
import json
import logging
from pathlib import Path

# Импортируем парсер банковских выписок
from bank_statement_parser import BankStatementParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_bank_statement.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_test_transactions(num_transactions: int = 100, 
                             start_date: datetime = datetime(2023, 1, 1),
                             end_date: datetime = datetime(2023, 12, 31)) -> pd.DataFrame:
    """
    Генерирует тестовые данные транзакций для тестирования парсера банковских выписок.
    
    Args:
        num_transactions: Количество транзакций для генерации.
        start_date: Начальная дата для генерации транзакций.
        end_date: Конечная дата для генерации транзакций.
        
    Returns:
        DataFrame с тестовыми данными транзакций.
    """
    # Категории транзакций и примеры описаний
    category_descriptions = {
        "Продукты": [
            "Магазин Пятерочка", "Магнит у дома", "Перекресток", "ВкусВилл", 
            "АШАН", "Азбука Вкуса", "Лента Гипермаркет", "Продукты 24"
        ],
        "Рестораны": [
            "Кафе у Антона", "Суши WOK", "Макдоналдс", "Бургер Кинг", 
            "KFC", "Delivery Club", "Яндекс Еда", "Кофейня Coffee Like"
        ],
        "Одежда": [
            "Магазин ZARA", "H&M", "Gloria Jeans", "Спортмастер", 
            "Детский Мир", "OSTIN", "Wildberries", "Lamoda"
        ],
        "Транспорт": [
            "Яндекс Такси", "Uber", "Метрополитен", "Автобус", 
            "АЗС Лукойл", "Троллейбус", "Электричка", "Трамвай"
        ],
        "Развлечения": [
            "Кинотеатр", "Театр оперы и балета", "Музей современного искусства", 
            "Концерт", "PlayStation Store", "Xbox Game Pass", "Боулинг центр"
        ],
        "Переводы": [
            "Перевод Иванову И.И.", "Пополнение счета", "Перевод по СБП", 
            "Внутрибанковский перевод", "Перевод с договора", "Перевод Петрову П.П."
        ],
        "Снятие наличных": [
            "Снятие в банкомате", "Снятие наличных в кассе", "Выдача наличных ATM", 
            "Получение наличных"
        ],
        "Комиссии и обслуживание": [
            "Комиссия за перевод", "Плата за обслуживание", "Ежемесячная комиссия", 
            "Обслуживание карты"
        ]
    }
    
    # Генерируем случайные транзакции
    transactions = []
    date_range = (end_date - start_date).days
    
    for _ in range(num_transactions):
        # Выбираем случайную категорию
        category = random.choice(list(category_descriptions.keys()))
        
        # Выбираем случайное описание для этой категории
        description = random.choice(category_descriptions[category])
        
        # Генерируем случайную дату и время
        random_day = random.randint(0, date_range)
        transaction_date = start_date + timedelta(days=random_day)
        
        # Генерируем случайное время
        hours = random.randint(8, 22)
        minutes = random.randint(0, 59)
        transaction_time = f"{hours:02d}:{minutes:02d}"
        
        # Дата списания может отличаться от даты операции на 0-1 день
        clearing_delay = random.randint(0, 1)
        clearing_date = transaction_date + timedelta(days=clearing_delay)
        
        # Время списания
        clearing_hours = random.randint(8, 22)
        clearing_minutes = random.randint(0, 59)
        clearing_time = f"{clearing_hours:02d}:{clearing_minutes:02d}"
        
        # Генерируем случайную сумму (отрицательную для расходов)
        amount = -1 * round(random.uniform(100, 5000), 2)
        
        # С вероятностью 20% создаем положительную транзакцию (доход)
        if random.random() < 0.2:
            amount = abs(amount)
            description = "Зарплата" if random.random() < 0.7 else "Перевод от друга"
            category = "Доход"
        
        # Генерируем случайный идентификатор транзакции
        transaction_id = str(random.randint(1000, 9999))
        
        # Форматируем даты как строки в формате дд.мм.гггг
        transaction_date_str = transaction_date.strftime("%d.%m.%Y")
        clearing_date_str = clearing_date.strftime("%d.%m.%Y")
        
        transactions.append({
            "Дата_операции": transaction_date,
            "Время_операции": transaction_time,
            "Дата_списания": clearing_date,
            "Время_списания": clearing_time,
            "Сумма": amount,
            "Сумма_в_валюте_счета": amount,  # Предполагаем, что валюта счета совпадает с валютой операции
            "Описание": description,
            "Идентификатор": transaction_id,
            "Категория": category,
            "Тип": "Доход" if amount > 0 else "Расход"
        })
    
    # Создаем DataFrame
    df = pd.DataFrame(transactions)
    
    # Сортируем по дате
    df = df.sort_values("Дата_операции")
    
    # Добавляем метаданные
    df["Номер_договора"] = "5567106297"
    df["Номер_счета"] = "40817810000080628894"
    df["Дата_договора"] = "04.02.2023"
    df["Период_с"] = start_date.strftime("%d.%m.%Y")
    df["Период_по"] = end_date.strftime("%d.%m.%Y")
    df["ФИО"] = "Воронцов Кирилл Владиславович"
    
    return df

def generate_tinkoff_statement_text(transactions_df: pd.DataFrame) -> str:
    """
    Генерирует текстовое представление выписки Тинькофф из DataFrame с транзакциями.
    
    Args:
        transactions_df: DataFrame с транзакциями.
        
    Returns:
        Текстовое представление выписки Тинькофф.
    """
    # Получаем метаданные выписки
    if transactions_df.empty:
        return "Нет данных для создания выписки"
    
    # Извлекаем метаданные из первой строки
    номер_договора = transactions_df["Номер_договора"].iloc[0]
    номер_счета = transactions_df["Номер_счета"].iloc[0]
    дата_договора = transactions_df["Дата_договора"].iloc[0]
    период_с = transactions_df["Период_с"].iloc[0]
    период_по = transactions_df["Период_по"].iloc[0]
    фио = transactions_df["ФИО"].iloc[0]
    
    # Формируем заголовок выписки
    header = f"""Справка о движении средств
Исх. № e016e33                                                            {период_по}

{фио}
Адрес места жительства:

О продукте
Дата заключения договора: {дата_договора}
Номер договора: {номер_договора}
Номер лицевого счета: {номер_счета}

Движение средств за период с {период_с} по {период_по}

"""
    
    # Добавляем заголовок таблицы транзакций
    table_header = "Дата и время операции | Дата списания | Сумма в валюте операции | Сумма в валюте счета | Описание операции | Номер операции\n"
    header += table_header + "-" * 120 + "\n"
    
    # Формируем строки с транзакциями
    transaction_lines = []
    for _, row in transactions_df.iterrows():
        # Форматируем суммы с пробелами и знаком валюты
        сумма_форматированная = f"{'+' if row['Сумма'] > 0 else ''}{row['Сумма']:.2f} ₽".replace(".", ",")
        сумма_счета_форматированная = f"{'+' if row['Сумма_в_валюте_счета'] > 0 else ''}{row['Сумма_в_валюте_счета']:.2f} ₽".replace(".", ",")
        
        # Форматируем даты и время
        дата_операции_str = row["Дата_операции"].strftime("%d.%m.%Y") if isinstance(row["Дата_операции"], (datetime, pd.Timestamp)) else row["Дата_операции"]
        дата_списания_str = row["Дата_списания"].strftime("%d.%m.%Y") if isinstance(row["Дата_списания"], (datetime, pd.Timestamp)) else row["Дата_списания"]
        
        # Формируем строку транзакции
        transaction_line = f"{дата_операции_str} {row['Время_операции']} | {дата_списания_str} | {сумма_форматированная} | {сумма_счета_форматированная} | {row['Описание']} | {row['Идентификатор']}"
        transaction_lines.append(transaction_line)
    
    # Объединяем заголовок и транзакции
    statement_text = header + "\n".join(transaction_lines)
    
    return statement_text

def save_test_transactions_as_csv(df: pd.DataFrame, file_path: str) -> None:
    """
    Сохраняет тестовые транзакции в CSV-файл.
    
    Args:
        df: DataFrame с транзакциями.
        file_path: Путь для сохранения CSV-файла.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.info(f"Тестовые транзакции сохранены в {file_path}")

def save_test_statement_as_text(statement_text: str, file_path: str) -> None:
    """
    Сохраняет текстовое представление выписки в файл.
    
    Args:
        statement_text: Текстовое представление выписки.
        file_path: Путь для сохранения файла.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(statement_text)
    logger.info(f"Текстовое представление выписки сохранено в {file_path}")

def test_bank_statement_parser():
    """
    Тестирует функциональность парсера банковских выписок.
    """
    print("Запуск тестирования парсера банковских выписок...")
    
    # Генерируем тестовые данные
    test_transactions = generate_test_transactions(
        num_transactions=200,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    
    print(f"Сгенерировано {len(test_transactions)} тестовых транзакций")
    
    # Сохраняем тестовые данные в CSV-файл
    test_data_path = "static/bank_statements/test_transactions.csv"
    save_test_transactions_as_csv(test_transactions, test_data_path)
    
    # Генерируем текстовое представление выписки Тинькофф
    test_statement_text = generate_tinkoff_statement_text(test_transactions)
    
    # Сохраняем текстовое представление выписки в файл
    test_statement_path = "static/bank_statements/test_statement.txt"
    save_test_statement_as_text(test_statement_text, test_statement_path)
    
    # Создаем экземпляр парсера
    parser = BankStatementParser()
    
    # Тестируем извлечение метаданных из выписки
    print("\nТестирование извлечения метаданных:")
    metadata = parser._extract_statement_metadata(test_statement_text)
    print("Извлеченные метаданные:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    # Тестируем извлечение транзакций из текста выписки
    print("\nТестирование извлечения транзакций из текста:")
    transactions = parser._extract_transactions_from_text(test_statement_text)
    print(f"Извлечено {len(transactions)} транзакций из текста выписки")
    
    # Тестируем анализ расходов по категориям
    print("\nАнализ расходов по категориям:")
    category_spending = parser.analyze_spending_by_category(test_transactions)
    print(category_spending.head())
    
    # Тестируем получение тренда расходов по месяцам
    print("\nТренд расходов по месяцам:")
    monthly_spending = parser.get_monthly_spending_trend(test_transactions)
    print(monthly_spending.head())
    
    # Тестируем прогноз будущих расходов
    print("\nПрогноз будущих расходов:")
    future_spending = parser.predict_future_spending(test_transactions)
    for category, amount in sorted(future_spending.items(), key=lambda x: x[1], reverse=True):
        print(f"{category}: {amount:.2f} руб.")
    
    # Тестируем генерацию отчета
    print("\nГенерация отчета о расходах:")
    report = parser.generate_spending_report(test_transactions, output_dir="reports/bank_analytics/test")
    
    print(f"Общая сумма расходов: {report['total_expenses']:.2f} руб.")
    print(f"Отчет сохранен в директории: reports/bank_analytics/test")
    
    # Проверяем метаданные в отчете
    print("\nМетаданные в отчете:")
    for key, value in report["metadata"].items():
        print(f"  {key}: {value}")
    
    # Отображаем пути к сгенерированным визуализациям
    print("\nСгенерированные визуализации:")
    for desc, path in report["visualization_files"].items():
        print(f"{desc}: {path}")
    
    print("\nТестирование парсера банковских выписок завершено.")

if __name__ == "__main__":
    test_bank_statement_parser() 