export interface Transaction {
  Дата_операции: string;
  Время_операции: string;
  Дата_списания: string;
  Сумма: number;
  Сумма_в_валюте_счета: number;
  Описание: string;
  Идентификатор: string;
  Тип: 'Доход' | 'Расход';
  Категория: string;
}

export interface StatementMetadata {
  Номер_договора: string;
  Номер_счета: string;
  Дата_договора: string;
  Период_с: string;
  Период_по: string;
  ФИО: string;
}

export interface CategorySpending {
  Категория: string;
  Сумма: number;
}

export interface MonthlyTrend {
  Месяц: string;
  Месяц_str: string;
  Категория: string;
  Сумма: number;
}

export interface FutureSpending {
  [category: string]: number;
}

export interface SpendingReport {
  total_expenses: number;
  category_spending: CategorySpending[];
  monthly_trend: MonthlyTrend[];
  future_spending: FutureSpending;
  visualization_files: {
    [key: string]: string;
  };
  metadata: StatementMetadata;
}

export interface BankStatement {
  transactions: Transaction[];
  metadata: StatementMetadata;
  report?: SpendingReport;
}

export type TransactionTableRow = Transaction & {
  id: string;
};

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor?: string[];
    borderWidth?: number;
  }[];
}

export const CATEGORY_COLORS: Record<string, string> = {
  "Продукты": "hsl(var(--food))",
  "Рестораны": "hsl(30, 90%, 55%)",
  "Одежда": "hsl(var(--shopping))",
  "Транспорт": "hsl(var(--transport))",
  "Развлечения": "hsl(var(--entertainment))",
  "Красота": "hsl(320, 80%, 65%)",
  "Здоровье": "hsl(var(--health))",
  "Жилье": "hsl(var(--utilities))",
  "Связь": "hsl(210, 80%, 60%)",
  "Подписки": "hsl(260, 70%, 65%)",
  "Техника": "hsl(170, 70%, 45%)",
  "Образование": "hsl(45, 80%, 55%)",
  "Переводы": "hsl(180, 70%, 50%)",
  "Комиссии и обслуживание": "hsl(0, 0%, 60%)",
  "Снятие наличных": "hsl(0, 0%, 40%)",
  "Другое": "hsl(0, 0%, 70%)"
}; 