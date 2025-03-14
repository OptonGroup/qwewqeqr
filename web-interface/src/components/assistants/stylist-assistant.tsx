"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, ShoppingBag, Plus, Pencil, ChevronDown, ChevronUp, Home } from 'lucide-react';
import { ProductCard } from './product-card';
import type { GarmentItem } from './product-card';
import PinterestOutfitSection from './pinterest-outfit-section';
import { Badge } from '@/components/ui/badge';
import { useAppContext } from '@/context/app-context';

// Базовые заглушки изображений в формате base64 для различных категорий
const BASE64_IMAGES = {
  // Серый прямоугольник с надписью "Изображение недоступно"
  default: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIyNHB4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiBmaWxsPSIjNmI3MjgwIj7QmNC30L7QsdGA0LDQttC10L3QuNC1INC90LXQtNC+0YHRgtGD0L/QvdC+PC90ZXh0Pjwvc3ZnPg==',
  // Силуэт футболки
  tshirt: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTEzMCAyMDAgTDIwMCAxMDAgTDI3MCAyMDAgTDMwMCAyMDAgTDMwMCA0MDAgTDEwMCA0MDAgTDEwMCAyMDAgWiIgZmlsbD0iIzk0YTNiOCIgc3Ryb2tlPSIjNjQ3NDhiIiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjQ1JSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCk0YPRgtCx0L7Qu9C60LA8L3RleHQ+PC9zdmc+',
  // Силуэт джинсов
  jeans: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTE1MCAxMDAgTDI1MCAxMDAgTDI3MCA0NTAgTDIyMCA1MDAgTDIwMCA0NTAgTDE4MCA1MDAgTDEzMCA0NTAgWiIgZmlsbD0iIzMwNjdBMCIgc3Ryb2tlPSIjMjg1MDdkIiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjI1JSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCU0LbQuNC90YHRizwvdGV4dD48L3N2Zz4=',
  // Силуэт куртки
  jacket: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTEyMCAxNTAgTDIwMCAxMDAgTDI4MCAxNTAgTDMwMCAyMDAgTDMwMCA0MDAgTDIzMCA0MDAgTDIzMCAzMDAgTDE3MCAzMDAgTDE3MCA0MDAgTDEwMCA0MDAgTDEwMCAyMDAgWiIgZmlsbD0iIzU3NTM0ZSIgc3Ryb2tlPSIjNDQzYzI4IiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjM1JSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCa0YPRgNGC0LrQsDwvdGV4dD48L3N2Zz4=',
  // Силуэт платья
  dress: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTE1MCAxNTAgTDI1MCAxNTAgTDI3MCAyMDAgTDIzMCA1MDAgTDE3MCA1MDAgTDEzMCAyMDAgWiIgZmlsbD0iI2U2MzBhMSIgc3Ryb2tlPSIjYmMyMDgyIiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjMwJSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCf0LvQsNGC0YzQtTwvdGV4dD48L3N2Zz4=',
  // Силуэт свитера
  sweater: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTEyMCAxNTAgTDIwMCAxMDAgTDI4MCAxNTAgTDMwMCAyMDAgTDMwMCA0MDAgTDEwMCA0MDAgTDEwMCAyMDAgWiIgZmlsbD0iIzY0NzQ4YiIgc3Ryb2tlPSIjNDc1NTY5IiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjM1JSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCh0LLQuNGC0LXRgDwvdGV4dD48L3N2Zz4=',
  // Силуэт обуви
  shoes: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTEwMCAzMDAgTDIwMCAyNTAgTDMwMCAzMDAgTDMwMCAzNTAgTDEwMCAzNTAgWiIgZmlsbD0iIzAzMTgyYyIgc3Ryb2tlPSIjMDAwMDAwIiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCe0LHRg9Cy0Yw8L3RleHQ+PC9zdmc+',
  // Общая одежда
  fashion: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTEzMCAyMDAgTDIwMCAxMDAgTDI3MCAyMDAgTDMwMCAyMDAgTDMwMCA0MDAgTDEwMCA0MDAgTDEwMCAyMDAgWiIgZmlsbD0iIzk0YTNiOCIgc3Ryb2tlPSIjNjQ3NDhiIiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjQ1JSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiM0NzU1NjkiPtCe0LTQtdC20LTQsDwvdGV4dD48L3N2Zz4=',
  // Улучшенная заглушка для пиджаков
  blazer: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTEyMCAxNTAgTDIwMCAxMDAgTDI4MCAxNTAgTDMwMCAyMDAgTDMwMCA0NTAgTDIzMCA0NTAgTDIwMCAzMDAgTDE3MCA0NTAgTDEwMCA0NTAgTDEwMCAyMDAgWiIgZmlsbD0iIzMzMzMzMyIgc3Ryb2tlPSIjMjIyMjIyIiBzdHJva2Utd2lkdGg9IjMiLz48cGF0aCBkPSJNMTcwIDIwMCBMMjMwIDIwMCBMMjMwIDI1MCBMMTcwIDI1MCBaIiBmaWxsPSIjZmZmZmZmIiBzdHJva2U9IiNjY2NjY2MiIHN0cm9rZS13aWR0aD0iMSIvPjxwYXRoIGQ9Ik0xNTAgMTUwIEwxNTAgNDUwIiBzdHJva2U9IiM1NTU1NTUiIHN0cm9rZS13aWR0aD0iMiIvPjxwYXRoIGQ9Ik0yNTAgMTUwIEwyNTAgNDUwIiBzdHJva2U9IiM1NTU1NTUiIHN0cm9rZS13aWR0aD0iMiIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjI4MCIgcj0iNSIgZmlsbD0iIzg4ODg4OCIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjMxMCIgcj0iNSIgZmlsbD0iIzg4ODg4OCIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjM0MCIgcj0iNSIgZmlsbD0iIzg4ODg4OCIvPjx0ZXh0IHg9IjUwJSIgeT0iMzUlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjRweCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iI2ZmZmZmZiI+0JrQu9Cw0YHRgdC40YfQtdGB0LrQuNC5INC/0LjQtNC20LDQujwvdGV4dD48L3N2Zz4=',
  // Новая заглушка для брюк
  pants: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PHBhdGggZD0iTTE1MCAxMDAgTDI1MCAxMDAgTDI2MCA0NTAgTDIyMCA1MDAgTDIwMCA0NTAgTDE4MCA1MDAgTDE0MCA0NTAgWiIgZmlsbD0iIzRiNWM2YiIgc3Ryb2tlPSIjMzY0MzRmIiBzdHJva2Utd2lkdGg9IjMiLz48dGV4dCB4PSI1MCUiIHk9IjI1JSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0cHgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPtCR0YDRjtC60Lg8L3RleHQ+PC9zdmc+',
  // Новая заглушка для шапок
  hat: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PGVsbGlwc2UgY3g9IjIwMCIgY3k9IjIwMCIgcng9IjEwMCIgcnk9IjUwIiBmaWxsPSIjODg4ODg4IiBzdHJva2U9IiM2NjY2NjYiIHN0cm9rZS13aWR0aD0iMyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjRweCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iI2ZmZmZmZiI+0KjQsNC/0LrQsDwvdGV4dD48L3N2Zz4=',
};

