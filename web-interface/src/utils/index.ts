import { ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Объединяет классы Tailwind CSS с помощью clsx и tailwind-merge
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Форматирует дату в локализованный формат
 * @param date строка или объект даты
 * @param options параметры форматирования
 * @returns отформатированная дата
 */
export function formatDate(
  date: string | Date,
  options: Intl.DateTimeFormatOptions = {
    day: "numeric",
    month: "long",
    year: "numeric",
  }
): string {
  const dateObject = typeof date === "string" ? new Date(date) : date
  return new Intl.DateTimeFormat("ru-RU", options).format(dateObject)
}

/**
 * Форматирует число как денежную сумму
 */
export function formatCurrency(amount: number, currency = 'RUB'): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Классифицирует сумму как доход или расход и возвращает соответствующий стиль
 */
export function getAmountColorClass(amount: number): string {
  return amount < 0 ? "expense-text" : "income-text"
}

/**
 * Генерирует уникальный идентификатор
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

/**
 * Группирует массив объектов по указанному ключу
 */
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((result, item) => {
    const groupKey = String(item[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * Возвращает сокращенное название месяца на русском
 */
export function getShortMonthName(monthStr: string): string {
  const date = new Date(monthStr)
  return new Intl.DateTimeFormat("ru-RU", { month: "short" }).format(date)
}

/**
 * Форматирует размер файла в человекочитаемый формат
 */
export function formatFileSize(bytes: number): string {
  const units = ["Б", "КБ", "МБ", "ГБ"]
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

/**
 * Задержка выполнения на указанное количество миллисекунд
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Обрезает текст до указанной длины и добавляет многоточие
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Преобразует первую букву строки в заглавную
 */
export function capitalizeFirstLetter(string: string): string {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Проверяет, является ли строка валидным JSON
 */
export function isValidJson(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Возвращает случайный элемент из массива
 */
export function getRandomItem<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Перемешивает массив
 */
export function shuffleArray<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
} 