#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для запуска тестовых файлов и сбора результатов.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Минимальная настройка логирования для скорости
    logging.basicConfig(
        level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)

def run_test(config: str, test_file: str, no_validation: bool = False, 
             debug: bool = False, output_file: str = None) -> int:
    """Запуск тестов с указанными параметрами."""
    try:
        # Формирование команды
        cmd = [sys.executable, test_file]
        if config:
            cmd.extend(['-c', config])
        if no_validation:
            cmd.append('--no-validation')
        if debug:
            cmd.append('--debug')
            
        # Настройка вывода
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                return subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True).returncode
        else:
            # Прямой вывод в консоль для скорости
            return subprocess.run(cmd, text=True).returncode
        
    except Exception as e:
        logging.error(f"Ошибка при запуске теста: {str(e)}")
        return 1

def main():
    """Основная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Запуск тестов')
    parser.add_argument('-c', '--config', default='formal', help='Конфигурация для запуска тестов')
    parser.add_argument('-t', '--test-file', required=True, help='Файл с тестами для запуска')
    parser.add_argument('--no-validation', action='store_true', help='Пропустить валидацию результатов')
    parser.add_argument('--debug', action='store_true', help='Включить режим отладки')
    parser.add_argument('-o', '--output-file', help='Файл для сохранения вывода')
    
    args = parser.parse_args()
    
    # Настройка окружения
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Запуск теста
    sys.exit(run_test(
        config=args.config,
        test_file=args.test_file,
        no_validation=args.no_validation,
        debug=args.debug,
        output_file=args.output_file
    ))

if __name__ == '__main__':
    main() 