// Функция для получения base64 изображения по категории
const getBase64ImageByCategory = (category: string): string => {
  const lowerCategory = category.toLowerCase();
  if (lowerCategory.includes('футболка') || lowerCategory.includes('рубашка')) return BASE64_IMAGES.tshirt;
  if (lowerCategory.includes('джинс') || lowerCategory.includes('брюк')) return BASE64_IMAGES.pants;
  if (lowerCategory.includes('куртка') || lowerCategory.includes('пальто') || lowerCategory.includes('пиджак')) return BASE64_IMAGES.jacket;
  if (lowerCategory.includes('платье')) return BASE64_IMAGES.dress;
  if (lowerCategory.includes('свитер') || lowerCategory.includes('худи') || lowerCategory.includes('толстовка')) return BASE64_IMAGES.sweater;
  if (lowerCategory.includes('обувь') || lowerCategory.includes('кед') || lowerCategory.includes('ботин') || lowerCategory.includes('кроссов')) return BASE64_IMAGES.shoes;
  if (lowerCategory.includes('пиджак') || lowerCategory.includes('блейзер')) return BASE64_IMAGES.blazer;
  if (lowerCategory.includes('шапка') || lowerCategory.includes('кепка') || lowerCategory.includes('берет')) return BASE64_IMAGES.hat;
  if (lowerCategory.includes('одежда')) return BASE64_IMAGES.fashion;
  return BASE64_IMAGES.default;
};

