/**
 * Форматирует дату в формат DD.MM.YYYY
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  
  return `${day}.${month}.${year}`;
}

/**
 * Возвращает название текущего месяца на русском языке
 */
export function getCurrentMonthName(): string {
  const months = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];
  
  const currentMonth = new Date().getMonth();
  return months[currentMonth];
}

/**
 * Возвращает название месяца на русском языке по его номеру (0-11)
 */
export function getMonthName(monthIndex: number): string {
  const months = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];
  
  return months[monthIndex % 12];
}

/**
 * Возвращает короткое название месяца на русском языке
 */
export function getShortMonthName(monthName: string): string {
  const monthMap: Record<string, string> = {
    'Январь': 'Янв',
    'Февраль': 'Фев',
    'Март': 'Мар',
    'Апрель': 'Апр',
    'Май': 'Май',
    'Июнь': 'Июн',
    'Июль': 'Июл',
    'Август': 'Авг',
    'Сентябрь': 'Сен',
    'Октябрь': 'Окт',
    'Ноябрь': 'Ноя',
    'Декабрь': 'Дек'
  };
  
  return monthMap[monthName] || monthName.substring(0, 3);
}

/**
 * Парсит дату из строки формата DD.MM.YYYY
 */
export function parseDate(dateString: string): Date {
  const [day, month, year] = dateString.split('.').map(Number);
  return new Date(year, month - 1, day);
}

/**
 * Возвращает первый и последний день месяца
 */
export function getMonthRange(year: number, month: number): { start: Date; end: Date } {
  const start = new Date(year, month, 1);
  const end = new Date(year, month + 1, 0);
  
  return { start, end };
}

/**
 * Форматирует дату в относительном формате (сегодня, вчера, и т.д.)
 */
export function formatRelativeDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  
  const isToday = d.getDate() === now.getDate() && 
                  d.getMonth() === now.getMonth() && 
                  d.getFullYear() === now.getFullYear();
  
  if (isToday) {
    return 'Сегодня';
  }
  
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  
  const isYesterday = d.getDate() === yesterday.getDate() && 
                      d.getMonth() === yesterday.getMonth() && 
                      d.getFullYear() === yesterday.getFullYear();
  
  if (isYesterday) {
    return 'Вчера';
  }
  
  return formatDate(d);
} 