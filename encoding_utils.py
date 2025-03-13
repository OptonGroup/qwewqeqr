"""
Модуль с утилитами для работы с кодировкой в Python
Автор: AI Assistant
Дата: 26.04.2025
Описание: Этот модуль содержит функции для корректной работы с кодировкой в Windows
"""

import os
import sys
import locale
import platform
import codecs
import logging
from pathlib import Path
from typing import Optional, Union, TextIO, BinaryIO, Dict, Any, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("encoding_utils")

def get_system_info() -> Dict[str, str]:
    """
    Получение информации о системе и кодировках
    
    Returns:
        Dict[str, str]: Словарь с информацией о системе и кодировках
    """
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
        "default_encoding": sys.getdefaultencoding(),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "locale": locale.getpreferredencoding(),
        "stdout_encoding": sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else "unknown",
        "stderr_encoding": sys.stderr.encoding if hasattr(sys.stderr, 'encoding') else "unknown",
        "powershell": "Yes" if is_powershell() else "No",
        "terminal_type": get_terminal_type(),
    }

def get_terminal_type() -> str:
    """
    Определение типа терминала
    
    Returns:
        str: Тип терминала (cmd, powershell, other)
    """
    if is_powershell():
        return "powershell"
    elif "PROMPT" in os.environ:
        return "cmd"
    return "other"

def detect_file_encoding(file_path: Union[str, Path], read_size: int = 4096) -> str:
    """
    Определение кодировки файла
    
    Args:
        file_path (Union[str, Path]): Путь к файлу
        read_size (int, optional): Размер читаемого блока. По умолчанию 4096.
    
    Returns:
        str: Определенная кодировка файла
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Файл {file_path} не существует.")
        return 'utf-8'
    
    # Проверяем BOM
    with open(file_path, 'rb') as f:
        raw = f.read(4)
        if raw.startswith(codecs.BOM_UTF8):
            return 'utf-8-sig'
        elif raw.startswith(codecs.BOM_UTF16_LE):
            return 'utf-16-le'
        elif raw.startswith(codecs.BOM_UTF16_BE):
            return 'utf-16-be'
    
    # Пробуем разные кодировки
    encodings = ['utf-8', 'cp1251', 'ascii']
    
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(read_size)
            return enc
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'

def convert_file_encoding(
    file_path: Union[str, Path],
    target_encoding: str = 'utf-8',
    source_encoding: Optional[str] = None,
    add_bom: bool = False
) -> bool:
    """
    Конвертация файла в указанную кодировку
    
    Args:
        file_path (Union[str, Path]): Путь к файлу
        target_encoding (str, optional): Целевая кодировка. По умолчанию 'utf-8'.
        source_encoding (Optional[str], optional): Исходная кодировка. Если None, определяется автоматически.
        add_bom (bool, optional): Добавить BOM для UTF-8. По умолчанию False.
    
    Returns:
        bool: True если конвертация успешна, иначе False
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Файл {file_path} не существует.")
        return False
    
    # Определяем исходную кодировку, если не указана
    if source_encoding is None:
        source_encoding = detect_file_encoding(file_path)
    
    try:
        # Читаем содержимое в исходной кодировке
        with open(file_path, 'r', encoding=source_encoding) as f:
            content = f.read()
        
        # Записываем в новой кодировке
        encoding_to_use = f"{target_encoding}-sig" if add_bom else target_encoding
        with open(file_path, 'w', encoding=encoding_to_use) as f:
            f.write(content)
        
        logger.info(f"Файл {file_path} успешно конвертирован из {source_encoding} в {target_encoding}"
                   f"{' с BOM' if add_bom else ''}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при конвертации файла {file_path}: {e}")
        return False