// Моковые данные для тестирования интерфейса
const mockItems: GarmentItem[] = [
  {
    id: '1',
    name: 'Базовая белая футболка',
    description: 'Универсальная хлопковая футболка свободного кроя',
    price: 999,
    imageUrl: 'https://basket-01.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/1.webp',
    category: 'Верх'
  },
  {
    id: '2',
    name: 'Джинсы классические',
    description: 'Прямые джинсы из плотного денима',
    price: 2499,
    imageUrl: 'https://basket-13.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/1.webp',
    category: 'Низ'
  },
  {
    id: '3',
    name: 'Кожаная куртка',
    description: 'Куртка из искусственной кожи с подкладкой',
    price: 5999,
    imageUrl: 'https://basket-16.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/1.webp',
    category: 'Верхняя одежда'
  },
  {
    id: '4',
    name: 'Кеды базовые',
    description: 'Белые кеды из хлопчатобумажной ткани',
    price: 1999,
    imageUrl: 'https://basket-05.wbbasket.ru/vol758/part75846/75846387/images/c516x688/1.webp',
    category: 'Обувь'
  }
];

// Интерфейс для данных распознавания одежды на изображении
interface ClothingRecognitionData {
  items: Array<{
    type: string;
    description: string;
    color: string;
    pattern?: string;
    material?: string;
    gender?: string;
  }>;
  fullDescription: string;
}

// Интерфейс для товара Wildberries
interface WildberriesProduct {
  id: string;
  name: string;
  brand: string;
  price: number;
  priceWithDiscount: number;
  imageUrl: string;
  imageUrls?: string[]; // Добавляем массив альтернативных URL изображений
  url: string;
  rating?: number;
  category?: string;
}

// Интерфейс для товара одежды
interface GarmentItem {
  id: string;
  name: string;
  description: string;
  price: number;
  oldPrice?: number;
  imageUrl: string;
  imageUrls?: string[]; // Добавляем массив альтернативных URL изображений
  category: string;
  gender?: string;
  url?: string;
}

// Интерфейс для предмета одежды из Pinterest
interface ClothingItem {
  type: string;    // Тип предмета (футболка, джинсы и т.д.)
  color: string;   // Цвет предмета
  description: string; // Описание (принт, фасон и т.д.)
  gender: string;  // Пол (мужской, женский)
}

// Интерфейс для результата поиска в Pinterest
interface PinterestOutfit {
  imageUrl: string;
  sourceUrl: string;
  description: string;
  clothingItems: ClothingItem[];
}

interface StylistAssistantProps {
  onReturnHome?: () => void;
}

// Функция для генерации URL изображений товаров Wildberries
const generateImageUrls = (productId: string | number): string[] => {
  // Преобразуем productId в строку, если он не строка
  const productIdStr = typeof productId === 'string' ? productId : String(productId);
  
  // Генерируем URL изображений
  const volDigits = productIdStr.length >= 4 ? 4 : (productIdStr.length >= 3 ? 3 : 1);
  const vol = productIdStr.slice(0, volDigits);
  
  const partDigits = productIdStr.length >= 6 ? 6 : (productIdStr.length >= 5 ? 5 : productIdStr.length);
  const part = productIdStr.slice(0, partDigits);
  
  const lastTwoDigits = productIdStr.slice(-2);
  const bucketNum = (parseInt(lastTwoDigits) % 20) + 1;
  const bucketStr = bucketNum.toString().padStart(2, '0');
  
  // Генерируем URL для нескольких изображений с разных корзин
  const generatedUrls = [];
  
  // Стандартный формат - basket-XX.wbbasket.ru с изображениями webp (1-4)
  for (let i = 1; i <= 4; i++) {
    generatedUrls.push(`https://basket-${bucketStr}.wbbasket.ru/vol${vol}/part${part}/${productIdStr}/images/c516x688/${i}.webp`);
  }
  
  // Альтернативный формат - images.wbstatic.net с jpg изображениями
  generatedUrls.push(`https://images.wbstatic.net/c516x688/new/${productIdStr.slice(0, 4)}/${productIdStr}-1.jpg`);
  
  return generatedUrls;
};

