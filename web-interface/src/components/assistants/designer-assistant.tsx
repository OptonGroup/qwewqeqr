"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, Search, RefreshCw, ShoppingBag, ArrowRight, Sofa, Bed, UtensilsCrossed, Briefcase, Gamepad2, Printer, UserSquare, Home } from 'lucide-react';
import { useAppContext } from '@/context/app-context';

interface FurnitureItem {
  id: string;
  name: string;
  description: string;
  price: number;
  imageUrl: string;
  category: string;
  dimensions: {
    width: number;
    height: number;
    depth: number;
  };
  style: string;
  colors: string[];
  materials: string[];
}

const mockItems: FurnitureItem[] = [
  {
    id: '1',
    name: 'Диван модульный',
    description: 'Современный модульный диван с возможностью трансформации',
    price: 89990,
    imageUrl: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=500&auto=format',
    category: 'Диваны',
    dimensions: {
      width: 280,
      height: 85,
      depth: 95
    },
    style: 'Современный',
    colors: ['Серый', 'Бежевый'],
    materials: ['Ткань', 'Дерево']
  },
  {
    id: '2',
    name: 'Кресло акцентное',
    description: 'Стильное кресло с высокой спинкой',
    price: 34990,
    imageUrl: 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=500&auto=format',
    category: 'Кресла',
    dimensions: {
      width: 75,
      height: 100,
      depth: 85
    },
    style: 'Скандинавский',
    colors: ['Зеленый', 'Синий'],
    materials: ['Велюр', 'Металл']
  },
  {
    id: '3',
    name: 'Стол обеденный',
    description: 'Обеденный стол из массива дуба',
    price: 45990,
    imageUrl: 'https://images.unsplash.com/photo-1577140917170-285929fb55b7?w=500&auto=format',
    category: 'Столы',
    dimensions: {
      width: 160,
      height: 75,
      depth: 90
    },
    style: 'Лофт',
    colors: ['Натуральный'],
    materials: ['Дуб', 'Металл']
  },
  {
    id: '4',
    name: 'Светильник подвесной',
    description: 'Дизайнерский подвесной светильник',
    price: 12990,
    imageUrl: 'https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=500&auto=format',
    category: 'Освещение',
    dimensions: {
      width: 40,
      height: 120,
      depth: 40
    },
    style: 'Современный',
    colors: ['Черный', 'Золотой'],
    materials: ['Металл', 'Стекло']
  }
];

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
    hasChildren: false,
    hasPets: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<FurnitureItem[]>([]);
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
    }
  };
  
  const handleNextStep = () => {
    setCurrentStep(currentStep + 1);
  };
  
  const handlePrevStep = () => {
    setCurrentStep(currentStep - 1);
  };
  
  const handleGetRecommendations = async () => {
    setIsLoading(true);
    
    // В реальном приложении здесь был бы запрос к API
    // Для примера используем моковые данные
    setTimeout(() => {
      setRecommendations(mockItems);
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
              <Tabs defaultValue="furniture" className="w-full">
                <div className="px-6 pb-6">
                  <TabsList className="w-full mb-6">
                    <TabsTrigger value="furniture">Мебель</TabsTrigger>
                    <TabsTrigger value="design">Дизайн-концепция</TabsTrigger>
                    <TabsTrigger value="layout">Планировка</TabsTrigger>
                  </TabsList>
                </div>
                
                <TabsContent value="furniture" className="px-6 pb-6 pt-0">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {recommendations.map(item => (
                      <Card key={item.id} className="overflow-hidden p-0">
                        <div className="relative h-56">
                          <img 
                            src={item.imageUrl} 
                            alt={item.name} 
                            className="w-full h-full object-cover"
                          />
                          {item.style && (
                            <div className="absolute top-3 right-3 bg-black/70 text-white px-2 py-1 rounded-full text-xs">
                              {getStyleName(selectedStyle || '')}
                            </div>
                          )}
                        </div>
                        <CardContent className="p-5">
                          <h3 className="font-semibold text-base mb-1">{item.name}</h3>
                          <p className="text-sm text-muted-foreground mb-3">{item.description}</p>
                          <div className="flex flex-wrap gap-2 mb-4">
                            {item.materials.map((material, index) => (
                              <span key={index} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                                {material}
                              </span>
                            ))}
                          </div>
                          <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
                            <div className="p-2 bg-primary/5 rounded">
                              <span className="font-medium block">Размеры:</span> 
                              {item.dimensions.width}×{item.dimensions.depth}×{item.dimensions.height} см
                            </div>
                            <div className="p-2 bg-primary/5 rounded">
                              <span className="font-medium block">Цвета:</span> 
                              {item.colors.join(', ')}
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="font-bold">{item.price} ₽</span>
                            <Button size="sm" variant="outline">
                              <ShoppingBag className="h-4 w-4 mr-2" />
                              Добавить
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>
                
                <TabsContent value="design" className="px-6 pb-6 pt-0">
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6 border rounded-xl bg-primary/5">
                        <h3 className="font-semibold text-lg mb-4">Цветовая палитра</h3>
                        <div className="flex space-x-4 mb-5">
                          <div className="color-sample bg-[#e8e4d9]"></div>
                          <div className="color-sample bg-[#b6c8b2]"></div>
                          <div className="color-sample bg-[#8a9b8e]"></div>
                          <div className="color-sample bg-[#555a56]"></div>
                          <div className="color-sample bg-[#91785c]"></div>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Палитра подобрана с учетом выбранного стиля и типа помещения. 
                          Нейтральные тона создают спокойную атмосферу и расширяют пространство.
                        </p>
                      </div>
                      
                      <div className="p-6 border rounded-xl bg-primary/5">
                        <h3 className="font-semibold text-lg mb-4">Материалы и текстуры</h3>
                        <div className="grid grid-cols-3 gap-4 mb-5">
                          <div className="texture-sample bg-[url('https://images.unsplash.com/photo-1583248483201-e9d3e613c9bc?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')]"></div>
                          <div className="texture-sample bg-[url('https://images.unsplash.com/photo-1606644403560-3c8c561035ad?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')]"></div>
                          <div className="texture-sample bg-[url('https://images.unsplash.com/photo-1604074130793-efb74419fde7?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')]"></div>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Сочетание различных текстур добавляет интерьеру глубину и характер.
                          Рекомендуем использовать натуральное дерево, мрамор и текстиль.
                        </p>
                      </div>
                    </div>
                    
                    <div className="border rounded-xl p-6">
                      <h3 className="font-semibold text-lg mb-4">Основные принципы дизайна</h3>
                      <div className="space-y-5">
                        <div>
                          <h4 className="text-base font-medium mb-2">Освещение</h4>
                          <p className="text-sm text-muted-foreground">
                            Используйте многоуровневое освещение: основной свет (люстра), рабочее освещение 
                            (настольные лампы) и акцентное освещение (споты, бра). Рекомендуем теплый 
                            свет (2700-3000К) для создания уютной атмосферы.
                          </p>
                        </div>
                        
                        <div>
                          <h4 className="text-base font-medium mb-2">Пропорции и масштаб</h4>
                          <p className="text-sm text-muted-foreground">
                            Учитывайте размер помещения при выборе мебели. Для площади {roomInfo.area}м² 
                            рекомендуем выбирать предметы с общей площадью основания не более {Math.round(Number(roomInfo.area) * 0.4)}м², 
                            чтобы сохранить свободное пространство и проходы.
                          </p>
                        </div>
                        
                        <div>
                          <h4 className="text-base font-medium mb-2">Акценты и фокусные точки</h4>
                          <p className="text-sm text-muted-foreground">
                            Создайте 1-2 ярких акцента в интерьере: это может быть выразительный предмет мебели, 
                            произведение искусства или декоративный элемент. Остальные предметы должны поддерживать
                            общую композицию, не конкурируя за внимание.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="layout" className="px-6 pb-6 pt-0">
                  <div className="space-y-6">
                    <div className="border rounded-xl p-6">
                      <h3 className="font-semibold text-lg mb-4">План размещения мебели</h3>
                      
                      <div className="aspect-video bg-muted rounded-lg flex items-center justify-center mb-6">
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
                      </div>
                      
                      <div className="space-y-4">
                        <h4 className="text-base font-medium mb-2">Рекомендации по расстановке</h4>
                        <div className="space-y-4 text-sm text-muted-foreground">
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