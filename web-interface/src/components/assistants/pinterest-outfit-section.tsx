import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link as LinkIcon, ExternalLink } from 'lucide-react';
import { ProductCard } from './product-card';

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

// Интерфейс для товара Wildberries
interface WildberriesProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  oldPrice?: number;
  imageUrl: string;
  imageUrls?: string[];
  category: string;
  url?: string;
  gender?: string;
}

interface PinterestOutfitSectionProps {
  outfit: PinterestOutfit;
  isLoading: boolean;
}

const PinterestOutfitSection: React.FC<PinterestOutfitSectionProps> = ({ outfit, isLoading }) => {
  const [productsByClothingItem, setProductsByClothingItem] = useState<Record<string, WildberriesProduct[]>>({});
  const [loadingItems, setLoadingItems] = useState<Record<string, boolean>>({});
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  // Функция для поиска товаров по конкретному предмету одежды
  const searchProductsForClothingItem = async (item: ClothingItem, itemIndex: number) => {
    // Создаем уникальный ключ для этого предмета
    const itemKey = `${itemIndex}-${item.type}`;
    
    // Устанавливаем статус загрузки
    setLoadingItems(prev => ({ ...prev, [itemKey]: true }));
    
    try {
      // Формируем поисковый запрос
      const searchQuery = `${item.color} ${item.type} ${item.description}`.trim();
      
      // Формируем URL с учетом пола
      let url = `/api/search-products?query=${encodeURIComponent(searchQuery)}&limit=3`;
      
      // Если указан пол, добавляем его в запрос
      if (item.gender) {
        url += `&gender=${encodeURIComponent(item.gender)}`;
      }
      
      console.log(`Поиск товаров: ${searchQuery}, пол: ${item.gender}`);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Ошибка при поиске товаров: ${response.statusText}`);
      }
      
      const products = await response.json();
      
      // Сохраняем результаты поиска для этого предмета
      setProductsByClothingItem(prev => ({ 
        ...prev, 
        [itemKey]: products 
      }));
      
      // Устанавливаем, что этот элемент раскрыт
      setExpandedItems(prev => ({ ...prev, [itemKey]: true }));
    } catch (error) {
      console.error('Ошибка при поиске товаров:', error);
    } finally {
      // Сбрасываем статус загрузки
      setLoadingItems(prev => ({ ...prev, [itemKey]: false }));
    }
  };

  // Функция для переключения состояния развернутости элемента
  const toggleItemExpanded = (itemKey: string) => {
    setExpandedItems(prev => ({ 
      ...prev, 
      [itemKey]: !prev[itemKey] 
    }));
  };

  return (
    <Card className="mb-8 border-primary/20">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Изображение и описание из Pinterest */}
          <div className="p-6 bg-muted/30">
            <div className="aspect-[3/4] relative overflow-hidden rounded-lg mb-4">
              <img 
                src={outfit.imageUrl} 
                alt="Pinterest Outfit" 
                className="w-full h-full object-cover"
              />
            </div>
            <h3 className="font-semibold text-lg mb-2">{outfit.description}</h3>
            <a 
              href={outfit.sourceUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center text-sm text-primary hover:underline"
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Посмотреть на Pinterest
            </a>
          </div>

          {/* Список элементов одежды и соответствующих товаров */}
          <div className="col-span-1 md:col-span-2 p-6">
            <h3 className="font-semibold text-xl mb-4">Элементы образа</h3>
            
            <div className="space-y-6">
              {outfit.clothingItems.map((item, index) => {
                const itemKey = `${index}-${item.type}`;
                const products = productsByClothingItem[itemKey] || [];
                const isLoading = loadingItems[itemKey] || false;
                const isExpanded = expandedItems[itemKey] || false;
                
                return (
                  <div key={itemKey} className="pb-4 border-b border-border/50 last:border-0">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">
                        {item.color} {item.type} {item.description}
                      </h4>
                      
                      {products.length > 0 ? (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => toggleItemExpanded(itemKey)}
                        >
                          {isExpanded ? 'Скрыть' : 'Показать товары'}
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => searchProductsForClothingItem(item, index)}
                          disabled={isLoading}
                        >
                          {isLoading ? 'Поиск...' : 'Найти похожие'}
                        </Button>
                      )}
                    </div>
                    
                    {/* Отображаем найденные товары, если они есть и секция развернута */}
                    {isExpanded && products.length > 0 && (
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                        {products.map(product => (
                          <ProductCard key={product.id} product={product} />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PinterestOutfitSection; 