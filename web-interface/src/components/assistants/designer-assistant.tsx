"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, Search, RefreshCw, ShoppingBag, ArrowRight, Sofa, Bed, UtensilsCrossed, Briefcase, Gamepad2, Printer, UserSquare, Home, ExternalLink, AlertCircle } from 'lucide-react';
import { useAppContext } from '@/context/app-context';
import { designerApi } from '@/lib/api';

// Интерфейс для элемента мебели
interface FurnitureItem {
  id: string;
  name: string;
  description: string;
  price: number;
  imageUrl: string;
  category: string;
  dimensions?: {
    width: number;
    height: number;
    depth: number;
  };
  style?: string;
  colors?: string[];
  materials?: string[];
  productUrl?: string;
  brand?: string;
}

// Интерфейс для анализа дизайна
interface DesignAnalysis {
  roomType: string;
  style: string;
  colorPalette: string[];
  recommendedMaterials: string[];
  designPrinciples: {
    title: string;
    description: string;
  }[];
  area: number;
  identifiedNeeds: any;
}

// Интерфейс для текстовой рекомендации
interface TextRecommendation {
  title: string;
  description: string;
}

// Интерфейс для дизайн-концепции
interface DesignConcept {
  mainIdea: string;
  styleDescription: string;
  moodBoard: string[];
  keyElements: {
    name: string;
    description: string;
  }[];
}

// Интерфейс для планировки помещения
interface FloorPlan {
  dimensions: {
    width: number;
    length: number;
    area: number;
  };
  zoning: {
    name: string;
    area: number;
    position: string;
  }[];
  furnitureLayout: {
    name: string;
    position: string;
    dimensions: string;
  }[];
  recommendations: string[];
}

// Интерфейс для данных API
interface DesignerApiResponse {
  success: boolean;
  designAnalysis?: DesignAnalysis;
  textRecommendations?: TextRecommendation[];
  designConcept?: DesignConcept;
  floorPlan?: FloorPlan;
  error?: string;
}

// Интерфейс для цветовой палитры
interface ColorPaletteResponse {
  success: boolean;
  style: string;
  colorPalette: string[];
  error?: string;
}

const roomTypes = [
  { id: 'living', name: 'Гостиная' },
  { id: 'bedroom', name: 'Спальня' },
  { id: 'kitchen', name: 'Кухня' },
  { id: 'office', name: 'Домашний офис' },
  { id: 'children', name: 'Детская' }
];

const styles = [
  { id: 'modern', name: 'Современный' },
  { id: 'scandinavian', name: 'Скандинавский' },
  { id: 'loft', name: 'Лофт' },
  { id: 'classic', name: 'Классический' },
  { id: 'minimalist', name: 'Минимализм' }
];

interface DesignerAssistantProps {
  onReturnHome?: () => void;
}

