#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для анализа банковских выписок Тинькофф банка.
Позволяет извлекать данные о транзакциях из PDF-файлов выписок,
анализировать расходы по категориям и создавать визуализацию данных.
"""

import os
import re
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import pandas as pd
import pdfplumber
import matplotlib.pyplot as plt
from pathlib import Path
import copy
import numpy as np

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bank_statement.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BankStatementParser:
    """
    Класс для парсинга и анализа банковских выписок Тинькофф.
    """
    
    # Категории транзакций и ключевые слова для классификации
    TRANSACTION_CATEGORIES = {
        "Продукты": ["ашан", "перекресток", "магнит", "пятерочка", "лента", "вкусвилл", "азбука вкуса",
                    "продукты", "супермаркет", "гипермаркет", "бакалея", "фрукты", "овощи", "лента супермаркет",
                    "пятерочка", "metro", "окей", "дикси", "продукты", "супермаркет", "гастроном"],
        "Рестораны": ["ресторан", "кафе", "бар", "фастфуд", "макдоналдс", "kfc", "бургер кинг", "coffee",
                     "кофейня", "суши", "пицца", "delivery club", "яндекс еда", "деливери", "якитория", 
                     "додо пицца", "вкусно и точка", "теремок", "шоколадница", "кофе хауз", "burger king"],
        "Одежда": ["одежда", "zara", "h&m", "твоё", "ostin", "обувь", "wildberries", "lamoda", "ozon",
                  "gloria jeans", "detmir", "детский мир", "спортмастер", "uniqlo", "gap", "street beat", 
                  "rendez-vous", "lamoda", "kari", "fashion", "kiabi", "mango", "adidas", "nike"],
        "Транспорт": ["яндекс такси", "uber", "такси", "метро", "троллейбус", "автобус", "маршрутка",
                     "электричка", "автозаправка", "азс", "транспорт", "проезд", "автомойка", "парковка",
                     "каршеринг", "делимобиль", "ситимобил", "яндекс go", "gett", "метрополитен"],
        "Развлечения": ["кино", "театр", "концерт", "музей", "выставка", "боулинг", "квест", "park",
                       "парк", "развлечения", "игры", "sony", "playstation", "xbox", "nintendo", "билеты", 
                       "кинотеатр", "формула кино", "кинопоиск", "окко", "иви", "амедиатека", "сериалы", 
                       "синема парк", "karaoke", "караоке", "netflix", "steam", "epic games"],
        "Красота": ["салон", "парикмахерская", "маникюр", "спа", "косметика", "л'этуаль", "иль де ботэ",
                   "ив роше", "уход", "стрижка", "окрашивание", "барбершоп", "стрижка", "массаж", "лэтуаль", 
                   "лэтуаль", "елизавета", "золотое яблоко", "sephora", "макияж", "eyebrows", "ресницы", "tattoo", "тату"],
        "Здоровье": ["аптека", "клиника", "больница", "врач", "стоматолог", "анализы", "лекарства", 
                    "медицина", "массаж", "оздоровление", "36.6", "здоровье", "доктор", "горздрав", "столички", 
                    "инвитро", "ситилаб", "гемотест", "стоматология", "вита", "витамины", "невролог", "окулист", "аллерголог"],
        "Жилье": ["аренда", "ипотека", "жкх", "квартплата", "электроэнергия", "газ", "вода", "отопление",
                 "коммунальные", "управляющая компания", "тсж", "квартира", "дом", "мосэнергосбыт", "комуслуги", 
                 "мосводоканал", "жилищник", "жилищный", "ук", "арендная плата", "арендодатель", "домофон", "консьерж"],
        "Связь": ["мтс", "билайн", "мегафон", "теле2", "tele2", "yota", "сотовая связь", "интернет",
                 "роутер", "wifi", "домашний интернет", "тв", "телевидение", "цифровое тв", "телеком", "связной", 
                 "ростелеком", "модем", "мобильный", "wi-fi", "4g", "провайдер", "сотовый", "сим-карта", "sim", "gsm"],
        "Подписки": ["netflix", "spotify", "apple", "google", "яндекс плюс", "кинопоиск", "амедиатека",
                    "подписка", "subscription", "icloud", "onedrive", "dropbox", "youtube", "premium", "иви", "ivi", 
                    "more.tv", "оплата подписки", "триал", "trial", "подписка продлена", "app store", "play market"],
        "Техника": ["м.видео", "эльдорадо", "dns", "ситилинк", "технопарк", "компьютер", "ноутбук",
                   "смартфон", "телефон", "планшет", "техника", "electronics", "гаджет", "re:store", "apple", 
                   "xiaomi", "samsung", "huawei", "sony", "lg", "техносила", "технопарк", "мобильный", "бытовая техника"],
        "Образование": ["курсы", "обучение", "образование", "книги", "читай-город", "буквоед", "литрес",
                       "школа", "университет", "вуз", "репетитор", "тренинг", "семинар", "workshop", "учебник", 
                       "колледж", "академия", "дополнительное образование", "повышение квалификации", "вебинар", 
                       "мастер-класс", "скилбокс", "skillbox", "нетология", "geekbrains", "coursera", "udemy"],
        "Переводы": ["перевод", "пополнение", "карта", "счет", "сбп", "система быстрых платежей", "p2p", 
                    "card2card", "внутренний перевод", "внешний перевод", "перевод между счетами", "от", "в пользу",
                    "зачисление", "снятие", "перевод клиенту", "перевод от клиента", "пополнение счета", "внутрибанковский перевод"],
        "Комиссии и обслуживание": ["комиссия", "обслуживание", "банковское обслуживание", "плата за", 
                                  "абонентская плата", "годовое обслуживание", "ежемесячная комиссия", "плата за выписку", 
                                  "за обслуживание", "за перевод", "плата за снятие", "конвертация"],
        "Снятие наличных": ["снятие", "наличные", "банкомат", "cash", "снятие наличных", "выдача наличных", 
                          "atm", "получение наличных", "кассовая операция", "касса"]
    }

    def __init__(self, cache_dir: str = "bank_statements_cache"):
        """
        Инициализирует парсер банковских выписок.
        
        Args:
            cache_dir: Директория для хранения кэша обработанных выписок.
        """
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Инициализация логгера
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            # Добавляем обработчики логирования, если их еще нет
            file_handler = logging.FileHandler("bank_statement_parser.log", encoding="utf-8")
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.logger.info(f"Инициализирован парсер банковских выписок с кэшем в директории: {self.cache_dir}")
    
    def parse_pdf_statement(self, file_path: Union[str, Path], force_reparse: bool = False) -> pd.DataFrame:
        """
        Парсит PDF-файл выписки Тинькофф и извлекает информацию о транзакциях.
        
        Args:
            file_path: Путь к PDF-файлу выписки.
            force_reparse: Принудительно перепарсить файл, даже если есть кэшированные результаты.
            
        Returns:
            DataFrame с данными о транзакциях.
        """
        file_path = Path(file_path)
        cache_file = Path(self.cache_dir) / f"{file_path.stem}_transactions.csv"
        
        # Проверяем, есть ли кэшированные результаты
        if cache_file.exists() and not force_reparse:
            self.logger.info(f"Используем кэшированные данные транзакций из {cache_file}")
            return pd.read_csv(cache_file, parse_dates=["Дата_операции", "Дата_списания"])
        
        try:
            self.logger.info(f"Начинаем парсинг PDF-файла: {file_path}")
            all_transactions = []
            metadata = {}
            
            with pdfplumber.open(file_path) as pdf:
                # Парсим метаданные из первой страницы
                if len(pdf.pages) > 0:
                    first_page_text = pdf.pages[0].extract_text()
                    metadata = self._extract_statement_metadata(first_page_text)
                    self.logger.info(f"Извлечены метаданные выписки: {metadata}")
                
                # Парсим транзакции со всех страниц
                for page_num, page in enumerate(pdf.pages):
                    self.logger.debug(f"Обрабатываем страницу {page_num+1} из {len(pdf.pages)}")
                    text = page.extract_text()
                    
                    page_transactions = self._extract_transactions_from_text(text)
                    all_transactions.extend(page_transactions)
                
                self.logger.info(f"Извлечено {len(all_transactions)} транзакций из PDF-файла")
                
                # Создаем DataFrame из списка транзакций
                if all_transactions:
                    transactions_df = pd.DataFrame(all_transactions)
                    
                    # Добавляем метаданные, если они есть
                    for key, value in metadata.items():
                        transactions_df[key] = value
                    
                    # Сортируем по дате операции
                    transactions_df = transactions_df.sort_values("Дата_операции")
                    
                    # Сохраняем в кэш
                    transactions_df.to_csv(cache_file, index=False)
                    self.logger.info(f"Транзакции сохранены в кэше: {cache_file}")
                    
                    return transactions_df
                else:
                    self.logger.warning(f"Не удалось извлечь транзакции из PDF-файла: {file_path}")
                    return pd.DataFrame()
        
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге PDF-файла {file_path}: {e}")
            return pd.DataFrame()
    
    def _extract_statement_metadata(self, text: str) -> dict:
        """
        Извлекает метаданные из текста выписки банка.
        
        Args:
            text: Текст выписки.
            
        Returns:
            Словарь с метаданными.
        """
        metadata = {
            "Номер_договора": "",
            "Номер_счета": "",
            "Дата_договора": "",
            "Период_с": "",
            "Период_по": "",
            "ФИО": ""
        }
        
        # Поиск номера договора - оба варианта форматирования
        match = re.search(r'Номер договора:?\s*(\d+)', text)
        if match:
            metadata["Номер_договора"] = match.group(1)
        
        # Поиск номера лицевого счета - оба варианта форматирования
        match = re.search(r'Номер лицевого счета:?\s*(\d+)', text)
        if match:
            metadata["Номер_счета"] = match.group(1)
        
        # Поиск даты заключения договора
        match = re.search(r'Дата заключения договора:?\s*(\d{2}\.\d{2}\.\d{4})', text)
        if match:
            metadata["Дата_договора"] = match.group(1)
        
        # Поиск периода выписки
        match = re.search(r'Движение средств за период с (\d{2}\.\d{2}\.\d{4}) по (\d{2}\.\d{2}\.\d{4})', text)
        if match:
            metadata["Период_с"] = match.group(1)
            metadata["Период_по"] = match.group(2)
        
        # Поиск ФИО клиента
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if i > 0 and i < 15:
                # Ищем строку, которая может содержать ФИО (обычно после "Исх. No" или "АО «ТБанк»")
                if re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+$', line.strip()):
                    metadata["ФИО"] = line.strip()
                    break
        
        return metadata

    def _extract_transactions_from_text(self, text: str) -> list:
        """
        Извлекает данные о транзакциях из текста выписки банка.
        
        Args:
            text: Текст выписки.
            
        Returns:
            Список словарей с данными о транзакциях.
        """
        transactions = []
        
        # Поиск начала таблицы с транзакциями
        lines = text.split('\n')
        start_idx = -1
        
        # Ищем строку с заголовком "Движение средств за период"
        for i, line in enumerate(lines):
            if "Движение средств за период" in line:
                start_idx = i + 3  # Пропускаем заголовок и строку заголовков таблицы
                self.logger.debug(f"Найден заголовок 'Движение средств за период' в строке {i}: {line}")
                self.logger.debug(f"Предполагаемые заголовки: {lines[i+1] if i+1 < len(lines) else 'нет'}")
                self.logger.debug(f"Предполагаемая первая строка данных: {lines[i+2] if i+2 < len(lines) else 'нет'}")
                break
        
        if start_idx == -1 or start_idx >= len(lines):
            self.logger.warning("Не удалось найти таблицу с транзакциями в тексте выписки")
            return transactions
        
        # Начинаем собирать транзакции из таблицы
        i = start_idx
        
        # Строка шаблона для четырех групп: дата/время операции, дата списания, сумма в валюте операции, сумма в валюте карты
        pattern = re.compile(r'(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})\s+(\d{2}\.\d{2}\.\d{4})\s+([\+\-][\d\s\.]+₽)\s+([\+\-][\d\s\.]+₽)')
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Пропуск пустых строк
            if not line or line.isspace():
                i += 1
                continue
            
            # Проверка конца таблицы
            if "АО «ТБанк»" in line or "БИК" in line or "универсальная лицензия" in line:
                self.logger.debug(f"Обнаружен конец таблицы в строке {i}: {line}")
                break
            
            # Проверяем, является ли строка началом транзакции (содержит дату и время)
            match = pattern.match(line)
            
            if match:
                self.logger.debug(f"Обнаружена строка транзакции {i}: {line}")
                
                # Извлекаем основные данные
                date_time_op = match.group(1)
                date_clearing = match.group(2)
                amount_currency_str = match.group(3)
                amount_account_str = match.group(4)
                
                # Разбиваем дату и время операции
                date_time_parts = date_time_op.split()
                date_op = date_time_parts[0]
                time_op = date_time_parts[1] if len(date_time_parts) > 1 else "00:00"
                
                # Преобразуем суммы
                amount_currency = self._parse_amount(amount_currency_str)
                amount_account = self._parse_amount(amount_account_str)
                
                # Остаток строки после сумм содержит описание и номер карты
                remaining_text = line[match.end():].strip()
                
                # Используем регулярное выражение для поиска 4 цифр в конце строки (номер карты)
                card_match = re.search(r'\b(\d{4})\s*$', remaining_text)
                if card_match:
                    card_number = card_match.group(1)
                    description = remaining_text[:card_match.start()].strip()
                else:
                    description = remaining_text
                    card_number = ""
                
                # Создаем транзакцию
                transaction = {
                    "Дата_операции": datetime.strptime(date_op, "%d.%m.%Y"),
                    "Время_операции": time_op,
                    "Дата_списания": datetime.strptime(date_clearing, "%d.%m.%Y"),
                    "Сумма": amount_currency,
                    "Сумма_в_валюте_счета": amount_account,
                    "Описание": description,
                    "Идентификатор": card_number,
                    "Тип": "Доход" if amount_currency > 0 else "Расход"
                }
                
                # Определяем категорию транзакции
                category = self._classify_transaction(description)
                transaction["Категория"] = category
                
                self.logger.debug(f"Создана транзакция: {transaction}")
                transactions.append(transaction)
            else:
                self.logger.debug(f"Строка не соответствует шаблону транзакции: {line}")
            
            i += 1
        
        self.logger.info(f"Извлечено {len(transactions)} транзакций из текста выписки")
        return transactions
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        Парсит строку с суммой в число.
        
        Args:
            amount_str: Строка с суммой (например, "+20 000.00 ₽" или "-245.00 ₽").
            
        Returns:
            Число, представляющее сумму.
        """
        # Удаляем символ рубля и другие лишние символы
        cleaned_str = amount_str.replace('₽', '').replace(' ', '')
        
        # Заменяем запятую на точку, если нужно
        cleaned_str = cleaned_str.replace(',', '.')
        
        try:
            # Конвертируем в число
            amount = float(cleaned_str)
            return amount
        except ValueError:
            self.logger.error(f"Не удалось преобразовать строку '{amount_str}' в число")
            return 0.0
    
    def _classify_transaction(self, description: str) -> str:
        """
        Классифицирует транзакцию по категориям на основе описания.
        
        Args:
            description: Описание транзакции.
            
        Returns:
            Категория транзакции.
        """
        description_lower = description.lower()
        
        for category, keywords in self.TRANSACTION_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return category
        
        # Особые случаи классификации
        if "перевод" in description_lower:
            return "Переводы"
        elif "комиссия" in description_lower or "плата за" in description_lower:
            return "Комиссии и обслуживание"
        elif "снятие" in description_lower or "наличные" in description_lower or "банкомат" in description_lower:
            return "Снятие наличных"
        
        return "Другое"
    
    def analyze_spending_by_category(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Анализирует расходы по категориям.
        
        Args:
            transactions_df: DataFrame с транзакциями.
            
        Returns:
            DataFrame с суммами расходов по категориям.
        """
        # Проверяем, что DataFrame не пустой
        if transactions_df.empty:
            self.logger.warning("Пустой DataFrame с транзакциями, анализ расходов невозможен")
            return pd.DataFrame()
            
        # Копируем DataFrame для безопасности
        df = transactions_df.copy()
        
        # Фильтруем только расходы (отрицательные суммы)
        expenses_df = df[df["Сумма"] < 0].copy()
        
        # Преобразуем суммы в положительные значения для удобства анализа
        expenses_df["Сумма"] = expenses_df["Сумма"].abs()
        
        # Если есть расходы, группируем их по категориям
        if not expenses_df.empty:
            category_spending = expenses_df.groupby("Категория")["Сумма"].sum().reset_index()
            # Сортируем по убыванию суммы
            category_spending = category_spending.sort_values("Сумма", ascending=False)
            return category_spending
        else:
            self.logger.warning("Нет данных о расходах для анализа")
            return pd.DataFrame()
    
    def get_monthly_spending_trend(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Получает тренд расходов по месяцам.
        
        Args:
            transactions_df: DataFrame с транзакциями.
            
        Returns:
            DataFrame с трендом расходов по месяцам и категориям.
        """
        # Проверяем, что DataFrame не пустой
        if transactions_df.empty:
            self.logger.warning("Пустой DataFrame с транзакциями, анализ тренда невозможен")
            return pd.DataFrame()
            
        # Копируем DataFrame для безопасности
        df = transactions_df.copy()
        
        # Фильтруем только расходы (отрицательные суммы)
        expenses_df = df[df["Сумма"] < 0].copy()
        
        # Преобразуем суммы в положительные значения для удобства анализа
        expenses_df["Сумма"] = expenses_df["Сумма"].abs()
        
        # Если есть расходы, анализируем тренд по месяцам
        if not expenses_df.empty and "Дата_операции" in expenses_df.columns:
            # Создаем столбец с месяцем операции
            expenses_df["Месяц"] = pd.PeriodIndex(expenses_df["Дата_операции"], freq="M")
            expenses_df["Месяц_str"] = expenses_df["Месяц"].astype(str)
            
            # Группируем по месяцу и категориям
            monthly_trend = expenses_df.groupby(["Месяц", "Месяц_str", "Категория"])["Сумма"].sum().reset_index()
            
            # Сортируем по месяцу и сумме
            monthly_trend = monthly_trend.sort_values(["Месяц", "Сумма"], ascending=[True, False])
            
            return monthly_trend
        else:
            self.logger.warning("Нет данных о расходах или даты операций для анализа тренда")
            return pd.DataFrame()
            
    def predict_future_spending(self, transactions_df: pd.DataFrame, prediction_period: int = 1) -> dict:
        """
        Прогнозирует будущие расходы на основе исторических данных.
        
        Args:
            transactions_df: DataFrame с транзакциями.
            prediction_period: Количество периодов для прогноза (1 = следующий месяц).
            
        Returns:
            Словарь с прогнозом расходов по категориям.
        """
        # Проверяем, что DataFrame не пустой
        if transactions_df.empty:
            self.logger.warning("Пустой DataFrame с транзакциями, прогноз невозможен")
            return {}
            
        # Получаем расходы по категориям
        category_spending = self.analyze_spending_by_category(transactions_df)
        
        if category_spending.empty:
            self.logger.warning("Нет данных о расходах для прогноза")
            return {}
        
        # Получаем количество месяцев в данных
        if "Дата_операции" in transactions_df.columns and not transactions_df.empty:
            min_date = transactions_df["Дата_операции"].min()
            max_date = transactions_df["Дата_операции"].max()
            
            # Вычисляем количество месяцев
            months_diff = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
            if months_diff <= 0:
                months_diff = 1  # Минимум 1 месяц
        else:
            months_diff = 1  # По умолчанию, если нет данных о датах
        
        # Создаем прогноз на основе средних расходов в месяц
        predictions = {}
        for _, row in category_spending.iterrows():
            category = row["Категория"]
            total_spending = row["Сумма"]
            
            # Среднемесячные расходы по категории
            monthly_avg = total_spending / months_diff
            
            # Прогноз на следующий период
            prediction = monthly_avg * prediction_period
            
            predictions[category] = prediction
        
        return predictions
    
    def visualize_spending_by_category(self, category_spending: pd.DataFrame, 
                                      output_file: Optional[str] = None) -> None:
        """
        Визуализирует расходы по категориям.
        
        Args:
            category_spending: DataFrame с суммами расходов по категориям.
            output_file: Путь для сохранения изображения. Если None, то график будет отображен.
        """
        plt.figure(figsize=(12, 8))
        
        # Создаем круговую диаграмму
        plt.pie(
            category_spending["Сумма"],
            labels=category_spending["Категория"],
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
        )
        plt.axis('equal')  # Равные пропорции обеспечивают круговую диаграмму
        plt.title('Распределение расходов по категориям', fontsize=16)
        
        if output_file:
            plt.savefig(output_file, bbox_inches='tight')
            self.logger.info(f"График сохранен в {output_file}")
        else:
            plt.show()
    
    def visualize_monthly_trend(self, monthly_spending: pd.DataFrame, 
                               output_file: Optional[str] = None) -> None:
        """
        Визуализирует тренд расходов по месяцам.
        
        Args:
            monthly_spending: DataFrame с ежемесячными расходами.
            output_file: Путь для сохранения изображения. Если None, то график будет отображен.
        """
        # Создаем сводную таблицу для визуализации
        pivot_df = monthly_spending.pivot_table(
            index="Месяц_str",
            columns="Категория",
            values="Сумма",
            aggfunc="sum"
        ).fillna(0)
        
        plt.figure(figsize=(14, 8))
        pivot_df.plot(kind="bar", stacked=True, figsize=(14, 8))
        plt.title('Динамика расходов по категориям', fontsize=16)
        plt.xlabel('Месяц', fontsize=12)
        plt.ylabel('Сумма расходов (руб.)', fontsize=12)
        plt.legend(title='Категория', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, bbox_inches='tight')
            self.logger.info(f"График сохранен в {output_file}")
        else:
            plt.show()

    def generate_spending_report(self, transactions_df: pd.DataFrame, output_dir: str = None, report_type: str = "default") -> dict:
        """
        Генерирует полный отчет о расходах с визуализацией.
        
        Args:
            transactions_df: DataFrame с транзакциями.
            output_dir: Директория для сохранения отчета.
            report_type: Тип отчета ('default', 'monthly', 'category').
            
        Returns:
            Словарь с данными отчета.
        """
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Фильтруем только расходы
        expenses_df = transactions_df[transactions_df['Сумма'] < 0].copy()
        expenses_df['Сумма'] = expenses_df['Сумма'].abs()
        
        # Анализ расходов по категориям
        category_spending = self.analyze_spending_by_category(transactions_df)
        
        # Анализ тренда расходов по месяцам
        monthly_trend = self.get_monthly_spending_trend(transactions_df)
        
        # Прогноз будущих расходов
        future_spending = self.predict_future_spending(transactions_df)
        
        # Получаем общую сумму расходов
        total_expenses = expenses_df['Сумма'].sum()
        
        # Создаем визуализации
        visualization_files = {}
        
        if output_dir:
            # График расходов по категориям
            plt.figure(figsize=(10, 6))
            try:
                top_categories = category_spending.head(10)
                plt.pie(top_categories['Сумма'], 
                       labels=top_categories['Категория'], 
                       autopct='%1.1f%%',
                       startangle=90)
                plt.axis('equal')
                plt.title('Расходы по категориям')
                
                chart_path = os.path.join(output_dir, 'category_spending.png')
                plt.savefig(chart_path)
                plt.close()
                
                visualization_files['category_chart'] = chart_path
                self.logger.info(f"График сохранен в {chart_path}")
            except Exception as e:
                self.logger.error(f"Ошибка при создании графика расходов по категориям: {e}")
            
            # График тренда расходов по месяцам
            if not monthly_trend.empty:
                plt.figure(figsize=(12, 6))
                try:
                    # Пивотная таблица для месяцев и категорий
                    pivot_table = pd.pivot_table(
                        monthly_trend,
                        values='Сумма',
                        index='Месяц_str',
                        columns='Категория',
                        aggfunc=np.sum
                    ).fillna(0)
                    
                    # Строим столбчатую диаграмму
                    pivot_table.plot(kind='bar', stacked=True)
                    plt.title('Тренд расходов по месяцам')
                    plt.xlabel('Месяц')
                    plt.ylabel('Сумма (руб.)')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    chart_path = os.path.join(output_dir, 'monthly_trend.png')
                    plt.savefig(chart_path)
                    plt.close()
                    
                    visualization_files['trend_chart'] = chart_path
                    self.logger.info(f"График сохранен в {chart_path}")
                except Exception as e:
                    self.logger.error(f"Ошибка при создании графика тренда расходов: {e}")
        
        # Получаем метаданные из первой строки DataFrame, если они есть
        metadata = {}
        metadata_fields = ["Номер_договора", "Номер_счета", "Дата_договора", "Период_с", "Период_по", "ФИО"]
        for field in metadata_fields:
            if field in transactions_df.columns and not transactions_df.empty:
                metadata[field] = transactions_df[field].iloc[0]
        
        # Создаем отчет
        report = {
            "total_expenses": float(total_expenses),
            "category_spending": category_spending.to_dict('records'),
            "monthly_trend": monthly_trend.to_dict('records') if not monthly_trend.empty else [],
            "future_spending": future_spending,
            "visualization_files": visualization_files,
            "metadata": metadata
        }
        
        # Сохраняем отчет в JSON
        if output_dir:
            report_path = os.path.join(output_dir, 'spending_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                # Преобразуем даты в строки для сериализации JSON
                json_report = copy.deepcopy(report)
                
                # Преобразуем данные категорий расходов
                for item in json_report.get('category_spending', []):
                    if isinstance(item.get('Дата_операции'), (datetime, pd.Timestamp)):
                        item['Дата_операции'] = item['Дата_операции'].strftime('%Y-%m-%d')
                
                # Преобразуем данные тренда расходов
                for item in json_report.get('monthly_trend', []):
                    if isinstance(item.get('Месяц'), pd.Period):
                        item['Месяц'] = str(item['Месяц'])
                
                json.dump(json_report, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Отчет о расходах сохранен в {report_path}")
        
        return report


def main():
    """
    Пример использования парсера банковских выписок.
    """
    parser = BankStatementParser()
    
    # Примеры путей к файлам выписок
    statements_directory = "static/bank_statements"
    output_directory = "reports/bank_analytics"
    
    os.makedirs(statements_directory, exist_ok=True)
    
    print(f"Для тестирования функциональности положите PDF-файлы выписок в директорию {statements_directory}")
    print("Затем раскомментируйте и доработайте код ниже для обработки ваших файлов.")
    
    """
    # Код для обработки реальных выписок:
    for file in os.listdir(statements_directory):
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(statements_directory, file)
            print(f"Обрабатываем файл: {file}")
            
            # Парсим выписку
            transactions_df = parser.parse_pdf_statement(file_path)
            
            if not transactions_df.empty:
                # Генерируем отчет о расходах
                report = parser.generate_spending_report(
                    transactions_df, 
                    output_dir=os.path.join(output_directory, file.split(".")[0])
                )
                
                print(f"Общая сумма расходов: {report['total_expenses']:.2f} руб.")
                print(f"Отчет сохранен в директории: {output_directory}/{file.split('.')[0]}")
    """


if __name__ == "__main__":
    main() 