export default function StylistAssistant({ onReturnHome }: StylistAssistantProps) {
  const { setSelectedRole } = useAppContext();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GarmentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isOutfitSearchMode, setIsOutfitSearchMode] = useState(false);
  const [gender, setGender] = useState<'женский' | 'мужской'>('женский');
  const [imageAnalysis, setImageAnalysis] = useState<string | null>(null);
  const [showFullAnalysis, setShowFullAnalysis] = useState<boolean>(true);
  
  // Новые состояния для Pinterest
  const [pinterestQuery, setPinterestQuery] = useState('');
  const [pinterestResults, setPinterestResults] = useState<PinterestOutfit[]>([]);
  const [isPinterestLoading, setIsPinterestLoading] = useState(false);
  
  // Популярные запросы для поиска лука
  const popularOutfitQueries = [
    "Офисный стиль женский",
    "Повседневный образ на осень",
    "Деловой стиль мужской",
    "Вечерний образ для девушки",
    "Спортивный стиль",
    "Летний пляжный лук"
  ];

  // Функция для обработки загрузки файла
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Функция для анализа изображения
  const handleAnalyzeImage = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setApiError(null);
    setSearchResults([]);
    setImageAnalysis(null);

    try {
      console.log('Начинаем загрузку изображения:', selectedFile.name);
      
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('gender', gender);

      console.log('Отправляем запрос на API с гендером:', gender);
      const response = await fetch('/api/analyze-image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Ошибка ответа API:', response.status, errorText);
        throw new Error(`Ошибка при анализе изображения: ${response.status} ${response.statusText}`);
      }

      console.log('Получен успешный ответ от API');
      const data = await response.json();
      console.log('Данные ответа:', data);
      
      // Обрабатываем результаты
      if (data.results && Array.isArray(data.results)) {
        // Добавляем URL для каждого товара и обрабатываем массив изображений
        const resultsWithUrl = data.results.map(item => {
          // Обрабатываем массив URL изображений
          const imageUrls = item.imageUrls || [];
          
          // Если у товара есть id, но нет массива imageUrls, генерируем его
          if (item.id && (!imageUrls || imageUrls.length === 0)) {
            const productId = item.id;
            
            return {
              ...item,
              imageUrls: generateImageUrls(productId),
              url: item.url || `https://www.wildberries.ru/catalog/${item.id}/detail.aspx`
            };
          }
          
          return {
            ...item,
            imageUrls: imageUrls,
            url: item.url || `https://www.wildberries.ru/catalog/${item.id}/detail.aspx`
          };
        });
        
        setSearchResults(resultsWithUrl);
        console.log('Установлены результаты поиска:', resultsWithUrl.length);
        
        // Сохраняем анализ для отображения
        if (data.analysis) {
          setImageAnalysis(data.analysis);
        }
        
        // Если API вернул сообщение об ошибке, но все равно дал результаты,
        // покажем предупреждение
        if (data.error) {
          setApiError(`Примечание: ${data.error}`);
        }
        
        // Если API использовал моковые данные, покажем сообщение
        if (data.api_source === 'mock') {
          setApiError(`Примечание: Использованы тестовые данные, так как произошла ошибка подключения к серверу анализа изображений.`);
        }
      } else {
        console.error('Некорректный формат ответа API:', data);
        setApiError('Получены некорректные данные от сервера');
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Ошибка при обработке запроса:', error);
      setApiError(error instanceof Error ? error.message : 'Произошла ошибка при анализе изображения');
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Функция для поиска товаров по текстовому запросу
  const handleTextSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    setApiError(null);
    try {
      const response = await fetch(`/api/search-products?query=${encodeURIComponent(searchQuery)}&limit=8&gender=${encodeURIComponent(gender)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Обрабатываем массив URL изображений для каждого товара
      const processedResults = data.map(item => {
        // Если у товара есть id, но нет массива imageUrls, генерируем его
        if (item.id && (!item.imageUrls || item.imageUrls.length === 0)) {
          const productId = item.id;
          
          return {
            ...item,
            imageUrls: generateImageUrls(productId),
            url: item.url || `https://www.wildberries.ru/catalog/${item.id}/detail.aspx`
          };
        }
        
        return {
          ...item,
          url: item.url || `https://www.wildberries.ru/catalog/${item.id}/detail.aspx`
        };
      });
      
      setSearchResults(processedResults);
    } catch (error) {
      console.error('Ошибка при поиске товаров:', error);
      setApiError(error instanceof Error ? error.message : 'Произошла ошибка при поиске товаров');
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Функция для поиска образов в Pinterest
  const searchPinterestOutfits = async () => {
    if (!pinterestQuery) {
      setApiError("Пожалуйста, укажите поисковый запрос");
      return;
    }
    
    setIsPinterestLoading(true);
    setApiError(null);
    setPinterestResults([]);
    
    try {
      console.log(`Поиск образов: ${pinterestQuery}, пол: ${gender}`);
      
      // Отправляем GET запрос к нашему API
      const response = await fetch(`/api/search-pinterest?query=${encodeURIComponent(pinterestQuery)}&gender=${encodeURIComponent(gender)}&limit=3`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка при поиске (${response.status}): ${errorText}`);
      }
      
      const results = await response.json();
      
      if (Array.isArray(results) && results.length > 0) {
        console.log(`Получено ${results.length} образов из Pinterest`);
        setPinterestResults(results);
      } else {
        setApiError("Не найдено подходящих образов. Попробуйте изменить запрос.");
        console.warn("Не найдено образов или получен некорректный формат данных:", results);
      }
    } catch (error) {
      console.error("Ошибка при поиске образов:", error);
      setApiError(`Ошибка при поиске образов: ${error.message || 'Неизвестная ошибка'}`);
    } finally {
      setIsPinterestLoading(false);
    }
  };

  // Функция для использования предустановленного запроса
  const usePresetQuery = (query: string) => {
    setPinterestQuery(query);
    
    // Определяем пол по запросу
    if (query.toLowerCase().includes('мужской') || query.toLowerCase().includes('мужчины')) {
      setGender('мужской');
    } else if (query.toLowerCase().includes('женский') || query.toLowerCase().includes('девушки')) {
      setGender('женский');
    }
  };

  // Переключение между режимами поиска в текстовом поиске
  const toggleSearchMode = () => {
    setIsOutfitSearchMode(!isOutfitSearchMode);
    
    // Сбрасываем результаты при переключении режима
    setSearchResults([]);
    setPinterestResults([]);
  };

  const formatResultsCount = (count: number): string => {
    if (count === 1) {
      return "Найден 1 образ";
    } else if (count >= 2 && count <= 4) {
      return `Найдено ${count} образа`;
    } else {
      return `Найдено ${count} образов`;
    }
  };

  // Компонент ProductCard с обработкой ошибок загрузки изображений
  const ProductCard: React.FC<{ product: GarmentItem }> = ({ product }) => {
    const [imgSrc, setImgSrc] = useState(product.imageUrl);
    const [imgError, setImgError] = useState(false);
    const [loadAttempts, setLoadAttempts] = useState(0);
    const [currentImageIndex, setCurrentImageIndex] = useState(0); // Индекс текущего изображения
    const [isHovering, setIsHovering] = useState(false); // Состояние наведения на карточку

    // Эффект для переключения изображений при наведении
    useEffect(() => {
      if (!product.imageUrls || product.imageUrls.length <= 1 || !isHovering) return;
      
      // Запускаем автоматическое переключение изображений при наведении
      const interval = setInterval(() => {
        setCurrentImageIndex(prevIndex => {
          const nextIndex = (prevIndex + 1) % product.imageUrls!.length;
          setImgSrc(product.imageUrls![nextIndex]);
          return nextIndex;
        });
      }, 1500); // Меняем изображение каждые 1.5 секунды

      return () => clearInterval(interval);
    }, [isHovering, product.imageUrls]);

    // Вызываем useEffect для обновления источника изображения при изменении товара
    useEffect(() => {
      setImgSrc(product.imageUrl);
      setImgError(false);
      setLoadAttempts(0);
      setCurrentImageIndex(0);
    }, [product]);

    // Функция для переключения на следующее изображение при клике
    const handleNextImage = (e: React.MouseEvent) => {
      e.stopPropagation();
      
      if (!product.imageUrls || product.imageUrls.length <= 1) return;
      
      const nextIndex = (currentImageIndex + 1) % product.imageUrls.length;
      setCurrentImageIndex(nextIndex);
      setImgSrc(product.imageUrls[nextIndex]);
    };

    // Функция определения категории из названия
    const getCategoryFromName = (name: string): string => {
      const lowerName = name.toLowerCase();
      if (lowerName.includes('футболка') || lowerName.includes('рубашка')) return 'tshirt';
      if (lowerName.includes('джинс') || lowerName.includes('брюк')) return 'pants';
      if (lowerName.includes('куртка') || lowerName.includes('пальто') || lowerName.includes('пиджак')) return 'jacket';
      if (lowerName.includes('пиджак') || lowerName.includes('блейзер')) return 'blazer';
      if (lowerName.includes('платье')) return 'dress';
      if (lowerName.includes('свитер') || lowerName.includes('худи') || lowerName.includes('толстовка')) return 'sweater';
      if (lowerName.includes('обувь') || lowerName.includes('кед') || lowerName.includes('ботин') || lowerName.includes('кроссов')) return 'shoes';
      if (lowerName.includes('шапка') || lowerName.includes('кепка') || lowerName.includes('берет')) return 'hat';
      return 'fashion';
    };

    // Обработчик ошибки загрузки изображения
    const handleImageError = () => {
      console.log(`Ошибка загрузки изображения: ${imgSrc} (попытка ${loadAttempts + 1})`);
      setLoadAttempts(prev => prev + 1);
      
      // Если у товара есть массив изображений и мы не перебрали все
      if (product.imageUrls && product.imageUrls.length > currentImageIndex + 1) {
        // Переключаемся на следующее изображение из массива
        const nextIndex = currentImageIndex + 1;
        console.log(`Пробуем следующее изображение из массива: ${product.imageUrls[nextIndex]}`);
        setCurrentImageIndex(nextIndex);
        setImgSrc(product.imageUrls[nextIndex]);
        return;
      }
      
      // Если превышено количество попыток или это уже заглушка, используем base64 изображение
      if (loadAttempts >= 2 || imgSrc.startsWith('data:')) {
        console.log('Превышено количество попыток загрузки, используем base64 изображение');
        setImgError(true);
        
        // Получаем категорию для base64 изображения
        const category = getCategoryFromName(product.name || product.category || '');
        const base64Image = getBase64ImageByCategory(category);
        
        setImgSrc(base64Image);
        return;
      }
      
      // Если не удалось загрузить изображение и есть ID товара, пробуем сгенерировать новые URL
      if (!imgError && product.id) {
        // Генерируем URL изображений с помощью нашей функции
        const generatedUrls = generateImageUrls(product.id);
        
        // Сохраняем сгенерированные URL в массив product.imageUrls
        product.imageUrls = generatedUrls;
        
        console.log(`Генерируем URL изображений: `, generatedUrls);
        
        // Используем первое изображение
        setImgSrc(generatedUrls[0]);
      } else {
        // Если всё не удалось, используем заглушку
        setImgError(true);
        
        // Получаем категорию для base64 изображения
        const category = getCategoryFromName(product.name || product.category || '');
        const base64Image = getBase64ImageByCategory(category);
        
        console.log(`Используем base64 изображение для категории: ${category}`);
        setImgSrc(base64Image);
      }
    };

    return (
      <Card className="overflow-hidden p-0">
        <div 
          className="relative h-48 cursor-pointer" 
          onClick={handleNextImage}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
        >
          <img 
            src={imgSrc} 
            alt={product.name} 
            className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
            onError={handleImageError}
          />
          <div className="absolute top-3 right-3 bg-black/70 text-white px-2 py-1 rounded-full text-xs">
            {product.category}
          </div>
          {product.gender && (
            <div className="absolute top-3 left-3 bg-primary/80 text-primary-foreground px-2 py-1 rounded-full text-xs">
              {product.gender === 'мужской' ? 'М' : product.gender === 'женский' ? 'Ж' : 'У'}
            </div>
          )}
          {/* Добавляем индикаторы изображений, если есть несколько */}
          {product.imageUrls && product.imageUrls.length > 1 && (
            <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
              {product.imageUrls.map((_, index) => (
                <div 
                  key={index} 
                  className={`w-2 h-2 rounded-full ${index === currentImageIndex ? 'bg-white' : 'bg-white/50'}`}
                />
              ))}
            </div>
          )}
        </div>
        <CardContent className="p-5">
          <h3 className="font-semibold text-base mb-1">{product.name}</h3>
          <p className="text-sm text-muted-foreground mb-4">{product.description}</p>
          <div className="flex justify-between items-center">
            <div className="space-y-1">
              <span className="font-bold">{product.price} ₽</span>
            </div>
            <Button size="sm" onClick={() => { if (product.url) window.open(product.url, '_blank'); }}>
              <ShoppingBag className="h-4 w-4 mr-2" />
              Купить
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Ассистент стилиста</h1>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setSelectedRole(null)}
          className="flex items-center gap-2"
        >
          <Home className="h-4 w-4" />
          Вернуться на главную
        </Button>
      </div>
      
      <Tabs defaultValue="photo-search" className="w-full">
        <TabsList className="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground mb-6 w-full md:w-auto">
          <TabsTrigger 
            value="photo-search"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
          >
            Поиск по фото
          </TabsTrigger>
          <TabsTrigger 
            value="text-search"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
          >
            Поиск по описанию
          </TabsTrigger>
          <TabsTrigger 
            value="wardrobe"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
          >
            Мой гардероб
          </TabsTrigger>
          <TabsTrigger 
            value="recommendations"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
          >
            Рекомендации
          </TabsTrigger>
        </TabsList>

        <TabsContent 
          value="photo-search" 
          className="mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <div className="card rounded-xl border border-border/40 bg-card p-6 shadow-sm transition-all duration-200 hover:shadow-md">
            <div className="flex flex-col space-y-1.5 pb-4">
              <h3 className="text-xl font-semibold leading-none tracking-tight text-card-foreground">
                Найдите похожие вещи по фотографии
              </h3>
              <p className="text-sm text-muted-foreground">
                Загрузите изображение одежды, и мы найдем похожие товары
              </p>
            </div>
            
            <div className="pt-0">
              <div className="space-y-8">
                <div className="space-y-4">
                  <label 
                    htmlFor="image-upload" 
                    className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-10 flex flex-col items-center justify-center cursor-pointer hover:border-primary/50 transition-colors"
                  >
                    {previewUrl ? (
                      <div className="relative w-full max-w-xs mx-auto">
                        <img 
                          src={previewUrl} 
                          alt="Preview" 
                          className="rounded-md max-h-[300px] mx-auto object-contain"
                        />
                      </div>
                    ) : (
                      <>
                        <div className="w-12 h-12 rounded-full bg-muted-foreground/10 flex items-center justify-center mb-4">
                          <svg 
                            className="w-6 h-6 text-muted-foreground" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24" 
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                        </div>
                        <div className="text-sm text-center text-muted-foreground">
                          <span className="font-medium">Перетащите изображение сюда</span> или нажмите для выбора
                        </div>
                        <p className="text-xs text-muted-foreground/70 mt-2">
                          Поддерживаются JPG, PNG и GIF
                        </p>
                      </>
                    )}
                    <input
                      id="image-upload"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleFileChange}
                    />
                  </label>
                  
                  <div className="flex justify-center">
                    <Button 
                      onClick={handleAnalyzeImage} 
                      disabled={!selectedFile || isLoading}
                      className="inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 active:scale-[0.98] h-10 px-4 py-2"
                    >
                      {isLoading ? (
                        <>
                          <div className="animate-spin mr-2 w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full" />
                          Анализируем...
                        </>
                      ) : 'Найти похожие вещи'}
                    </Button>
                  </div>
                  
                  {apiError && (
                    <div className="p-4 bg-destructive/10 text-destructive rounded-md text-sm">
                      {apiError}
                    </div>
                  )}
                  
                  {isLoading && (
                    <div className="text-center py-12">
                      <div className="animate-spin inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
                      <p className="text-muted-foreground">Анализируем изображение и ищем похожие товары...</p>
                    </div>
                  )}
                  
                  {searchResults.length > 0 && !isLoading && (
                    <div className="space-y-4" id="search-results-container">
                      {imageAnalysis && (
                        <div className="p-5 mb-6 bg-muted/30 rounded-lg border border-border/40 shadow-sm">
                          <h3 className="font-bold text-lg mb-3">Анализ изображения:</h3>
                          <div className="flex items-center gap-3 mb-4">
                            {previewUrl && (
                              <div className="w-20 h-20 rounded-md overflow-hidden flex-shrink-0">
                                <img src={previewUrl} alt="Загруженное фото" className="w-full h-full object-cover" />
                              </div>
                            )}
                            <div>
                              <p className="text-sm font-medium text-foreground">Алгоритм определил что на изображении:</p>
                              <div className="mt-1 text-muted-foreground text-sm flex flex-wrap gap-1">
                                {searchResults.slice(0, 3).map((item, index) => (
                                  <Badge key={index} variant="outline" className="bg-primary/10">
                                    {item.category}: {item.name}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                          
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="w-full text-xs flex items-center justify-center gap-1 mb-3"
                            onClick={() => setShowFullAnalysis(!showFullAnalysis)}
                          >
                            {showFullAnalysis ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                            {showFullAnalysis ? "Скрыть полный анализ" : "Показать полный анализ"}
                          </Button>
                          
                          {showFullAnalysis && (
                            <div className="text-muted-foreground text-sm whitespace-pre-line border-t border-border/40 pt-3">
                              <p className="font-medium text-foreground mb-1">Полный анализ:</p>
                              {imageAnalysis}
                            </div>
                          )}
                        </div>
                      )}
                      <h2 className="text-xl font-semibold">Найдено {searchResults.length} товаров</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {searchResults.map((item) => (
                          <ProductCard key={item.id} product={item} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent 
          value="text-search" 
          className="mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <div className="card rounded-xl border border-border/40 bg-card p-6 shadow-sm transition-all duration-200 hover:shadow-md">
            <div className="flex flex-col space-y-1.5 pb-4">
              <h3 className="text-xl font-semibold leading-none tracking-tight text-card-foreground">
                Поиск одежды по описанию
              </h3>
              <p className="text-sm text-muted-foreground">
                Опишите, что вы ищете, и мы подберем подходящие варианты
              </p>
            </div>
            <div className="pt-0">
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="flex items-center gap-4 mb-2">
                    <Button 
                      variant={isOutfitSearchMode ? "default" : "outline"}
                      className="inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] h-10 px-4 py-2"
                      onClick={() => setIsOutfitSearchMode(true)}
                    >
                      Поиск образов
                    </Button>
                    <Button 
                      variant={!isOutfitSearchMode ? "default" : "outline"}
                      className="inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] h-10 px-4 py-2"
                      onClick={() => setIsOutfitSearchMode(false)}
                    >
                      Поиск товаров
                    </Button>
                  </div>
                  
                  {!isOutfitSearchMode ? (
                    <>
                      <div className="flex gap-2">
                        <Input
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          placeholder="Опишите товар, например: черное платье"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleTextSearch()}
                        />
                        <Button 
                          onClick={handleTextSearch} 
                          disabled={isLoading}
                          className="inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 active:scale-[0.98] h-10 px-4 py-2"
                        >
                          {isLoading ? "Поиск..." : "Найти"}
                        </Button>
                      </div>
                      
                      <div className="flex flex-wrap gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:scale-[0.98] h-9 rounded-md px-3 text-xs"
                          onClick={() => { setSearchQuery('Белая футболка'); handleTextSearch(); }}
                        >
                          Белая футболка
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:scale-[0.98] h-9 rounded-md px-3 text-xs"
                          onClick={() => { setSearchQuery('Черные джинсы'); handleTextSearch(); }}
                        >
                          Черные джинсы
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:scale-[0.98] h-9 rounded-md px-3 text-xs"
                          onClick={() => { setSearchQuery('Кожаная куртка'); handleTextSearch(); }}
                        >
                          Кожаная куртка
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:scale-[0.98] h-9 rounded-md px-3 text-xs"
                          onClick={() => { setSearchQuery('Платье миди'); handleTextSearch(); }}
                        >
                          Платье миди
                        </Button>
                      </div>
                    </>
                  ) : (
                    // Поиск образов
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <Input
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          placeholder="Опишите желаемый образ, например: Повседневный образ на осень"
                          value={pinterestQuery}
                          onChange={(e) => setPinterestQuery(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && searchPinterestOutfits()}
                        />
                        <Button 
                          onClick={searchPinterestOutfits} 
                          disabled={isPinterestLoading}
                          className="inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 active:scale-[0.98] h-10 px-4 py-2"
                        >
                          {isPinterestLoading ? "Поиск..." : "Найти"}
                        </Button>
                      </div>
                      
                      <div className="flex gap-2 items-center">
                        <div className="text-sm text-muted-foreground">Пол:</div>
                        <Button
                          variant={gender === 'женский' ? "default" : "outline"}
                          size="sm"
                          className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 text-xs"
                          onClick={() => setGender('женский')}
                        >
                          Женский
                        </Button>
                        <Button
                          variant={gender === 'мужской' ? "default" : "outline"}
                          size="sm"
                          className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 text-xs"
                          onClick={() => setGender('мужской')}
                        >
                          Мужской
                        </Button>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="text-sm text-muted-foreground">Популярные запросы:</div>
                        <div className="flex flex-wrap gap-2">
                          {popularOutfitQueries.map((query, index) => (
                            <Button
                              key={index}
                              variant="outline"
                              size="sm"
                              className="inline-flex items-center justify-center whitespace-nowrap font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground active:scale-[0.98] h-9 rounded-md px-3 text-xs"
                              onClick={() => usePresetQuery(query)}
                            >
                              {query}
                            </Button>
                          ))}
                        </div>
                      </div>
                      
                      {/* Результаты поиска образов */}
                      {isPinterestLoading ? (
                        <div className="text-center py-12">
                          <div className="animate-spin inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
                          <p className="text-muted-foreground">Ищем стильные образы и подбираем похожие товары...</p>
                        </div>
                      ) : pinterestResults.length > 0 ? (
                        <div className="space-y-4 mt-8">
                          <div className="flex items-center justify-between">
                            <h2 className="text-2xl font-semibold text-foreground">
                              {formatResultsCount(pinterestResults.length)}
                            </h2>
                            {/* Если нужны дополнительные кнопки, можно добавить здесь */}
                          </div>
                          
                          {/* Список результатов */}
                          <div className="space-y-8">
                            {pinterestResults.map((outfit, index) => (
                              <PinterestOutfitSection 
                                key={`${outfit.imageUrl}-${index}`}
                                outfit={outfit}
                                isLoading={false}
                              />
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent 
          value="wardrobe"
          className="mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {/* Содержимое вкладки Мой гардероб */}
        </TabsContent>
        
        <TabsContent 
          value="recommendations"
          className="mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {/* Содержимое вкладки Рекомендации */}
        </TabsContent>
      </Tabs>
    </div>
  );
} 