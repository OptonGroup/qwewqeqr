import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link as LinkIcon, ExternalLink, Search, ShoppingBag, ChevronDown, ChevronUp } from 'lucide-react';
import { ProductCard } from './product-card';
import { Badge } from '@/components/ui/badge';

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
  const [imageError, setImageError] = useState<boolean>(false);
  const [showFullAnalysis, setShowFullAnalysis] = useState<boolean>(false);

  // Функция для поиска товаров по конкретному предмету одежды
  const searchProductsForClothingItem = async (item: ClothingItem, itemIndex: number) => {
    // Создаем уникальный ключ для этого предмета
    const itemKey = `${itemIndex}-${item.type}`;
    
    // Устанавливаем статус загрузки
    setLoadingItems(prev => ({ ...prev, [itemKey]: true }));
    
    try {
      // Формируем поисковый запрос с учетом пола
      // Добавляем пол в начало запроса для лучших результатов
      const genderText = 
        item.gender === 'мужской' ? 'мужской' : 
        item.gender === 'женский' ? 'женский' : '';
      
      // Очищаем описание от скобок и лишних символов
      const cleanDescription = (item.description || '')
        .replace(/[()[\]{}]/g, '')
        .replace(/\s+/g, ' ')
        .trim();
      
      // Формируем поисковый запрос с приоритетом на тип и цвет
      const searchQuery = [
        genderText,
        item.type || '',
        item.color || '',
        cleanDescription
      ].filter(Boolean).join(' ').trim();
      
      // Формируем URL с учетом пола
      let url = `/api/search-products?query=${encodeURIComponent(searchQuery)}&limit=3`;
      
      // Если указан пол, добавляем его в запрос для фильтрации на бэкенде
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
  
  // Функция для генерации полного анализа образа
  const generateFullAnalysis = () => {
    if (!outfit.clothingItems || outfit.clothingItems.length === 0) {
      return 'Нет данных для анализа образа.';
    }
    
    // Определяем преобладающий пол в образе
    const genderCounts = outfit.clothingItems.reduce((counts, item) => {
      const gender = item.gender || 'унисекс';
      counts[gender] = (counts[gender] || 0) + 1;
      return counts;
    }, {} as Record<string, number>);
    
    let predominantGender = 'не определен';
    let maxCount = 0;
    
    for (const [gender, count] of Object.entries(genderCounts)) {
      if (count > maxCount) {
        maxCount = count;
        predominantGender = gender;
      }
    }
    
    // Создаем список предметов
    const itemsList = outfit.clothingItems
      .map((item, index) => {
        const genderIcon = item.gender === 'мужской' ? '👨' : item.gender === 'женский' ? '👩' : '🧑';
        return `${index + 1}. ${genderIcon} ${item.color || 'Цвет не указан'} ${item.type || 'предмет'} ${item.description ? `(${item.description})` : ''}`.trim();
      })
      .join('\n');
    
    // Создаем детальное описание каждого предмета
    const detailedItems = outfit.clothingItems
      .map(item => {
        const genderIcon = item.gender === 'мужской' ? '👨' : item.gender === 'женский' ? '👩' : '🧑';
        return `${genderIcon} ${item.type?.toUpperCase() || 'ПРЕДМЕТ'}:
- Цвет: ${item.color || 'не указан'}
- Пол: ${item.gender || 'унисекс'} 
- Описание: ${item.description || 'Нет дополнительной информации'}`
      })
      .join('\n\n');
    
    // Определяем стиль образа на основе ключевых слов
    let style = 'повседневный';
    const items = outfit.clothingItems.map(item => `${item.color} ${item.type} ${item.description || ''}`).join(' ').toLowerCase();
    const description = (outfit.description || '').toLowerCase();
    
    if (items.includes('пиджак') || items.includes('блузка') || items.includes('брюки') || description.includes('офис') || description.includes('делов')) {
      style = 'деловой';
    } else if (items.includes('платье') && (items.includes('вечер') || description.includes('вечер'))) {
      style = 'вечерний';
    } else if (items.includes('спорт') || items.includes('кроссовки') || items.includes('худи') || description.includes('спорт')) {
      style = 'спортивный';
    } else if (items.includes('джинсы') || items.includes('футболка') || items.includes('кеды')) {
      style = 'кэжуал';
    } else if (items.includes('пляж') || items.includes('купальник') || items.includes('шорты') && description.includes('лет')) {
      style = 'пляжный';
    } else if (items.includes('зимн') || items.includes('пуховик') || items.includes('шапка') || items.includes('свитер')) {
      style = 'зимний';
    }
    
    // Формируем общее описание
    const genderText = predominantGender === 'мужской' ? 'мужской' : 
                       predominantGender === 'женский' ? 'женский' : 
                       predominantGender === 'унисекс' ? 'унисекс' : 'не определен';
    
    const generalDescription = `ОБЩЕЕ:
Пол: ${genderText}
Стиль: ${style}
Описание: Образ представляет собой ${style} стиль одежды ${genderText === 'мужской' ? 'для мужчин' : genderText === 'женский' ? 'для женщин' : ''}, ${
      style === 'деловой' ? 'подходящий для офисной или официальной обстановки.' : 
      style === 'вечерний' ? 'идеальный для особых случаев и выходов в свет.' : 
      style === 'спортивный' ? 'удобный для активного образа жизни и занятий спортом.' : 
      style === 'пляжный' ? 'отлично подходящий для отдыха у воды и на пляже.' :
      style === 'зимний' ? 'теплый и комфортный для холодного времени года.' :
      'комфортный для повседневной носки.'
    } ${outfit.description || ''}`;
    
    // Собираем полный анализ
    return `${generalDescription}\n\nСписок предметов:\n${itemsList}\n\nДетали предметов:\n${detailedItems}`;
  };

  return (
    <Card className="mb-8 border-primary/20">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Изображение и описание из Pinterest */}
          <div className="p-6 bg-muted/30">
            <div className="aspect-[3/4] relative overflow-hidden rounded-lg mb-4">
              {!imageError ? (
                <img 
                  src={outfit.imageUrl} 
                  alt="Pinterest Outfit" 
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    // Если изображение не загрузилось, заменяем на стандартную заглушку
                    setImageError(true);
                    (e.target as HTMLImageElement).src = 'https://placehold.co/600x800/e2e8f0/64748b?text=Изображение+недоступно';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-muted/40">
                  <p className="text-muted-foreground text-sm text-center px-4">
                    Изображение недоступно
                  </p>
                </div>
              )}
              
              {/* Отметки предметов одежды на фото */}
              {outfit.clothingItems && outfit.clothingItems.length > 0 && (
                <div className="absolute bottom-2 right-2 bg-black/70 p-2 rounded-md max-w-[90%] text-white">
                  <p className="text-xs mb-1">Найденная одежда:</p>
                  <div className="flex flex-wrap gap-1">
                    {outfit.clothingItems.map((item, idx) => (
                      <Badge key={idx} variant="outline" className="bg-primary/20 text-white border-primary/50 text-xs">
                        {item.color || ''} {item.type || ''}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <h3 className="font-semibold text-lg mb-2">{outfit.description || 'Стильный образ'}</h3>
            {outfit.sourceUrl && (
              <a 
                href={outfit.sourceUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center text-sm text-primary hover:underline"
              >
                <ExternalLink className="h-4 w-4 mr-1" />
                Посмотреть на Pinterest
              </a>
            )}
            
            {/* Анализ изображения - новая секция */}
            {outfit.clothingItems && outfit.clothingItems.length > 0 && (
              <div className="mt-4 bg-muted/30 rounded-lg p-4 border border-border/40">
                <h4 className="font-medium text-sm">Анализ изображения:</h4>
                <div className="mt-2">
                  <div className="mb-2">
                    <p className="text-xs text-muted-foreground mb-1">Алгоритм определил следующие предметы одежды:</p>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {outfit.clothingItems.slice(0, 3).map((item, idx) => (
                        <Badge 
                          key={idx} 
                          variant="outline" 
                          className={`${
                            item.gender === 'мужской' 
                              ? 'bg-blue-50 text-blue-700 border-blue-200' 
                              : item.gender === 'женский' 
                                ? 'bg-pink-50 text-pink-700 border-pink-200' 
                                : 'bg-primary/10'
                          }`}
                        >
                          {item.type || 'Предмет'}: {item.color || ''} {item.description ? `(${item.description})` : ''}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full text-xs flex items-center justify-center gap-1"
                    onClick={() => setShowFullAnalysis(!showFullAnalysis)}
                  >
                    {showFullAnalysis ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    {showFullAnalysis ? "Скрыть полный анализ" : "Показать полный анализ"}
                  </Button>
                  
                  {showFullAnalysis && (
                    <div className="mt-2 text-xs text-muted-foreground p-2 bg-background/50 rounded border border-border/30 whitespace-pre-line">
                      {generateFullAnalysis()}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Список элементов одежды и соответствующих товаров */}
          <div className="col-span-1 md:col-span-2 p-6">
            <h3 className="font-semibold text-xl mb-4">Элементы образа</h3>
            
            {outfit.clothingItems && outfit.clothingItems.length > 0 ? (
              <div className="space-y-6">
                {outfit.clothingItems.map((item, index) => {
                  const itemKey = `${index}-${item.type}`;
                  const products = productsByClothingItem[itemKey] || [];
                  const isLoading = loadingItems[itemKey] || false;
                  const isExpanded = expandedItems[itemKey] || false;
                  
                  return (
                    <div key={itemKey} className="pb-4 border-b border-border/50 last:border-0">
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium flex items-center">
                            <Badge variant="outline" className="mr-2 bg-primary/10">
                              {item.gender === 'мужской' ? 'М' : item.gender === 'женский' ? 'Ж' : 'У'}
                            </Badge>
                            {item.color || ''} {item.type || ''} {item.description ? ` ${item.description}` : ''}
                          </h4>
                        </div>
                        
                        <div className="flex gap-2">
                          {products.length > 0 ? (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => toggleItemExpanded(itemKey)}
                              className="text-xs"
                            >
                              {isExpanded ? 'Скрыть' : 'Показать похожие'}
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => searchProductsForClothingItem(item, index)}
                              disabled={isLoading}
                              className="flex items-center gap-1 text-xs"
                            >
                              {isLoading ? (
                                <>
                                  <div className="animate-spin w-3 h-3 border-2 border-primary border-t-transparent rounded-full" />
                                  Поиск...
                                </>
                              ) : (
                                <>
                                  <Search className="h-3 w-3" />
                                  Найти на WB
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                      
                      {/* Отображаем найденные товары, если они есть и секция развернута */}
                      {isExpanded && products.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                          {products.map(product => (
                            <ProductCard 
                              key={product.id} 
                              item={{
                                id: product.id,
                                name: product.name,
                                description: product.description,
                                price: product.price,
                                oldPrice: product.oldPrice,
                                imageUrl: product.imageUrl,
                                category: product.category,
                                url: product.url || `https://www.wildberries.ru/catalog/${product.id}/detail.aspx`,
                                gender: product.gender
                              }} 
                            />
                          ))}
                        </div>
                      )}

                      {/* Показываем альтернативную кнопку, если товары уже найдены, но скрыты */}
                      {!isExpanded && products.length > 0 && (
                        <div className="mt-2">
                          <Button
                            variant="default"
                            size="sm"
                            className="w-full text-xs"
                            onClick={() => toggleItemExpanded(itemKey)}
                          >
                            <ShoppingBag className="h-3 w-3 mr-1" />
                            Показать похожие товары ({products.length})
                          </Button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <p>Нет данных о предметах одежды в этом образе.</p>
                <p className="mt-2">Попробуйте выполнить новый поиск или выбрать другой образ.</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PinterestOutfitSection; 