def setup_console_encoding() -> None:
    """
    Настройка кодировки консоли для корректного отображения кириллицы
    """
    if is_windows():
        try:
            # Пытаемся установить кодировку для консоли Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # 65001 - код для UTF-8
            kernel32.SetConsoleCP(65001)
            
            # Дополнительная настройка для PowerShell
            if is_powershell():
                os.system("chcp 65001 > nul")
            
            logger.info("Установлена кодировка консоли Windows: UTF-8 (65001)")
        except Exception as e:
            logger.warning(f"Не удалось установить кодировку консоли Windows: {e}")
    
    # Устанавливаем кодировку для stdout и stderr
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        # Для старых версий Python
        if hasattr(sys.stdout, 'encoding'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        if hasattr(sys.stderr, 'encoding'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    
    logger.info(f"Установлена кодировка для stdout: {sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'unknown'}")
    logger.info(f"Установлена кодировка для stderr: {sys.stderr.encoding if hasattr(sys.stderr, 'encoding') else 'unknown'}")

def print_system_info() -> None:
    """
    Вывод информации о системе и кодировках
    """
    info = get_system_info()
    logger.info("Системная информация:")
    for key, value in info.items():
        logger.info(f"  {key}: {value}")

def is_windows() -> bool:
    """
    Проверка, является ли текущая ОС Windows
    
    Returns:
        bool: True, если ОС - Windows, иначе False
    """
    return platform.system().lower() == "windows"

def is_powershell() -> bool:
    """
    Проверка, запущен ли скрипт из PowerShell
    
    Returns:
        bool: True, если скрипт запущен из PowerShell, иначе False
    """
    # Проверка переменных окружения, характерных для PowerShell
    return os.environ.get('PSModulePath') is not None

def safe_open(
    file_path: Union[str, Path], 
    mode: str = 'r', 
    encoding: str = 'utf-8',
    errors: str = 'replace',
    fallback_encoding: str = 'cp1251'
) -> Union[TextIO, BinaryIO]:
    """
    Безопасное открытие файла с обработкой ошибок кодировки
    
    Args:
        file_path (Union[str, Path]): Путь к файлу
        mode (str, optional): Режим открытия файла. По умолчанию 'r'.
        encoding (str, optional): Кодировка файла. По умолчанию 'utf-8'.
        errors (str, optional): Обработка ошибок кодировки. По умолчанию 'replace'.
        fallback_encoding (str, optional): Запасная кодировка. По умолчанию 'cp1251'.
    
    Returns:
        Union[TextIO, BinaryIO]: Открытый файловый объект
    
    Raises:
        IOError: Если файл не удалось открыть
    """
    file_path = Path(file_path)
    
    # Для бинарных режимов игнорируем кодировку
    if 'b' in mode:
        return open(file_path, mode)
    
    try:
        return open(file_path, mode, encoding=encoding, errors=errors)
    except UnicodeDecodeError:
        logger.warning(f"Не удалось открыть файл {file_path} с кодировкой {encoding}. "
                      f"Пробуем использовать {fallback_encoding}.")
        try:
            return open(file_path, mode, encoding=fallback_encoding, errors=errors)
        except UnicodeDecodeError:
            logger.error(f"Не удалось открыть файл {file_path} с кодировкой {fallback_encoding}.")
            raise

def safe_write(
    file_path: Union[str, Path], 
    content: str,
    mode: str = 'w', 
    encoding: str = 'utf-8',
    errors: str = 'replace',
    fallback_encoding: str = 'cp1251'
) -> bool:
    """
    Безопасная запись в файл с обработкой ошибок кодировки
    
    Args:
        file_path (Union[str, Path]): Путь к файлу
        content (str): Содержимое для записи
        mode (str, optional): Режим открытия файла. По умолчанию 'w'.
        encoding (str, optional): Кодировка файла. По умолчанию 'utf-8'.
        errors (str, optional): Обработка ошибок кодировки. По умолчанию 'replace'.
        fallback_encoding (str, optional): Запасная кодировка. По умолчанию 'cp1251'.
    
    Returns:
        bool: True, если запись успешна, иначе False
    """
    file_path = Path(file_path)
    
    # Создаем родительские директории, если они не существуют
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, mode, encoding=encoding, errors=errors) as f:
            f.write(content)
        return True
    except UnicodeEncodeError:
        logger.warning(f"Не удалось записать в файл {file_path} с кодировкой {encoding}. "
                      f"Пробуем использовать {fallback_encoding}.")
        try:
            with open(file_path, mode, encoding=fallback_encoding, errors=errors) as f:
                f.write(content)
            return True
        except UnicodeEncodeError:
            logger.error(f"Не удалось записать в файл {file_path} с кодировкой {fallback_encoding}.")
            return False

def safe_read(
    file_path: Union[str, Path], 
    encoding: str = 'utf-8',
    errors: str = 'replace',
    fallback_encoding: str = 'cp1251'
) -> Tuple[bool, str]:
    """
    Безопасное чтение из файла с обработкой ошибок кодировки
    
    Args:
        file_path (Union[str, Path]): Путь к файлу
        encoding (str, optional): Кодировка файла. По умолчанию 'utf-8'.
        errors (str, optional): Обработка ошибок кодировки. По умолчанию 'replace'.
        fallback_encoding (str, optional): Запасная кодировка. По умолчанию 'cp1251'.
    
    Returns:
        Tuple[bool, str]: (успех, содержимое)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Файл {file_path} не существует.")
        return False, ""
    
    try:
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            content = f.read()
        return True, content
    except UnicodeDecodeError:
        logger.warning(f"Не удалось прочитать файл {file_path} с кодировкой {encoding}. "
                      f"Пробуем использовать {fallback_encoding}.")
        try:
            with open(file_path, 'r', encoding=fallback_encoding, errors=errors) as f:
                content = f.read()
            return True, content
        except UnicodeDecodeError:
            logger.error(f"Не удалось прочитать файл {file_path} с кодировкой {fallback_encoding}.")
            return False, ""

def setup_file_logger(
    log_file: Union[str, Path],
    level: int = logging.INFO,
    encoding: str = 'utf-8'
) -> logging.Logger:
    """
    Настройка логирования в файл с указанной кодировкой
    
    Args:
        log_file (Union[str, Path]): Путь к файлу логов
        level (int, optional): Уровень логирования. По умолчанию logging.INFO.
        encoding (str, optional): Кодировка файла логов. По умолчанию 'utf-8'.
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    log_file = Path(log_file)
    
    # Создаем родительские директории, если они не существуют
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Создаем логгер
    logger = logging.getLogger("file_logger")
    logger.setLevel(level)
    
    # Создаем обработчик для записи в файл
    file_handler = logging.FileHandler(log_file, encoding=encoding)
    file_handler.setLevel(level)
    
    # Создаем форматтер
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Добавляем обработчик к логгеру
    logger.addHandler(file_handler)
    
    return logger

if __name__ == "__main__":
    # Пример использования
    setup_console_encoding()
    print_system_info()
    
    # Пример записи в файл
    test_content = "Тестовая строка с кириллицей: абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    success = safe_write("test_output.txt", test_content)
    print(f"Запись в файл: {'успешно' if success else 'ошибка'}")
    
    # Пример чтения из файла
    success, content = safe_read("test_output.txt")
    print(f"Чтение из файла: {'успешно' if success else 'ошибка'}")
    print(f"Содержимое: {content}")
    
    # Пример настройки логирования в файл
    file_logger = setup_file_logger("test_log.log")
    file_logger.info("Тестовое сообщение с кириллицей: абвгдеёжзийклмнопрстуфхцчшщъыьэюя") 