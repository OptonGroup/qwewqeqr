"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, Search, RefreshCw, ShoppingBag, Plus, Pencil, Link } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { ProductCard, GarmentItem } from './product-card';
import PinterestOutfitSection from './pinterest-outfit-section';
import { Badge } from '@/components/ui/badge';

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
};

// Функция для получения base64 изображения по категории
const getBase64ImageByCategory = (category: string): string => {
  const lowerCategory = category.toLowerCase();
  if (lowerCategory.includes('футболка') || lowerCategory.includes('рубашка')) return BASE64_IMAGES.tshirt;
  if (lowerCategory.includes('джинс') || lowerCategory.includes('брюк')) return BASE64_IMAGES.jeans;
  if (lowerCategory.includes('куртка') || lowerCategory.includes('пальто') || lowerCategory.includes('плащ')) return BASE64_IMAGES.jacket;
  if (lowerCategory.includes('платье')) return BASE64_IMAGES.dress;
  if (lowerCategory.includes('свитер') || lowerCategory.includes('худи') || lowerCategory.includes('толстовка')) return BASE64_IMAGES.sweater;
  if (lowerCategory.includes('обувь') || lowerCategory.includes('кед') || lowerCategory.includes('ботин') || lowerCategory.includes('кроссов')) return BASE64_IMAGES.shoes;
  if (lowerCategory.includes('одежда')) return BASE64_IMAGES.fashion;
  return BASE64_IMAGES.default;
};

interface GarmentItem {
  id: string;
  name: string;
  description: string;
  price: number;
  oldPrice?: number;
  imageUrl: string;
  imageUrls?: string[]; // Добавляем массив альтернативных URL изображений
  category: string;
  url?: string;
  gender?: string;
}

// Моковые данные для тестирования интерфейса
const mockItems: GarmentItem[] = [
  {
    id: '1',
    name: 'Базовая белая футболка',
    description: 'Универсальная хлопковая футболка свободного кроя',
    price: 999,
    imageUrl: 'https://basket-01.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-01.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/1.webp',
      'https://basket-02.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/2.webp',
      'https://basket-03.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/3.webp'
    ],
    category: 'Верх'
  },
  {
    id: '2',
    name: 'Джинсы классические',
    description: 'Прямые джинсы из плотного денима',
    price: 2499,
    imageUrl: 'https://basket-13.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-13.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/1.webp',
      'https://basket-12.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/2.webp',
      'https://basket-11.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/3.webp'
    ],
    category: 'Низ'
  },
  {
    id: '3',
    name: 'Кожаная куртка',
    description: 'Куртка из искусственной кожи с подкладкой',
    price: 5999,
    imageUrl: 'https://basket-16.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-16.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/1.webp',
      'https://basket-15.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/2.webp',
      'https://basket-14.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/3.webp'
    ],
    category: 'Верхняя одежда'
  },
  {
    id: '4',
    name: 'Кеды базовые',
    description: 'Белые кеды из хлопчатобумажной ткани',
    price: 1999,
    imageUrl: 'https://basket-05.wbbasket.ru/vol758/part75846/75846387/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-05.wbbasket.ru/vol758/part75846/75846387/images/c516x688/1.webp',
      'https://basket-06.wbbasket.ru/vol758/part75846/75846387/images/c516x688/2.webp',
      'https://basket-07.wbbasket.ru/vol758/part75846/75846387/images/c516x688/3.webp'
    ],
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

