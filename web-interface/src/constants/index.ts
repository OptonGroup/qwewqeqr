import {
  ShoppingCart,
  Home,
  Car,
  Utensils,
  Film,
  Shirt,
  Heart,
  Scissors,
  Tv,
  CreditCard,
  Briefcase,
  Wallet,
  Gift,
  Coffee,
  Smartphone,
  BookOpen,
  Plane,
  DollarSign,
  HelpCircle
} from 'lucide-react';

// Цвета для категорий расходов
export const CATEGORY_COLORS: Record<string, string> = {
  'Продукты': '#4CAF50',
  'Жилье': '#2196F3',
  'Транспорт': '#FF9800',
  'Рестораны': '#F44336',
  'Развлечения': '#9C27B0',
  'Одежда': '#3F51B5',
  'Здоровье': '#00BCD4',
  'Красота': '#E91E63',
  'Подписки': '#607D8B',
  'Кредиты': '#795548',
  'Работа': '#8BC34A',
  'Переводы': '#FFEB3B',
  'Подарки': '#FF5722',
  'Кафе': '#9E9E9E',
  'Техника': '#673AB7',
  'Образование': '#03A9F4',
  'Путешествия': '#FFC107',
  'Инвестиции': '#CDDC39',
  'Другое': '#757575'
};

// Иконки для категорий расходов
export const CATEGORY_ICONS: Record<string, React.ComponentType> = {
  'Продукты': ShoppingCart,
  'Жилье': Home,
  'Транспорт': Car,
  'Рестораны': Utensils,
  'Развлечения': Film,
  'Одежда': Shirt,
  'Здоровье': Heart,
  'Красота': Scissors,
  'Подписки': Tv,
  'Кредиты': CreditCard,
  'Работа': Briefcase,
  'Переводы': Wallet,
  'Подарки': Gift,
  'Кафе': Coffee,
  'Техника': Smartphone,
  'Образование': BookOpen,
  'Путешествия': Plane,
  'Инвестиции': DollarSign,
  'Другое': HelpCircle
};

// Рекомендуемое распределение бюджета (в процентах)
export const RECOMMENDED_BUDGET_ALLOCATION: Record<string, number> = {
  'Жилье': 30,
  'Продукты': 15,
  'Транспорт': 10,
  'Здоровье': 10,
  'Развлечения': 5,
  'Одежда': 5,
  'Рестораны': 5,
  'Красота': 3,
  'Подписки': 2,
  'Сбережения': 10,
  'Другое': 5
};

// Пороговые значения для оценки расходов
export const SPENDING_THRESHOLDS = {
  WARNING: 90, // Если расходы достигают 90% от рекомендуемого бюджета
  DANGER: 110  // Если расходы превышают рекомендуемый бюджет на 10%
};

// Форматы дат
export const DATE_FORMATS = {
  DISPLAY: 'DD.MM.YYYY',
  API: 'YYYY-MM-DD'
}; 