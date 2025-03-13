"""
Модуль для работы с Pinterest без авторизации.
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
import json
from pathlib import Path
import os
from pydantic import BaseModel, Field
from retry import retry
from bs4 import BeautifulSoup
import re
import hashlib
import urllib.parse
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pinterest.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class PinInfo(BaseModel):
    """Модель для хранения информации о пине."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: str
    link: Optional[str] = None
    source_url: Optional[str] = None
    board: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    saved_path: Optional[str] = None
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def dict(self, *args, **kwargs):
        """Переопределяем метод dict для корректной сериализации в JSON."""
        d = super().dict(*args, **kwargs)
        # Убеждаемся, что last_updated всегда строка
        if isinstance(d['last_updated'], datetime):
            d['last_updated'] = d['last_updated'].isoformat()
        return d

class PinterestAPI:
    """Класс для работы с Pinterest без авторизации."""
    
    SEARCH_URL = "https://www.pinterest.com/search/pins"
    
    def __init__(self, download_dir: str = "photo"):
        """
        Инициализация клиента Pinterest API.
        
        Args:
            download_dir: Директория для сохранения изображений
        """
        self._session: Optional[aiohttp.ClientSession] = None
        self._driver: Optional[webdriver.Chrome] = None
        self._download_dir = Path(download_dir)
        self._download_dir.mkdir(exist_ok=True)
        self._cache_dir = Path("pinterest_cache")
        self._cache_dir.mkdir(exist_ok=True)
        
        # Загружаем кеш
        self._load_cache()
        logger.info("Pinterest API клиент инициализирован")
    
    async def _init_selenium(self):
        """Инициализация Selenium WebDriver."""
        if self._driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--remote-debugging-port=9222")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-notifications")
                chrome_options.add_argument("--disable-popup-blocking")
                chrome_options.add_argument('--ignore-certificate-errors')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # Список возможных путей к Chrome
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
                    r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
                    r"C:\Program Files\Google\Chrome Dev\Application\chrome.exe",
                ]
                
                # Поиск Chrome в системе
                chrome_binary = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_binary = path
                        logger.info(f"Найден Chrome по пути: {path}")
                        break
                
                if not chrome_binary:
                    # Попытка найти Chrome через реестр Windows
                    try:
                        import winreg
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                            chrome_binary = winreg.QueryValue(key, None)
                            logger.info(f"Найден Chrome через реестр: {chrome_binary}")
                    except Exception as e:
                        logger.warning(f"Не удалось найти Chrome через реестр: {e}")
                
                if not chrome_binary:
                    # Попытка автоматической установки Chrome
                    try:
                        logger.info("Попытка автоматической установки Chrome...")
                        import subprocess
                        import tempfile
                        import urllib.request
                        
                        # URL для скачивания Chrome
                        chrome_url = "https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe"
                        
                        # Создаем временную директорию
                        with tempfile.TemporaryDirectory() as temp_dir:
                            installer_path = os.path.join(temp_dir, "chrome_installer.exe")
                            
                            # Скачиваем установщик
                            logger.info("Скачивание установщика Chrome...")
                            urllib.request.urlretrieve(chrome_url, installer_path)
                            
                            # Запускаем установку
                            logger.info("Запуск установки Chrome...")
                            subprocess.run([installer_path, "/silent", "/install"], 
                                        check=True, 
                                        capture_output=True)
                            
                            logger.info("Chrome успешно установлен")
                            
                            # Проверяем стандартный путь установки
                            chrome_binary = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                            if not os.path.exists(chrome_binary):
                                chrome_binary = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                            
                    except Exception as e:
                        logger.error(f"Ошибка при установке Chrome: {e}")
                        raise Exception("Не удалось установить Chrome. Пожалуйста, установите его вручную.")
                
                if chrome_binary and os.path.exists(chrome_binary):
                    chrome_options.binary_location = chrome_binary
                else:
                    logger.error("Chrome не найден и не может быть установлен")
                    raise Exception("Chrome не найден и не может быть установлен. Пожалуйста, установите Chrome вручную.")
                
                # Создаем сервис с увеличенным таймаутом
                service = Service(
                    ChromeDriverManager().install(),
                    service_args=['--verbose'],
                    log_path='chromedriver.log'
                )
                
                # Создаем драйвер с увеличенным таймаутом
                self._driver = webdriver.Chrome(
                    service=service,
                    options=chrome_options
                )
                
                # Устанавливаем таймауты
                self._driver.set_page_load_timeout(60)
                self._driver.implicitly_wait(20)
                
                logger.info("Selenium WebDriver успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Selenium: {e}")
                if self._driver:
                    self._driver.quit()
                    self._driver = None
                raise
    
    def _load_cache(self) -> None:
        """Загружает кеш из файла."""
        try:
            cache_file = self._cache_dir / "pins_cache.json"
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Загружен кеш с {len(self._cache)} пинами")
            else:
                self._cache = {}
                logger.info("Создан новый кеш")
        except Exception as e:
            logger.error(f"Ошибка при загрузке кеша: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Сохраняет кеш в файл."""
        try:
            cache_file = self._cache_dir / "pins_cache.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.info("Кеш сохранен")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кеша: {e}")
    
    def _get_file_hash(self, url: str) -> str:
        """
        Генерирует хеш для URL изображения.
        
        Args:
            url: URL изображения
            
        Returns:
            Хеш URL
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    async def _init_session(self):
        """Инициализация HTTP сессии."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            logger.info("HTTP сессия инициализирована")
    
    async def _download_image(self, url: str) -> Optional[str]:
        """
        Скачивает изображение по URL.
        
        Args:
            url: URL изображения
            
        Returns:
            Путь к сохраненному файлу или None в случае ошибки
        """
        try:
            # Генерируем имя файла из хеша URL
            file_hash = self._get_file_hash(url)
            file_path = self._download_dir / f"{file_hash}.jpg"
            
            # Проверяем, существует ли файл
            if file_path.exists():
                logger.info(f"Изображение уже существует: {file_path}")
                return str(file_path)
            
            await self._init_session()
            
            async with self._session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при скачивании изображения: {response.status}")
                    return None
                
                data = await response.read()
                
                # Сохраняем изображение
                with open(file_path, "wb") as f:
                    f.write(data)
                
                logger.info(f"Изображение сохранено: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании изображения: {e}")
            return None

    def _get_best_image_url(self, img_element) -> Optional[str]:
        """
        Получает URL изображения наилучшего качества.
        
        Args:
            img_element: Элемент изображения
            
        Returns:
            URL изображения наилучшего качества или None
        """
        try:
            # Пробуем получить оригинальное изображение через data-src-original
            image_url = img_element.get_attribute('data-src-original')
            if image_url and image_url.startswith('http'):
                return image_url
            
            # Пробуем получить большое изображение через data-big-pin
            image_url = img_element.get_attribute('data-big-pin')
            if image_url and image_url.startswith('http'):
                return image_url
                
            # Пробуем получить изображение через srcset
            srcset = img_element.get_attribute('srcset')
            if srcset:
                # Парсим srcset и находим URL с максимальным размером
                urls_with_sizes = []
                for part in srcset.split(','):
                    part = part.strip()
                    if not part:
                        continue
                    
                    # Разбиваем на URL и размер
                    parts = part.split(' ')
                    if len(parts) >= 2:
                        url = parts[0]
                        # Извлекаем числовое значение размера
                        size = ''.join(filter(str.isdigit, parts[1]))
                        if size:
                            urls_with_sizes.append((url, int(size)))
                
                # Сортируем по размеру и берем самый большой
                if urls_with_sizes:
                    urls_with_sizes.sort(key=lambda x: x[1], reverse=True)
                    return urls_with_sizes[0][0]
            
            # Пробуем получить через src
            image_url = img_element.get_attribute('src')
            if image_url and image_url.startswith('http'):
                # Пробуем улучшить качество изображения, заменяя параметры размера
                image_url = re.sub(r'/\d+x/|/\d+x\d+/', '/originals/', image_url)
                return image_url
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении URL изображения: {e}")
            return None
        
    @retry(tries=5, delay=2, backoff=2)
    async def search_pins(
        self,
        query: str,
        limit: int = 10,
        download: bool = True
    ) -> List[PinInfo]:
        """
        Поиск пинов по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            download: Скачивать ли изображения
            
        Returns:
            Список найденных пинов
        """
        try:
            # Инициализируем сессию для скачивания
            if download:
                await self._init_session()
            
            # Инициализируем Selenium
            await self._init_selenium()
            
            # Формируем URL для поиска с правильным кодированием
            encoded_query = urllib.parse.quote(query)
            search_url = f"{self.SEARCH_URL}/?q={encoded_query}"
            
            logger.info(f"Загружаем страницу поиска: {search_url}")
            
            # Добавляем обработку ошибок при загрузке страницы
            try:
                self._driver.get(search_url)
            except Exception as e:
                logger.error(f"Ошибка при загрузке страницы: {e}")
                # Пробуем еще раз с дополнительным ожиданием
                time.sleep(5)
                self._driver.get(search_url)
            
            # Ждем загрузки любого из возможных селекторов
            selectors = [
                "div[data-test-id='search-pins-feed']",
                "div[data-test-id='pin']",
                "div[data-grid-item='true']",
                "div.Grid__Item"
            ]
            
            for selector in selectors:
                try:
                    WebDriverWait(self._driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Найден селектор: {selector}")
                    break
                except Exception:
                    continue
            
            logger.info("Страница загружена, прокручиваем для загрузки изображений")
            
            # Прокручиваем страницу для загрузки большего количества изображений
            last_height = self._driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = 5  # Ограничиваем количество прокруток
            
            while scrolls < max_scrolls:
                # Прокручиваем страницу
                self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Ждем загрузки контента
                
                # Проверяем высоту страницы
                new_height = self._driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scrolls += 1
            
            logger.info("Ищем изображения на странице")
            
            # Ищем все изображения на странице
            pins = []
            
            # Пробуем разные селекторы для поиска пинов
            pin_selectors = [
                "div[data-test-id='pin']",
                "div[data-grid-item='true']",
                "div.Grid__Item",
                "div[role='listitem']"
            ]
            
            pin_elements = []
            for selector in pin_selectors:
                try:
                    elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        pin_elements = elements
                        logger.info(f"Найдены пины через селектор: {selector}")
                        break
                except Exception:
                    continue
            
            if not pin_elements:
                # Если не нашли через селекторы, пробуем найти все изображения
                pin_elements = self._driver.find_elements(By.TAG_NAME, "img")
                logger.info("Используем поиск по тегу img")
            
            logger.info(f"Найдено {len(pin_elements)} потенциальных пинов")
            
            for pin_element in pin_elements[:limit]:
                try:
                    # Ищем изображение
                    img = None
                    if pin_element.tag_name == "img":
                        img = pin_element
                    else:
                        try:
                            img = pin_element.find_element(By.TAG_NAME, "img")
                        except Exception:
                            continue
                    
                    # Получаем URL изображения наилучшего качества
                    image_url = self._get_best_image_url(img)
                    
                    if not image_url:
                        continue
                    
                    # Фильтруем ненужные изображения
                    if any(x in image_url.lower() for x in ['logo', 'favicon', '/75/', 'webapp', 'spinner', 'loading']):
                        continue
                    
                    # Получаем описание
                    description = img.get_attribute('alt') or img.get_attribute('title')
                    
                    # Получаем ссылку на пин
                    pin_link = None
                    try:
                        if pin_element.tag_name == "a":
                            pin_link = pin_element.get_attribute('href')
                        else:
                            link_element = pin_element.find_element(By.TAG_NAME, "a")
                            pin_link = link_element.get_attribute('href')
                    except Exception:
                        pass
                    
                    # Создаем уникальный ID для пина
                    pin_id = self._get_file_hash(image_url)
                    
                    # Проверяем кеш
                    if pin_id in self._cache:
                        pins.append(PinInfo(**self._cache[pin_id]))
                        continue
                    
                    # Создаем объект пина
                    pin = PinInfo(
                        id=pin_id,
                        title=description,
                        description=description,
                        image_url=image_url,
                        link=pin_link,
                        source_url=None,
                        board=None,
                        tags=[],
                        last_updated=datetime.now().isoformat()
                    )
                    
                    # Скачиваем изображение, если требуется
                    if download and pin.image_url:
                        pin.saved_path = await self._download_image(pin.image_url)
                    
                    # Сохраняем в кеш только если удалось скачать изображение
                    if not download or pin.saved_path:
                        self._cache[pin_id] = pin.dict()
                        pins.append(pin)
                        logger.info(f"Добавлен пин: {pin.image_url}")
                    
                    # Проверяем лимит
                    if len(pins) >= limit:
                        break
                
                except Exception as e:
                    logger.error(f"Ошибка при обработке изображения: {e}")
                    continue
            
            if pins:
                try:
                    self._save_cache()
                except Exception as e:
                    logger.error(f"Ошибка при сохранении кеша: {e}")
                
                logger.info(f"Найдено {len(pins)} пинов по запросу '{query}'")
            else:
                logger.warning(f"Не найдены изображения для запроса '{query}'")
            
            return pins[:limit]

        except Exception as e:
            logger.error(f"Ошибка при поиске пинов: {e}")
            return []
        finally:
            if self._driver:
                self._driver.quit()
                self._driver = None
    
    async def close(self) -> None:
        """Закрывает все открытые соединения."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._driver:
            self._driver.quit()
            self._driver = None
        logger.info("Все соединения закрыты")

class Pinterest:
    """Обертка для обратной совместимости."""
    
    def __init__(self, number_of_photo: int = 10, photo_dir: str = "photo"):
        """
        Инициализация Pinterest клиента.
        
        Args:
            number_of_photo: Максимальное количество фотографий для загрузки
            photo_dir: Директория для сохранения фотографий
        """
        self.api = PinterestAPI(download_dir=photo_dir)
        self.number_of_photo = number_of_photo
        self.photo_dir = photo_dir
        
        # Создаем директорию, если её нет
        os.makedirs(photo_dir, exist_ok=True)
    
    async def search_pins(self, query: str, limit: Optional[int] = None, download: bool = True) -> List[PinInfo]:
        """
        Поиск пинов по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов (если не указано, используется number_of_photo)
            download: Скачивать ли изображения
            
        Returns:
            Список найденных пинов
        """
        if limit is None:
            limit = self.number_of_photo
            
        return await self.api.search_pins(query=query, limit=limit, download=download)
    
    async def close(self):
        """Закрывает соединения."""
        await self.api.close()