const DesignerAssistant: React.FC<DesignerAssistantProps> = ({ onReturnHome }) => {
  const { setSelectedRole } = useAppContext();
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);
  const [roomImage, setRoomImage] = useState<File | null>(null);
  const [roomImageUrl, setRoomImageUrl] = useState<string | null>(null);
  const [roomInfo, setRoomInfo] = useState({
    area: '',
    budget: '',
    hasWindows: '',
    hasImage: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [designAnalysis, setDesignAnalysis] = useState<DesignAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<FurnitureItem[]>([]);
  const [categorizedProducts, setCategorizedProducts] = useState<Record<string, FurnitureItem[]>>({});
  const [colorPalette, setColorPalette] = useState<string[]>([]);
  const [textRecommendations, setTextRecommendations] = useState<TextRecommendation[]>([]);
  const [designConcept, setDesignConcept] = useState<DesignConcept | null>(null);
  const [floorPlan, setFloorPlan] = useState<FloorPlan | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  
  const handleRoomSelect = (room: string) => {
    setSelectedRoom(room);
  };
  
  const handleStyleSelect = (style: string) => {
    setSelectedStyle(style);
  };
  
  const handleRoomInfoChange = (field: string, value: string | boolean) => {
    setRoomInfo(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setRoomImage(file);
      const url = URL.createObjectURL(file);
      setRoomImageUrl(url);
      handleRoomInfoChange('hasImage', true);
    }
  };
  
  const handleNextStep = () => {
    setCurrentStep(currentStep + 1);
  };
  
  const handlePrevStep = () => {
    setCurrentStep(currentStep - 1);
  };
  
  const handleGetRecommendations = async () => {
    if (!selectedRoom || !selectedStyle) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Получаем анализ дизайна и рекомендации
      const analysisResponse: DesignerApiResponse = await designerApi.analyze({
        roomType: selectedRoom,
        style: selectedStyle,
        roomInfo: {
          area: roomInfo.area ? parseFloat(roomInfo.area) : undefined,
          budget: roomInfo.budget ? parseFloat(roomInfo.budget) : undefined,
          hasWindows: roomInfo.hasWindows,
          hasImage: roomInfo.hasImage
        }
      });
      
      if (analysisResponse.success) {
        if (analysisResponse.designAnalysis) {
          setDesignAnalysis(analysisResponse.designAnalysis);
          setColorPalette(analysisResponse.designAnalysis.colorPalette);
        }
        
        if (analysisResponse.textRecommendations) {
          setTextRecommendations(analysisResponse.textRecommendations);
        }
        
        if (analysisResponse.designConcept) {
          setDesignConcept(analysisResponse.designConcept);
        }
        
        if (analysisResponse.floorPlan) {
          setFloorPlan(analysisResponse.floorPlan);
        }
        
        setCurrentStep(4);
      } else {
        setError(analysisResponse.error || 'Не удалось получить рекомендации. Пожалуйста, попробуйте еще раз.');
      }
    } catch (error) {
      console.error('Ошибка при получении рекомендаций:', error);
      setError('Произошла ошибка при получении рекомендаций. Пожалуйста, попробуйте еще раз.');
    } finally {
      setIsLoading(false);
    }
  };

  // Если API недоступно, используем моковые данные
  const handleGetRecommendationsFallback = () => {
    setIsLoading(true);
    setError(null);
    
    setTimeout(() => {
      // Моковые текстовые рекомендации
      const mockTextRecommendations: TextRecommendation[] = [
        {
          title: "ПЕРЕДВИНУТЬ",
          description: "• Расположите диван напротив фокусной точки комнаты (телевизор, камин или окно).\n• Создайте зону для общения, сгруппировав кресла и журнальный столик.\n• Разместите книжный шкаф у стены, не загораживая проход.\n• В стиле Современный желательно избегать загромождения центра комнаты."
        },
        {
          title: "ДОКУПИТЬ",
          description: "• Основная мебель (диван, кресла, журнальный столик): 30000 руб.\n• Системы хранения (шкафы, полки): 7500 руб.\n• Освещение (торшер, настольные лампы): 5000 руб.\n• Декор (ковер, подушки, картины): 7500 руб.\n\nРекомендуемые покупки для стиля Современный: \n• Диван с четкими линиями и хромированными ножками\n• Журнальный столик со стеклянной столешницей\n• Минималистичные светильники с металлическими элементами"
        },
        {
          title: "ЗАМЕНИТЬ/УБРАТЬ",
          description: "• Замените устаревшую мебель с резными элементами на модели с четкими линиями.\n• Уберите массивные тяжелые шторы в пользу легких роллет или жалюзи.\n• Избавьтесь от обилия мелких статуэток и сувениров.\n• Замените старые люстры на современные светильники с лаконичным дизайном."
        },
        {
          title: "ОБЩЕЕ",
          description: "• Для помещения площадью 18 м² выбирайте мебель соответствующих размеров, чтобы сохранить простор и функциональность.\n• В комнате с естественным освещением особенно важно не загораживать окна массивной мебелью и использовать светоотражающие поверхности.\n\n• Цветовая палитра для стиля Современный: нейтральные тона (белый, серый, бежевый) с яркими акцентами (синий, зеленый, красный).\n\n• Материалы для стиля Современный: стекло, металл, глянцевые поверхности, пластик."
        }
      ];
      
      setTextRecommendations(mockTextRecommendations);
      
      // Моковые данные для дизайн-анализа
      setDesignAnalysis({
        roomType: getRoomName(selectedRoom || ''),
        style: getStyleName(selectedStyle || ''),
        colorPalette: ['#E8E8E8', '#303030', '#6E7E85', '#A4C2A8', '#D3D5D7'],
        recommendedMaterials: ['Натуральное дерево', 'Текстиль', 'Металл', 'Стекло'],
        designPrinciples: [
          {
            title: 'Пропорции и масштаб',
            description: `Для площади ${roomInfo.area}м² рекомендуем выбирать предметы с общей площадью основания не более ${Math.round(Number(roomInfo.area) * 0.4)}м².`
          },
          {
            title: 'Акценты',
            description: 'Создайте 1-2 ярких акцента, остальные элементы должны быть нейтральными.'
          }
        ],
        area: parseFloat(roomInfo.area),
        identifiedNeeds: {}
      });
      
      // Моковые данные для дизайн-концепции
      setDesignConcept({
        mainIdea: `Светлое, функциональное пространство с акцентом на чистые линии и минимализм. ${getRoomName(selectedRoom || '')} площадью ${roomInfo.area} м² в ${getStyleName(selectedStyle || '')} стиле создает ощущение простора и свободы.`,
        styleDescription: "Современный стиль характеризуется чистыми линиями, нейтральной цветовой гаммой и технологичными материалами. Ключевые элементы: геометрические формы, глянцевые поверхности, стекло, металл и открытые пространства. Акцент на функциональность и эргономику.",
        moodBoard: ["хром", "стекло", "графитовый", "бежевый", "яркие акценты", "глянцевые поверхности"],
        keyElements: [
          {
            name: "Зонирование",
            description: `Разделение пространства ${roomInfo.area} м² на функциональные зоны: отдыха, общения и, возможно, рабочую.`
          },
          {
            name: "Система освещения",
            description: "Многоуровневое освещение: основной верхний свет, направленные светильники и декоративные источники света."
          },
          {
            name: "Акцентная стена", 
            description: `Выделение одной стены в стиле ${getStyleName(selectedStyle || '')} (цветом, текстурой, декором) для создания фокусной точки.`
          }
        ]
      });
      
      // Моковые данные для планировки
      const area = parseFloat(roomInfo.area || '20');
      const width = Math.sqrt(area * 1.5);
      const length = area / width;
      
      setFloorPlan({
        dimensions: {
          width: parseFloat(width.toFixed(1)),
          length: parseFloat(length.toFixed(1)),
          area: area
        },
        zoning: [
          {
            name: "Зона отдыха",
            area: parseFloat((area * 0.6).toFixed(1)),
            position: "центр"
          },
          {
            name: "Зона для общения",
            area: parseFloat((area * 0.3).toFixed(1)),
            position: "у окна"
          },
          {
            name: "Зона хранения",
            area: parseFloat((area * 0.1).toFixed(1)),
            position: "у стены"
          }
        ],
        furnitureLayout: [
          {
            name: "Диван",
            position: "у стены напротив окна",
            dimensions: "2.5 x 0.9 м"
          },
          {
            name: "Журнальный столик",
            position: "перед диваном",
            dimensions: "0.9 x 0.6 м"
          },
          {
            name: "Тумба под ТВ",
            position: "у стены напротив дивана",
            dimensions: "1.5 x 0.5 м"
          },
          {
            name: "Кресло",
            position: "рядом с диваном",
            dimensions: "0.8 x 0.8 м"
          }
        ],
        recommendations: [
          "Расположите диван так, чтобы было удобно смотреть телевизор",
          `В комнате площадью ${area} м² оставляйте минимум 70-80 см для проходов`,
          "Избегайте загромождения центра комнаты мебелью",
          "Используйте многофункциональную мебель для экономии пространства"
        ]
      });
      
      setColorPalette(['#E8E8E8', '#303030', '#6E7E85', '#A4C2A8', '#D3D5D7']);
      
      setCurrentStep(4);
      setIsLoading(false);
    }, 1500);
  };

  const getRoomName = (roomId: string) => {
    const room = roomTypes.find(r => r.id === roomId);
    return room ? room.name : '';
  };

  const getStyleName = (styleId: string) => {
    const style = styles.find(s => s.id === styleId);
    return style ? style.name : '';
  };
  
  const handleBuyProduct = (productUrl?: string) => {
    if (productUrl) {
      window.open(productUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>, item: FurnitureItem) => {
    // Заменяем на изображение-заглушку при ошибке загрузки
    e.currentTarget.src = 'https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?w=500&auto=format';
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Ассистент дизайнера</h1>
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

      <div className="mb-10">
        <div className="flex items-center mb-6">
          {[1, 2, 3, 4].map((step) => (
            <React.Fragment key={step}>
              <div 
                className={`step-indicator ${
                  step === currentStep ? 'bg-primary text-primary-foreground' : 
                  step < currentStep ? 'bg-primary/80 text-primary-foreground' : 'bg-muted text-muted-foreground'
                }`}
              >
                {step}
              </div>
              {step < 4 && (
                <div className={`step-line w-16 ${step < currentStep ? 'bg-primary' : 'bg-muted'}`}></div>
              )}
            </React.Fragment>
          ))}
        </div>
        <div className="text-sm text-muted-foreground/90 font-medium">
          {currentStep === 1 && 'Шаг 1: Выберите тип комнаты'}
          {currentStep === 2 && 'Шаг 2: Выберите стиль интерьера'}
          {currentStep === 3 && 'Шаг 3: Параметры помещения'}
          {currentStep === 4 && 'Шаг 4: Ваши рекомендации'}
        </div>
      </div>

      {/* Отображение ошибки */}
      {error && (
        <div className="bg-destructive/15 text-destructive p-4 rounded-lg mb-6 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-medium mb-1">Ошибка</h3>
            <p className="text-sm">{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setError(null)} 
              className="mt-2"
            >
              Закрыть
            </Button>
          </div>
        </div>
      )}

      {/* Шаг 1: Тип комнаты */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Выберите тип комнаты</CardTitle>
            <CardDescription>
              Этот выбор определит категории мебели и элементы декора
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
              {roomTypes.map((room) => (
                <div 
                  key={room.id}
                  className={`p-5 border rounded-xl cursor-pointer hover:border-primary transition-all ${
                    selectedRoom === room.id ? 'border-primary bg-primary/5 shadow-sm' : 'border-border/60'
                  }`}
                  onClick={() => handleRoomSelect(room.id)}
                >
                  <div className="flex items-center gap-3 mb-2">
                    {room.id === 'living' && <Sofa className="h-5 w-5 text-primary" />}
                    {room.id === 'bedroom' && <Bed className="h-5 w-5 text-primary" />}
                    {room.id === 'kitchen' && <UtensilsCrossed className="h-5 w-5 text-primary" />}
                    {room.id === 'office' && <Briefcase className="h-5 w-5 text-primary" />}
                    {room.id === 'children' && <Gamepad2 className="h-5 w-5 text-primary" />}
                    <h3 className="font-semibold text-lg">{room.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {room.id === 'living' && 'Гостиная, зал, общее пространство для отдыха и приема гостей'}
                    {room.id === 'bedroom' && 'Спальня, комната для сна и отдыха'}
                    {room.id === 'kitchen' && 'Кухня, столовая, обеденная зона'}
                    {room.id === 'office' && 'Рабочий кабинет, домашний офис'}
                    {room.id === 'children' && 'Детская комната, игровая зона'}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end mt-8">
              <Button onClick={handleNextStep} disabled={!selectedRoom} className="px-6">
                Далее <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Шаг 2: Стиль */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Выберите стиль интерьера</CardTitle>
            <CardDescription>
              Стиль определит характер и настроение вашего интерьера
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
              {styles.map((style) => (
                <div 
                  key={style.id}
                  className={`p-5 border rounded-xl cursor-pointer hover:border-primary transition-all ${
                    selectedStyle === style.id ? 'border-primary bg-primary/5 shadow-sm' : 'border-border/60'
                  }`}
                  onClick={() => setSelectedStyle(style.id)}
                >
                  <h3 className="font-semibold text-lg mb-1">{style.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {style.id === 'modern' && 'Четкие линии, минимальный декор, практичность'}
                    {style.id === 'scandinavian' && 'Светлые тона, натуральные материалы, уют'}
                    {style.id === 'loft' && 'Индустриальные детали, грубые фактуры, открытое пространство'}
                    {style.id === 'classic' && 'Элегантность, симметрия, традиционные элементы'}
                    {style.id === 'minimalist' && 'Функциональность, простота, чистые поверхности'}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="flex justify-between mt-8">
              <Button variant="outline" onClick={handlePrevStep}>
                Назад
              </Button>
              <Button onClick={handleNextStep} disabled={!selectedStyle} className="px-6">
                Далее <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Шаг 3: Параметры помещения */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Параметры помещения</CardTitle>
            <CardDescription>
              Укажите характеристики вашей комнаты для точного подбора мебели
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                <div className="space-y-2">
                  <label htmlFor="area" className="text-sm font-medium">
                    Площадь комнаты (м²)
                  </label>
                  <Input
                    id="area"
                    type="number"
                    placeholder="Например, 18"
                    value={roomInfo.area}
                    onChange={(e) => handleRoomInfoChange('area', e.target.value)}
                    className="h-11"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="budget" className="text-sm font-medium">
                    Бюджет (₽)
                  </label>
                  <Input
                    id="budget"
                    type="number"
                    placeholder="Например, 100000"
                    value={roomInfo.budget}
                    onChange={(e) => handleRoomInfoChange('budget', e.target.value)}
                    className="h-11"
                  />
                </div>
                
                <div className="space-y-3">
                  <label className="text-sm font-medium">
                    Наличие окон
                  </label>
                  <div className="flex flex-wrap gap-3">
                    <Button 
                      variant={roomInfo.hasWindows === 'yes' ? 'default' : 'outline'} 
                      size="sm" 
                      onClick={() => handleRoomInfoChange('hasWindows', 'yes')}
                      className="rounded-full"
                    >
                      Есть окна
                    </Button>
                    <Button 
                      variant={roomInfo.hasWindows === 'no' ? 'default' : 'outline'} 
                      size="sm" 
                      onClick={() => handleRoomInfoChange('hasWindows', 'no')}
                      className="rounded-full"
                    >
                      Нет окон
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Фото помещения (необязательно)
                </label>
                <div className="border-2 border-dashed rounded-xl p-8 transition-colors hover:border-primary/50 bg-background">
                  <input
                    type="file"
                    id="room-photo"
                    className="hidden"
                    accept="image/*"
                    onChange={handleFileChange}
                  />
                  <label 
                    htmlFor="room-photo" 
                    className="cursor-pointer flex flex-col items-center justify-center"
                  >
                    {roomImageUrl ? (
                      <div className="w-full">
                        <img 
                          src={roomImageUrl} 
                          alt="Preview" 
                          className="max-h-60 mx-auto rounded-lg object-contain" 
                        />
                        <p className="text-sm text-center mt-4 text-muted-foreground">
                          Нажмите, чтобы заменить изображение
                        </p>
                      </div>
                    ) : (
                      <>
                        <Upload className="h-12 w-12 text-muted-foreground mb-3" />
                        <p className="text-muted-foreground text-center">
                          Перетащите файл или нажмите для загрузки
                          <br />
                          <span className="text-sm">
                            Фото поможет точнее подобрать интерьерные решения
                          </span>
                        </p>
                      </>
                    )}
                  </label>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between mt-8">
              <Button variant="outline" onClick={handlePrevStep}>
                Назад
              </Button>
              <Button 
                onClick={handleGetRecommendations} 
                disabled={isLoading || !roomInfo.area || !roomInfo.budget}
                className="px-6"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Анализ данных...
                  </>
                ) : (
                  'Получить рекомендации'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Шаг 4: Рекомендации */}
      {currentStep === 4 && (
        <div className="space-y-8">
          <Card className="overflow-hidden">
            <CardHeader>
              <CardTitle>Ваш проект интерьера</CardTitle>
              <CardDescription>
                Рекомендации основаны на выбранных характеристиках: {getRoomName(selectedRoom || '')} в стиле {getStyleName(selectedStyle || '')}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Tabs defaultValue="recommendations" className="w-full">
                <div className="px-6 pb-6">
                  <TabsList className="w-full mb-6">
                    <TabsTrigger value="recommendations">Рекомендации</TabsTrigger>
                    <TabsTrigger value="design">Дизайн-концепция</TabsTrigger>
                    <TabsTrigger value="layout">Планировка</TabsTrigger>
                  </TabsList>
                </div>
                
                <TabsContent value="recommendations" className="px-6 pb-6 pt-0">
                  <div className="space-y-6">
                    {textRecommendations.map((recommendation, index) => (
                      <div key={index} className="border rounded-xl p-5 bg-card">
                        <h3 className="font-semibold text-lg mb-2">{recommendation.title}</h3>
                        <p className="text-muted-foreground">{recommendation.description}</p>
                      </div>
                    ))}
                    
                    {textRecommendations.length === 0 && (
                      <div className="text-center p-10 border rounded-xl">
                        <p className="text-muted-foreground">Нет доступных рекомендаций. Попробуйте изменить параметры запроса.</p>
                      </div>
                    )}
                  </div>
                </TabsContent>
                
                <TabsContent value="design" className="px-6 pb-6 pt-0">
                  <div className="space-y-6">
                    <div className="border rounded-xl p-6">
                      <h3 className="font-semibold text-lg mb-4">Основная идея</h3>
                      <p className="text-muted-foreground">
                        {designConcept?.mainIdea || 
                          `Светлое, функциональное пространство для ${getRoomName(selectedRoom || '')} в стиле ${getStyleName(selectedStyle || '')}.`
                        }
                      </p>
                      <div className="mt-4">
                        <h4 className="text-base font-medium mb-2">Описание стиля</h4>
                        <p className="text-sm text-muted-foreground">
                          {designConcept?.styleDescription || 
                            `${getStyleName(selectedStyle || '')} стиль характеризуется гармоничным сочетанием функциональности и эстетики.`
                          }
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6 border rounded-xl bg-primary/5">
                        <h3 className="font-semibold text-lg mb-4">Цветовая палитра</h3>
                        <div className="flex space-x-4 mb-5">
                          {(designAnalysis?.colorPalette || colorPalette).map((color, index) => (
                            <div key={index} className="color-sample" style={{backgroundColor: color}}></div>
                          ))}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Палитра подобрана с учетом выбранного стиля и типа помещения. 
                          {getStyleName(selectedStyle || '') === 'Скандинавский' && 
                            ' Светлые тона создают ощущение пространства и света.'}
                          {getStyleName(selectedStyle || '') === 'Лофт' && 
                            ' Промышленные оттенки подчеркивают характерный для лофта индустриальный стиль.'}
                          {getStyleName(selectedStyle || '') === 'Современный' && 
                            ' Нейтральные тона создают спокойную атмосферу и расширяют пространство.'}
                        </p>
                      </div>
                      
                      <div className="p-6 border rounded-xl bg-primary/5">
                        <h3 className="font-semibold text-lg mb-4">Материалы и текстуры</h3>
                        <p className="text-sm mb-4">
                          Mood Board:
                        </p>
                        <div className="flex flex-wrap gap-2 mb-5">
                          {(designConcept?.moodBoard || []).map((item, index) => (
                            <span key={index} className="inline-block px-3 py-1 bg-background rounded-full text-xs">
                              {item}
                            </span>
                          ))}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Рекомендуемые материалы:
                          <span className="block mt-2">
                            {designAnalysis?.recommendedMaterials?.map((material, index) => (
                              <span key={index} className="inline-block mr-2 mb-2 px-2 py-1 bg-primary/10 rounded-full text-xs">
                                {material}
                              </span>
                            ))}
                          </span>
                        </p>
                      </div>
                    </div>
                    
                    <div className="border rounded-xl p-6">
                      <h3 className="font-semibold text-lg mb-4">Ключевые элементы дизайна</h3>
                      <div className="space-y-5">
                        {designConcept?.keyElements?.map((element, index) => (
                          <div key={index}>
                            <h4 className="text-base font-medium mb-2">{element.name}</h4>
                            <p className="text-sm text-muted-foreground">
                              {element.description}
                            </p>
                          </div>
                        ))}
                        {(!designConcept?.keyElements || designConcept.keyElements.length === 0) && 
                          designAnalysis?.designPrinciples?.map((principle, index) => (
                            <div key={index}>
                              <h4 className="text-base font-medium mb-2">{principle.title}</h4>
                              <p className="text-sm text-muted-foreground">
                                {principle.description}
                              </p>
                            </div>
                          ))
                        }
                      </div>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="layout" className="px-6 pb-6 pt-0">
                  <div className="space-y-6">
                    <div className="border rounded-xl p-6">
                      <div className="flex flex-wrap items-center justify-between mb-4">
                        <h3 className="font-semibold text-lg">План размещения мебели</h3>
                        <div className="text-sm text-muted-foreground">
                          Размеры: {floorPlan?.dimensions.width.toFixed(1) || "0.0"} x {floorPlan?.dimensions.length.toFixed(1) || "0.0"} м 
                          (площадь: {floorPlan?.dimensions.area || roomInfo.area} м²)
                        </div>
                      </div>
                      
                      <div className="aspect-video bg-muted rounded-lg flex items-center justify-center mb-6">
                        {roomImageUrl ? (
                          <img 
                            src={roomImageUrl} 
                            alt="Фото помещения" 
                            className="max-h-full rounded-lg object-contain" 
                          />
                        ) : (
                          <div className="text-center p-8">
                            <UserSquare className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
                            <p className="text-muted-foreground">
                              Здесь будет размещен план помещения с расстановкой мебели
                              <br />
                              <span className="text-sm">
                                Для создания детального плана загрузите фото помещения или укажите точные размеры
                              </span>
                            </p>
                            {!roomImage && (
                              <Button variant="outline" className="mt-4" onClick={() => setCurrentStep(3)}>
                                Загрузить фото
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div className="space-y-4">
                          <h4 className="text-base font-medium mb-2">Зонирование помещения</h4>
                          {floorPlan?.zoning && floorPlan.zoning.length > 0 ? (
                            <div className="space-y-3">
                              {floorPlan.zoning.map((zone, index) => (
                                <div key={index} className="flex items-center justify-between border-b pb-2">
                                  <div className="flex items-center gap-3">
                                    <div className={`w-3 h-3 rounded-full bg-primary opacity-${100 - index * 20}`}></div>
                                    <span>{zone.name}</span>
                                  </div>
                                  <div className="text-sm text-muted-foreground flex gap-3">
                                    <span>{zone.area} м²</span>
                                    <span>{zone.position}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">Зонирование будет доступно после указания точных размеров помещения.</p>
                          )}
                        </div>
                        
                        <div className="space-y-4">
                          <h4 className="text-base font-medium mb-2">Размещение мебели</h4>
                          {floorPlan?.furnitureLayout && floorPlan.furnitureLayout.length > 0 ? (
                            <div className="space-y-3">
                              {floorPlan.furnitureLayout.map((item, index) => (
                                <div key={index} className="flex items-center justify-between border-b pb-2">
                                  <span>{item.name}</span>
                                  <div className="text-sm text-muted-foreground flex gap-3">
                                    <span>{item.position}</span>
                                    <span>{item.dimensions}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">Детальное размещение мебели будет доступно после уточнения параметров помещения.</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <h4 className="text-base font-medium mb-2">Рекомендации по расстановке</h4>
                        <div className="space-y-4 text-sm text-muted-foreground">
                          {floorPlan?.recommendations && floorPlan.recommendations.length > 0 ? (
                            floorPlan.recommendations.map((recommendation, index) => (
                              <div key={index} className="flex gap-3 items-start">
                                <ArrowRight className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                <p>{recommendation}</p>
                              </div>
                            ))
                          ) : (
                            <>
                              <div className="flex gap-3 items-start">
                                <ArrowRight className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                <p>
                                  Расположите диван и кресла вокруг центральной точки (например, журнального столика или камина), 
                                  создавая зону для общения.
                                </p>
                              </div>
                              <div className="flex gap-3 items-start">
                                <ArrowRight className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                <p>
                                  Оставьте проходы шириной не менее 70-80 см между предметами мебели для удобного передвижения по комнате.
                                </p>
                              </div>
                              <div className="flex gap-3 items-start">
                                <ArrowRight className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                <p>
                                  Избегайте размещения мебели прямо у стен - небольшой отступ (10-15 см) создаст более изящную композицию.
                                </p>
                              </div>
                              <div className="flex gap-3 items-start">
                                <ArrowRight className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                <p>
                                  Используйте принцип зонирования, разделив пространство на функциональные зоны: для отдыха, работы, хранения.
                                </p>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
          
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setCurrentStep(3)}>
              Изменить параметры
            </Button>
            <Button className="px-6">
              <Printer className="mr-2 h-4 w-4" />
              Сохранить проект
            </Button>
          </div>
        </div>
      )}
      
      <style jsx global>{`
        .step-indicator {
          width: 2.5rem;
          height: 2.5rem;
          border-radius: 9999px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 500;
        }
        
        .step-line {
          height: 2px;
        }
        
        .color-sample {
          width: 40px;
          height: 40px;
          border-radius: 9999px;
          border: 1px solid rgba(0,0,0,0.1);
        }
        
        .texture-sample {
          aspect-ratio: 1;
          border-radius: 0.5rem;
          background-size: cover;
          background-position: center;
        }
      `}</style>
    </div>
  );
};

export default DesignerAssistant; 