const StylistAssistant: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GarmentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  
  // Новые состояния для Pinterest
  const [pinterestQuery, setPinterestQuery] = useState('');
  const [pinterestResults, setPinterestResults] = useState<PinterestOutfit[]>([]);
  const [isPinterestLoading, setIsPinterestLoading] = useState(false);
  const [isOutfitSearchMode, setIsOutfitSearchMode] = useState(false);
  const [gender, setGender] = useState('женский');
  
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
      // Создаем URL для предпросмотра изображения
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      // Сбрасываем предыдущие результаты
      setRecommendations([]);
    }
  };
  
  // Функция для анализа изображения с помощью API
  const handleAnalyzeImage = async () => {
    if (!selectedFile) return;
    
    setIsLoading(true);
    setApiError(null); // Сбрасываем ошибку перед новым запросом
    
    try {
      // Создаем FormData для отправки файла
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Отправляем запрос на анализ изображения
      const response = await fetch('http://localhost:8000/analyze-image', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при анализе изображения: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Проверяем, содержит ли ответ сообщение об ошибке от сервера
      if (data.error) {
        setApiError(data.error);
        console.error('Ошибка API:', data.error);
        return;
      }
      
      setRecommendations(data.elements);
    } catch (error) {
      console.error('Ошибка при анализе изображения:', error);
      setApiError(`Не удалось выполнить запрос: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Функция для поиска товаров по текстовому запросу
  const handleTextSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/search-products?query=${encodeURIComponent(searchQuery)}&limit=8`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Error searching products:', error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Функция для поиска образов в Pinterest
  const handlePinterestSearch = async () => {
    if (!pinterestQuery.trim()) return;
    
    setIsPinterestLoading(true);
    setPinterestResults([]);
    
    try {
      const response = await fetch('/api/search-pinterest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: pinterestQuery,
          gender: gender
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setPinterestResults(data);
      
      console.log('Результаты поиска Pinterest:', data);
    } catch (error) {
      console.error('Error searching Pinterest:', error);
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

  // Компонент ProductCard с обработкой ошибок загрузки изображений
  const ProductCard: React.FC<{ product: GarmentItem }> = ({ product }) => {
    const [imgSrc, setImgSrc] = useState(product.imageUrl);
    const [imgError, setImgError] = useState(false);
    const [imgIndex, setImgIndex] = useState(0); // Индекс текущего URL в массиве imageUrls
    const [loadAttempts, setLoadAttempts] = useState(0); // Счетчик попыток загрузки

    // Вызываем useEffect для обновления источника изображения при изменении товара
    useEffect(() => {
      setImgSrc(product.imageUrl);
      setImgError(false);
      setImgIndex(0);
      setLoadAttempts(0);
    }, [product.imageUrl, product.id]);

    // Функция для определения категории товара
    const getCategoryFromName = (name: string): string => {
      const lowerName = name.toLowerCase();
      if (lowerName.includes('футболка') || lowerName.includes('рубашка')) return 'tshirt';
      if (lowerName.includes('джинс') || lowerName.includes('брюк')) return 'jeans';
      if (lowerName.includes('куртка') || lowerName.includes('пальто') || lowerName.includes('пиджак')) return 'jacket';
      if (lowerName.includes('платье')) return 'dress';
      if (lowerName.includes('свитер') || lowerName.includes('худи') || lowerName.includes('толстовка')) return 'sweater';
      if (lowerName.includes('обувь') || lowerName.includes('кед') || lowerName.includes('ботин') || lowerName.includes('кроссов')) return 'shoes';
      return 'fashion';
    };

    // Обработчик ошибки загрузки изображения
    const handleImageError = () => {
      console.log(`Ошибка загрузки изображения: ${imgSrc} (попытка ${loadAttempts + 1})`);
      setLoadAttempts(prev => prev + 1);
      
      if (loadAttempts >= 5) {
        console.log('Превышено количество попыток загрузки, используем base64 изображение');
        setImgError(true);
        
        // Получаем категорию для base64 изображения
        const category = getCategoryFromName(product.name || product.category || '');
        const base64Image = getBase64ImageByCategory(category);
        
        setImgSrc(base64Image);
        return;
      }
      
      // Если есть массив альтернативных URL изображений
      if (product.imageUrls && product.imageUrls.length > imgIndex + 1) {
        // Переходим к следующему URL в массиве
        const nextIndex = imgIndex + 1;
        setImgIndex(nextIndex);
        setImgSrc(product.imageUrls[nextIndex]);
        console.log(`Пробуем альтернативный URL: ${product.imageUrls[nextIndex]}`);
      } 
      // Если нет массива или все URL уже испробованы
      else if (!imgError) {
        // Пробуем сгенерировать URL на основе ID товара
        if (product.id) {
          const productId = product.id;
          
          // Определяем части URL на основе ID товара
          // Для vol берем первые 3-4 цифры ID
          const volDigits = productId.length >= 4 ? 4 : (productId.length >= 3 ? 3 : 1);
          const vol = productId.slice(0, volDigits);
          
          // Для part берем первые 5-6 цифр ID
          const partDigits = productId.length >= 6 ? 6 : (productId.length >= 5 ? 5 : productId.length);
          const part = productId.slice(0, partDigits);
          
          // Определяем номер бакета на основе ID
          // Используем остаток от деления последних 2 цифр ID на 20 + 1
          // чтобы получить номера от 1 до 20
          const lastTwoDigits = productId.slice(-2);
          const bucketNum = (parseInt(lastTwoDigits) % 20) + 1;
          const bucketStr = bucketNum.toString().padStart(2, '0');
          
          const newImageUrl = `https://basket-${bucketStr}.wbbasket.ru/vol${vol}/part${part}/${productId}/images/c516x688/1.webp`;
          console.log(`Генерируем URL изображения: ${newImageUrl}`);
          
          setImgSrc(newImageUrl);
        } 
        // Если не удалось сгенерировать URL, используем base64
        else {
          setImgError(true);
          
          // Получаем категорию для base64 изображения
          const category = getCategoryFromName(product.name || product.category || '');
          const base64Image = getBase64ImageByCategory(category);
          
          console.log(`Используем base64 изображение для категории: ${category}`);
          setImgSrc(base64Image);
        }
      }
    };

    return (
      <Card className="overflow-hidden p-0">
        <div className="relative h-48">
          <img 
            src={imgSrc} 
            alt={product.name} 
            className="w-full h-full object-cover"
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
        </div>
        <CardContent className="p-5">
          <h3 className="font-semibold text-base mb-1">{product.name}</h3>
          <p className="text-sm text-muted-foreground mb-4">{product.description}</p>
          <div className="flex justify-between items-center">
            <div className="space-y-1">
              <span className="font-bold">{product.price} ₽</span>
              {product.oldPrice && (
                <span className="text-sm text-muted-foreground line-through block">
                  {product.oldPrice} ₽
                </span>
              )}
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
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-8 text-foreground/90">Персональный стилист</h1>
      
      <Tabs defaultValue="text-search" className="w-full">
        <TabsList className="mb-6 w-full md:w-auto">
          <TabsTrigger value="image-search">Поиск по фото</TabsTrigger>
          <TabsTrigger value="text-search">Поиск по описанию</TabsTrigger>
          <TabsTrigger value="wardrobe">Мой гардероб</TabsTrigger>
          <TabsTrigger value="recommendations">Рекомендации</TabsTrigger>
        </TabsList>
        
        <TabsContent value="image-search">
          <Card>
            <CardHeader>
              <CardTitle>Найдите похожие вещи по фотографии</CardTitle>
              <CardDescription>
                Загрузите изображение одежды, и мы найдем похожие товары
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                <div className="border-2 border-dashed rounded-xl p-8 transition-colors hover:border-primary/50 bg-background">
                  <input
                    type="file"
                    id="image-upload"
                    className="hidden"
                    accept="image/*"
                    onChange={handleFileChange}
                  />
                  <label 
                    htmlFor="image-upload" 
                    className="cursor-pointer flex flex-col items-center justify-center"
                  >
                    {previewUrl ? (
                      <div className="w-full">
                        <img 
                          src={previewUrl} 
                          alt="Preview" 
                          className="max-h-60 mx-auto rounded-lg object-contain" 
                        />
                        <p className="text-sm text-center mt-4 text-muted-foreground">
                          Нажмите, чтобы заменить изображение
                        </p>
                      </div>
                    ) : (
                      <div className="text-center">
                        <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-lg font-medium mb-2">Загрузите изображение одежды</p>
                        <p className="text-sm text-muted-foreground">
                          Перетащите файл сюда или нажмите для выбора
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          Поддерживаемые форматы: JPG, PNG, WEBP
                        </p>
                      </div>
                    )}
                  </label>
                </div>
                
                <div className="flex justify-center">
                  <Button 
                    onClick={handleAnalyzeImage} 
                    disabled={isLoading || !selectedFile}
                    className="px-8"
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Анализ изображения...
                      </>
                    ) : (
                      <>
                        <Search className="mr-2 h-4 w-4" />
                        Найти похожие
                      </>
                    )}
                  </Button>
                </div>
                
                {apiError && (
                  <div className="mt-4 p-4 bg-destructive/10 text-destructive rounded-md">
                    <p className="font-medium">Внимание:</p>
                    <p>{apiError}</p>
                    <p className="text-sm mt-2">Показаны тестовые данные вместо реального анализа. Проверьте, запущен ли Python API.</p>
                  </div>
                )}
                
                {recommendations.length > 0 && (
                  <div className="space-y-8 mt-8">
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h2 className="text-xl font-bold mb-4">Распознанная одежда:</h2>
                      <ul className="list-disc pl-6 space-y-2">
                        {recommendations.map((item, index) => (
                          <li key={index}>
                            <span className="font-semibold">{item.type}</span>: {item.color} {item.description}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="space-y-8">
                      {recommendations.map((item, index) => (
                        <div key={index} className="space-y-4">
                          <h3 className="text-lg font-semibold">{item.type} {item.color}</h3>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {item.wb_products && item.wb_products.length > 0 ? (
                              item.wb_products.map((product, productIndex) => (
                                <Card key={`${index}-${productIndex}`} className="overflow-hidden">
                                  <div className="relative">
                                    <img 
                                      src={product.image_url} 
                                      alt={product.name} 
                                      className="w-full h-64 object-cover"
                                    />
                                    <Badge className="absolute top-2 right-2 bg-gray-800 text-white">
                                      {item.type}
                                    </Badge>
                                  </div>
                                  <CardHeader className="p-4">
                                    <CardTitle className="text-lg">{product.name}</CardTitle>
                                    <div className="text-sm text-gray-500">{product.brand}</div>
                                  </CardHeader>
                                  <CardContent className="p-4 pt-0">
                                    <div className="flex justify-between items-center mb-4">
                                      <div className="font-bold text-xl">
                                        {product.sale_price} ₽
                                      </div>
                                      {product.discount > 0 && (
                                        <div className="flex items-center">
                                          <span className="text-gray-500 line-through text-sm mr-2">
                                            {product.price} ₽
                                          </span>
                                          <Badge className="bg-red-500">-{product.discount}%</Badge>
                                        </div>
                                      )}
                                    </div>
                                    <Button 
                                      className="w-full"
                                      onClick={() => window.open(product.product_url, '_blank')}
                                    >
                                      Купить
                                    </Button>
                                  </CardContent>
                                </Card>
                              ))
                            ) : (
                              <Card className="col-span-3">
                                <CardContent className="p-6">
                                  <p className="text-center text-gray-500">
                                    Не найдено товаров для {item.type} {item.color}
                                  </p>
                                </CardContent>
                              </Card>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="text-search">
          <Card>
            <CardHeader>
              <CardTitle>Поиск одежды по описанию</CardTitle>
              <CardDescription>
                Опишите, что вы ищете, и мы подберем подходящие варианты
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                <div className="space-y-4">
                  <div className="flex items-center gap-4 mb-2">
                    <Button 
                      variant={isOutfitSearchMode ? "default" : "outline"} 
                      onClick={() => setIsOutfitSearchMode(true)}
                    >
                      Поиск образов
                    </Button>
                    <Button 
                      variant={!isOutfitSearchMode ? "default" : "outline"} 
                      onClick={() => setIsOutfitSearchMode(false)}
                    >
                      Поиск товаров
                    </Button>
                  </div>
                  
                  {isOutfitSearchMode ? (
                    <>
                      {/* Поиск образов */}
                      <div className="space-y-4">
                        <div className="flex gap-2">
                          <Input
                            placeholder="Опишите желаемый образ, например: Повседневный образ на осень"
                            value={pinterestQuery}
                            onChange={(e) => setPinterestQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handlePinterestSearch()}
                          />
                          <Button onClick={handlePinterestSearch} disabled={isPinterestLoading}>
                            {isPinterestLoading ? "Поиск..." : "Найти"}
                          </Button>
                        </div>
                        
                        <div className="flex gap-2 items-center">
                          <div className="text-sm text-muted-foreground">Пол:</div>
                          <Button
                            variant={gender === 'женский' ? "default" : "outline"}
                            size="sm"
                            onClick={() => setGender('женский')}
                          >
                            Женский
                          </Button>
                          <Button
                            variant={gender === 'мужской' ? "default" : "outline"}
                            size="sm"
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
                                onClick={() => usePresetQuery(query)}
                              >
                                {query}
                              </Button>
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      {/* Результаты поиска образов */}
                      {isPinterestLoading ? (
                        <div className="text-center py-12">
                          <div className="animate-spin inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
                          <p className="text-muted-foreground">Ищем стильные образы и подбираем похожие товары...</p>
                        </div>
                      ) : pinterestResults.length > 0 ? (
                        <div className="space-y-8">
                          <h2 className="text-2xl font-semibold mt-8 mb-4">Найдено {pinterestResults.length} образов</h2>
                          {pinterestResults.map((outfit, index) => (
                            <PinterestOutfitSection 
                              key={index} 
                              outfit={outfit} 
                              isLoading={false} 
                            />
                          ))}
                        </div>
                      ) : null}
                    </>
                  ) : (
                    <>
                      {/* Поиск товаров */}
                      <div className="flex gap-2">
                        <Input
                          placeholder="Опишите товар, например: черное платье"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleTextSearch()}
                        />
                        <Button onClick={handleTextSearch} disabled={isLoading}>
                          {isLoading ? "Поиск..." : "Найти"}
                        </Button>
                      </div>
                      
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => { setSearchQuery('Белая футболка'); handleTextSearch(); }}>
                          Белая футболка
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => { setSearchQuery('Черные джинсы'); handleTextSearch(); }}>
                          Черные джинсы
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => { setSearchQuery('Кожаная куртка'); handleTextSearch(); }}>
                          Кожаная куртка
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => { setSearchQuery('Платье миди'); handleTextSearch(); }}>
                          Платье миди
                        </Button>
                      </div>
                      
                      {/* Результаты поиска товаров */}
                      {isLoading ? (
                        <div className="text-center py-12">
                          <div className="animate-spin inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
                          <p className="text-muted-foreground">Ищем товары...</p>
                        </div>
                      ) : searchResults.length > 0 ? (
                        <div className="mt-8">
                          <h2 className="text-2xl font-semibold mb-4">Найдено {searchResults.length} товаров</h2>
                          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                            {searchResults.map((product) => (
                              <ProductCard key={product.id} product={product} />
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="wardrobe">
          <Card>
            <CardHeader>
              <CardTitle>Мой гардероб</CardTitle>
              <CardDescription>
                Управляйте своим гардеробом и создавайте комплекты
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold">Вещи в гардеробе</h3>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Добавить вещь
                  </Button>
                </div>
                
                <Tabs defaultValue="all" className="w-full">
                  <TabsList className="mb-4">
                    <TabsTrigger value="all">Все</TabsTrigger>
                    <TabsTrigger value="tops">Верх</TabsTrigger>
                    <TabsTrigger value="bottoms">Низ</TabsTrigger>
                    <TabsTrigger value="outerwear">Верхняя одежда</TabsTrigger>
                    <TabsTrigger value="shoes">Обувь</TabsTrigger>
                    <TabsTrigger value="accessories">Аксессуары</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="all">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                      {mockItems.slice(0, 4).map(item => (
                        <div 
                          key={item.id}
                          className="border rounded-xl overflow-hidden bg-background group hover:border-primary cursor-pointer transition-colors"
                        >
                          <div className="h-40 relative">
                            <img 
                              src={item.imageUrl}
                              alt={item.name}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <Button size="sm" variant="secondary" className="px-2">
                                <Pencil className="h-4 w-4 mr-1" />
                                Редактировать
                              </Button>
                            </div>
                          </div>
                          <div className="p-3">
                            <p className="font-medium text-sm truncate">{item.name}</p>
                            <p className="text-xs text-muted-foreground">{item.category}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="tops">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                      {mockItems.filter(item => item.category === 'Верх').map(item => (
                        <div 
                          key={item.id}
                          className="border rounded-xl overflow-hidden bg-background group hover:border-primary cursor-pointer transition-colors"
                        >
                          <div className="h-40 relative">
                            <img 
                              src={item.imageUrl}
                              alt={item.name}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <Button size="sm" variant="secondary" className="px-2">
                                <Pencil className="h-4 w-4 mr-1" />
                                Редактировать
                              </Button>
                            </div>
                          </div>
                          <div className="p-3">
                            <p className="font-medium text-sm truncate">{item.name}</p>
                            <p className="text-xs text-muted-foreground">{item.category}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                  
                  {/* Остальные категории имеют аналогичную структуру */}
                </Tabs>
                
                <div className="pt-8 border-t">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold">Мои комплекты</h3>
                    <Button size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Создать комплект
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Повседневный образ</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex gap-3 items-start">
                          <img 
                            src={mockItems[0].imageUrl} 
                            alt="Item" 
                            className="w-16 h-16 object-cover rounded" 
                          />
                          <img 
                            src={mockItems[1].imageUrl} 
                            alt="Item" 
                            className="w-16 h-16 object-cover rounded" 
                          />
                          <img 
                            src={mockItems[3].imageUrl} 
                            alt="Item" 
                            className="w-16 h-16 object-cover rounded" 
                          />
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Офисный стиль</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex gap-3 items-start">
                          <img 
                            src={mockItems[0].imageUrl} 
                            alt="Item" 
                            className="w-16 h-16 object-cover rounded" 
                          />
                          <img 
                            src={mockItems[1].imageUrl} 
                            alt="Item" 
                            className="w-16 h-16 object-cover rounded" 
                          />
                          <img 
                            src={mockItems[2].imageUrl} 
                            alt="Item" 
                            className="w-16 h-16 object-cover rounded" 
                          />
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="recommendations">
          <Card>
            <CardHeader>
              <CardTitle>Персональные рекомендации</CardTitle>
              <CardDescription>
                Основаны на вашем стиле и предпочтениях
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Дополните свой гардероб</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {mockItems.slice(0, 4).map(item => (
                      <ProductCard key={item.id} product={item} />
                    ))}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-4">Тренды этого сезона</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {mockItems.slice(0, 4).map(item => (
                      <ProductCard key={item.id} product={item} />
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default StylistAssistant; 