"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, ShoppingBag, ArrowRight, Home } from 'lucide-react';
import { useAppContext } from '@/context/app-context';
import { cosmetologistApi } from '@/lib/api';

interface CosmeticProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  salePrice?: number;  // Цена со скидкой
  discount?: number;   // Процент скидки
  imageUrl: string;
  category: string;
  benefits: string[];
  url?: string;
}

interface SkinAnalysis {
  description: string;
  daily: {
    morning: { steps: Array<{ name: string; product: string }> };
    evening: { steps: Array<{ name: string; product: string }> };
  };
  weekly: {
    procedures: Array<{ name: string; product: string; frequency: string }>;
    additional: Array<{ name: string; description: string }>;
  };
  recommendations: {
    lifestyle: Array<{ text: string }>;
    ingredients: Array<{ name: string; purpose: string }>;
  };
}

const mockProducts: CosmeticProduct[] = [
  {
    id: '1',
    name: 'Увлажняющий крем для лица',
    description: 'Интенсивное увлажнение для сухой и чувствительной кожи',
    price: 1290,
    salePrice: 990,
    discount: 23,
    imageUrl: 'https://images.unsplash.com/photo-1570194065650-d99fb4ee2063?w=500&auto=format',
    category: 'Уход за лицом',
    benefits: ['Увлажнение', 'Питание', 'Защита'],
    url: 'https://www.wildberries.ru/catalog/1/detail.aspx'
  },
  {
    id: '2',
    name: 'Сыворотка с гиалуроновой кислотой',
    description: 'Интенсивное увлажнение и разглаживание мелких морщин',
    price: 1890,
    salePrice: 1299,
    discount: 31,
    imageUrl: 'https://images.unsplash.com/photo-1556229174-5e42a09e36c5?w=500&auto=format',
    category: 'Уход за лицом',
    benefits: ['Увлажнение', 'Антивозрастной эффект', 'Выравнивание тона'],
    url: 'https://www.wildberries.ru/catalog/2/detail.aspx'
  },
  {
    id: '3',
    name: 'Очищающий гель для умывания',
    description: 'Бережное очищение для всех типов кожи',
    price: 790,
    salePrice: 590,
    discount: 25,
    imageUrl: 'https://images.unsplash.com/photo-1610705267928-1b9f2fa7f1c5?w=500&auto=format',
    category: 'Очищение',
    benefits: ['Очищение', 'Тонизирование', 'Мягкое воздействие'],
    url: 'https://www.wildberries.ru/catalog/3/detail.aspx'
  },
  {
    id: '4',
    name: 'Ночная восстанавливающая маска',
    description: 'Интенсивное восстановление кожи во время сна',
    price: 1490,
    salePrice: 1190,
    discount: 20,
    imageUrl: 'https://images.unsplash.com/photo-1599305090598-fe179d501227?w=500&auto=format',
    category: 'Маски',
    benefits: ['Восстановление', 'Питание', 'Регенерация'],
    url: 'https://www.wildberries.ru/catalog/4/detail.aspx'
  }
];

const skinTypes = [
  { id: 'normal', name: 'Нормальная' },
  { id: 'dry', name: 'Сухая' },
  { id: 'oily', name: 'Жирная' },
  { id: 'combination', name: 'Комбинированная' },
  { id: 'sensitive', name: 'Чувствительная' }
];

const skinConcerns = [
  { id: 'aging', name: 'Возрастные изменения' },
  { id: 'acne', name: 'Акне/Высыпания' },
  { id: 'pigmentation', name: 'Пигментация' },
  { id: 'redness', name: 'Покраснения' },
  { id: 'dryness', name: 'Сухость' },
  { id: 'oiliness', name: 'Жирность' }
];

interface CosmetologistAssistantProps {
  onReturnHome?: () => void;
}

const CosmetologistAssistant: React.FC<CosmetologistAssistantProps> = ({ onReturnHome }) => {
  const { setSelectedRole } = useAppContext();
  const [selectedSkinType, setSelectedSkinType] = useState<string | null>(null);
  const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);
  const [age, setAge] = useState<string>('');
  const [selectedLifestyles, setSelectedLifestyles] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<CosmeticProduct[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [currentProducts, setCurrentProducts] = useState<string>('');
  const [allergies, setAllergies] = useState<string>('');
  const [skinAnalysis, setSkinAnalysis] = useState<SkinAnalysis | null>(null);
  
  const handleSkinTypeSelect = (type: string) => {
    setSelectedSkinType(type);
  };
  
  const handleConcernToggle = (concern: string) => {
    if (selectedConcerns.includes(concern)) {
      setSelectedConcerns(selectedConcerns.filter(c => c !== concern));
    } else {
      setSelectedConcerns([...selectedConcerns, concern]);
    }
  };
  
  const handleAgeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAge(e.target.value);
  };
  
  const handleLifestyleToggle = (lifestyle: string) => {
    if (selectedLifestyles.includes(lifestyle)) {
      setSelectedLifestyles(selectedLifestyles.filter(l => l !== lifestyle));
    } else {
      setSelectedLifestyles([...selectedLifestyles, lifestyle]);
    }
  };
  
  const handleCurrentProductsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentProducts(e.target.value);
  };
  
  const handleAllergiesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAllergies(e.target.value);
  };
  
  const handleNextStep = () => {
    setCurrentStep(currentStep + 1);
  };
  
  const handlePrevStep = () => {
    setCurrentStep(currentStep - 1);
  };
  
  const generateSkinAnalysisFromAI = async (userData: any): Promise<SkinAnalysis> => {
    try {
      // В реальном приложении здесь будет запрос к API нейронной сети
      // Возвращаем заглушку для демонстрации
      
      console.log("Sending to neural network:", userData);
      
      // Имитация задержки ответа от сервера
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      let analysisDescription = '';
      if (userData.skinType === 'sensitive') {
        analysisDescription = 'У вас чувствительная кожа, которой необходим бережный уход без агрессивных компонентов.';
      } else if (userData.skinType === 'dry') {
        analysisDescription = 'У вас сухая кожа, которая нуждается в интенсивном увлажнении и питании.';
      } else if (userData.skinType === 'oily') {
        analysisDescription = 'У вас жирная кожа, которой нужно бережное очищение и контроль себорегуляции.';
      } else if (userData.skinType === 'combination') {
        analysisDescription = 'У вас комбинированная кожа, требующая балансирующего ухода.';
      } else {
        analysisDescription = 'У вас нормальная кожа, которой нужно поддерживающий уход и защита.';
      }
      
      if (userData.concerns.includes('acne')) {
        analysisDescription += ' Высыпания указывают на необходимость противовоспалительных компонентов.';
      }
      
      if (userData.concerns.includes('pigmentation')) {
        analysisDescription += ' Пигментация требует средств, выравнивающих тон кожи.';
      }
      
      return {
        description: analysisDescription,
        daily: {
          morning: {
            steps: [
              { name: 'Очищение', product: 'Очищающий гель для умывания' },
              { name: 'Тонизирование', product: 'Увлажняющий тоник без спирта' },
              { name: 'Сыворотка', product: 'Сыворотка с гиалуроновой кислотой' },
              { name: 'Увлажнение', product: 'Увлажняющий крем для лица' },
              { name: 'Защита', product: 'Солнцезащитный крем SPF 30+' }
            ]
          },
          evening: {
            steps: [
              { name: 'Очищение', product: 'Очищающий гель для умывания' },
              { name: 'Тонизирование', product: 'Увлажняющий тоник без спирта' },
              { name: 'Сыворотка', product: 'Ночная восстанавливающая сыворотка' },
              { name: 'Увлажнение', product: 'Ночной питательный крем' },
              { name: 'Крем для глаз', product: 'Увлажняющий крем для области вокруг глаз' }
            ]
          }
        },
        weekly: {
          procedures: [
            { name: 'Эксфолиация', product: 'Мягкий пилинг с AHA-кислотами', frequency: '1-2 раза в неделю' },
            { name: 'Маска', product: 'Увлажняющая тканевая маска', frequency: '1-2 раза в неделю' },
            { name: 'Глубокое очищение', product: 'Очищающая маска с глиной', frequency: '1 раз в неделю' }
          ],
          additional: [
            { name: 'Уход за губами', description: 'Увлажняющий бальзам для губ' },
            { name: 'Уход за руками', description: 'Питательный крем для рук' },
            { name: 'Массаж лица', description: 'Использование нефритового роллера для улучшения микроциркуляции' }
          ]
        },
        recommendations: {
          lifestyle: [
            { text: 'Пить не менее 1,5-2 литров воды в день' },
            { text: 'Защищать кожу от солнца круглый год' },
            { text: 'Избегать горячей воды при умывании' },
            { text: 'Регулярно менять наволочки (минимум раз в неделю)' },
            { text: 'Ограничить потребление сахара и быстрых углеводов' }
          ],
          ingredients: [
            { name: 'Гиалуроновая кислота', purpose: 'для глубокого увлажнения' },
            { name: 'Ниацинамид', purpose: 'для укрепления барьерной функции кожи' },
            { name: 'Пептиды', purpose: 'для стимуляции выработки коллагена' },
            { name: 'Церамиды', purpose: 'для восстановления защитного барьера' },
            { name: 'Антиоксиданты', purpose: 'для защиты от свободных радикалов' }
          ]
        }
      };
    } catch (error) {
      console.error("Error generating skin analysis:", error);
      throw error;
    }
  };
  
  const handleGetRecommendations = async () => {
    setIsLoading(true);
    
    try {
      // Собираем данные пользователя
      const userData = {
        skinType: selectedSkinType,
        concerns: selectedConcerns,
        age: age,
        lifestyles: selectedLifestyles,
        currentProducts: currentProducts,
        allergies: allergies
      };
      
      console.log("Отправляем данные пользователя на сервер:", userData);
      
      // Отправляем запрос к API для получения рекомендаций
      const data = await cosmetologistApi.analyze(userData);
      
      // Устанавливаем полученный анализ кожи
      if (data.skinAnalysis) {
        setSkinAnalysis(data.skinAnalysis);
      } else {
        // Если сервер не вернул анализ кожи, создаем заглушку на основе типа кожи
        const analysis = await generateSkinAnalysisFromAI(userData);
        setSkinAnalysis(analysis);
      }
      
      // Получаем рекомендуемые продукты из ответа API
      if (data.recommendedProducts && data.recommendedProducts.length > 0) {
        // Форматируем данные продуктов, полученных от API
        const formattedProducts = data.recommendedProducts.map(product => ({
          ...product,
          // Добавляем пустой массив benefits, если его нет в данных от API
          benefits: product.benefits || [],
          // Используем поле sale_price или salePrice как скидочную цену, если оно есть
          salePrice: product.salePrice || product.sale_price || null,
          // Убеждаемся, что цена всегда существует
          price: product.price || (product.salePrice || product.sale_price || 0) * (100 / (100 - (product.discount || 0)))
        }));
        setRecommendations(formattedProducts);
      } else {
        // Если сервер не вернул рекомендации, используем моковые данные
        setRecommendations(mockProducts);
      }
      
      setCurrentStep(4);
    } catch (error) {
      console.error("Ошибка при получении рекомендаций:", error);
      alert("Произошла ошибка при получении рекомендаций. Пожалуйста, попробуйте еще раз.");
      
      // В случае ошибки используем локальный метод генерации анализа
      try {
        const analysis = await generateSkinAnalysisFromAI({
          skinType: selectedSkinType,
          concerns: selectedConcerns,
          age: age,
          lifestyles: selectedLifestyles,
          currentProducts: currentProducts,
          allergies: allergies
        });
        setSkinAnalysis(analysis);
        setRecommendations(mockProducts);
        setCurrentStep(4);
      } catch (fallbackError) {
        console.error("Ошибка при локальной генерации анализа:", fallbackError);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Ассистент косметолога</h1>
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
          {currentStep === 1 && 'Шаг 1: Определите тип кожи'}
          {currentStep === 2 && 'Шаг 2: Выберите проблемы кожи'}
          {currentStep === 3 && 'Шаг 3: Дополнительная информация'}
          {currentStep === 4 && 'Шаг 4: Ваши рекомендации'}
        </div>
      </div>
      
      {/* Шаг 1: Тип кожи */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Определите ваш тип кожи</CardTitle>
            <CardDescription>
              Выберите тип, который наиболее соответствует вашей коже
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
              {skinTypes.map((type) => (
                <div 
                  key={type.id}
                  className={`p-5 border rounded-xl cursor-pointer hover:border-primary transition-all ${
                    selectedSkinType === type.id ? 'border-primary bg-primary/5 shadow-sm' : 'border-border/60'
                  }`}
                  onClick={() => handleSkinTypeSelect(type.id)}
                >
                  <h3 className="font-semibold text-lg mb-1">{type.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {type.id === 'normal' && 'Баланс, не склонна к жирности или сухости'}
                    {type.id === 'dry' && 'Склонна к шелушению, ощущение стянутости'}
                    {type.id === 'oily' && 'Избыточное выделение кожного сала, блеск'}
                    {type.id === 'combination' && 'T-зона жирная, щеки нормальные или сухие'}
                    {type.id === 'sensitive' && 'Быстро реагирует на внешние факторы, склонна к покраснениям'}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end mt-8">
              <Button onClick={handleNextStep} disabled={!selectedSkinType} className="px-6">
                Далее <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Шаг 2: Проблемы кожи */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Выберите проблемы кожи</CardTitle>
            <CardDescription>
              Отметьте все, что относится к вашей коже
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
              {skinConcerns.map((concern) => (
                <div 
                  key={concern.id}
                  className={`p-5 border rounded-xl cursor-pointer hover:border-primary transition-all ${
                    selectedConcerns.includes(concern.id) ? 'border-primary bg-primary/5 shadow-sm' : 'border-border/60'
                  }`}
                  onClick={() => handleConcernToggle(concern.id)}
                >
                  <h3 className="font-semibold text-lg mb-1">{concern.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {concern.id === 'aging' && 'Морщины, потеря упругости, тонкая кожа'}
                    {concern.id === 'acne' && 'Высыпания, воспаления, угри'}
                    {concern.id === 'pigmentation' && 'Пятна, неровный тон кожи'}
                    {concern.id === 'redness' && 'Покраснения, раздражения, купероз'}
                    {concern.id === 'dryness' && 'Шелушение, ощущение стянутости'}
                    {concern.id === 'oiliness' && 'Жирный блеск, расширенные поры'}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="flex justify-between mt-8">
              <Button variant="outline" onClick={handlePrevStep}>
                Назад
              </Button>
              <Button onClick={handleNextStep} className="px-6">
                Далее <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Шаг 3: Дополнительная информация */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Дополнительная информация</CardTitle>
            <CardDescription>
              Эти данные помогут подобрать более точные рекомендации
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <label htmlFor="age" className="text-sm font-medium">
                    Возраст
                  </label>
                  <Input
                    id="age"
                    type="number"
                    placeholder="Например: 30"
                    value={age}
                    onChange={handleAgeChange}
                    className="h-11"
                  />
                </div>
                
                <div className="space-y-3">
                  <label className="text-sm font-medium">
                    Образ жизни
                  </label>
                  <div className="flex flex-wrap gap-3">
                    <Button 
                      variant={selectedLifestyles.includes('active') ? "default" : "outline"} 
                      size="sm" 
                      className="rounded-full"
                      onClick={() => handleLifestyleToggle('active')}
                    >
                      Активный
                    </Button>
                    <Button 
                      variant={selectedLifestyles.includes('office') ? "default" : "outline"} 
                      size="sm" 
                      className="rounded-full"
                      onClick={() => handleLifestyleToggle('office')}
                    >
                      Офис
                    </Button>
                    <Button 
                      variant={selectedLifestyles.includes('sport') ? "default" : "outline"} 
                      size="sm" 
                      className="rounded-full"
                      onClick={() => handleLifestyleToggle('sport')}
                    >
                      Спорт
                    </Button>
                    <Button 
                      variant={selectedLifestyles.includes('travel') ? "default" : "outline"} 
                      size="sm" 
                      className="rounded-full"
                      onClick={() => handleLifestyleToggle('travel')}
                    >
                      Путешествия
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Текущие средства ухода (необязательно)
                </label>
                <Input
                  placeholder="Перечислите средства, которыми вы пользуетесь сейчас"
                  className="h-11"
                  value={currentProducts}
                  onChange={handleCurrentProductsChange}
                />
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Ограничения и аллергии (необязательно)
                </label>
                <Input
                  placeholder="Например: аллергия на эфирные масла"
                  className="h-11"
                  value={allergies}
                  onChange={handleAllergiesChange}
                />
              </div>
            </div>
            
            <div className="flex justify-between mt-8">
              <Button variant="outline" onClick={handlePrevStep}>
                Назад
              </Button>
              <Button 
                onClick={handleGetRecommendations} 
                disabled={isLoading}
                className="px-6"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Подбор средств...
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
          <Card>
            <CardHeader>
              <CardTitle>Ваша персональная программа ухода</CardTitle>
              <CardDescription>
                Рекомендации составлены на основе ваших данных
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                <div className="p-6 bg-primary/5 rounded-xl">
                  <h3 className="font-semibold text-lg mb-3">Анализ вашей кожи</h3>
                  <p className="text-sm">
                    {skinAnalysis?.description || 'Анализ не доступен. Пожалуйста, попробуйте еще раз.'}
                  </p>
                  {selectedLifestyles.length > 0 && (
                    <div className="mt-3">
                      <h4 className="font-semibold text-sm mb-1">Ваш образ жизни:</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedLifestyles.includes('active') && (
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">Активный</span>
                        )}
                        {selectedLifestyles.includes('office') && (
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">Офис</span>
                        )}
                        {selectedLifestyles.includes('sport') && (
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">Спорт</span>
                        )}
                        {selectedLifestyles.includes('travel') && (
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">Путешествия</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                <Tabs defaultValue="daily" className="w-full">
                  <TabsList className="mb-6">
                    <TabsTrigger value="daily">Ежедневный уход</TabsTrigger>
                    <TabsTrigger value="weekly">Еженедельный уход</TabsTrigger>
                    <TabsTrigger value="recommendations">Рекомендации</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="daily">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Утренний уход</h3>
                        <ol className="space-y-3 text-sm ml-5 list-decimal">
                          {skinAnalysis?.daily.morning.steps.map((step, idx) => (
                            <li key={idx}>{step.name}: <span className="text-primary font-medium">{step.product}</span></li>
                          ))}
                        </ol>
                      </div>
                      
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Вечерний уход</h3>
                        <ol className="space-y-3 text-sm ml-5 list-decimal">
                          {skinAnalysis?.daily.evening.steps.map((step, idx) => (
                            <li key={idx}>{step.name}: <span className="text-primary font-medium">{step.product}</span></li>
                          ))}
                        </ol>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="weekly">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Еженедельный уход</h3>
                        <ol className="space-y-3 text-sm ml-5 list-decimal">
                          {skinAnalysis?.weekly.procedures.map((procedure, idx) => (
                            <li key={idx}>{procedure.name}: <span className="text-primary font-medium">{procedure.product}</span> ({procedure.frequency})</li>
                          ))}
                        </ol>
                      </div>
                      
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Дополнительный уход</h3>
                        <ul className="space-y-3 text-sm ml-5 list-disc">
                          {skinAnalysis?.weekly.additional.map((item, idx) => (
                            <li key={idx}>{item.name}: <span className="text-primary font-medium">{item.description}</span></li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="recommendations">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Рекомендации по образу жизни</h3>
                        <ul className="space-y-3 text-sm ml-5 list-disc">
                          {skinAnalysis?.recommendations.lifestyle.map((item, idx) => (
                            <li key={idx}>{item.text}</li>
                          ))}
                          {selectedLifestyles.includes('active') && (
                            <li><span className="font-medium">Для активного образа жизни:</span> Используйте легкие некомедогенные средства, которые не будут забивать поры во время активности</li>
                          )}
                          {selectedLifestyles.includes('office') && (
                            <li><span className="font-medium">Для офисного образа жизни:</span> Учитывая длительное пребывание в помещении с кондиционером, используйте увлажняющий спрей в течение дня</li>
                          )}
                          {selectedLifestyles.includes('sport') && (
                            <li><span className="font-medium">Для занятий спортом:</span> Очищайте кожу сразу после тренировки, используйте легкие текстуры средств</li>
                          )}
                          {selectedLifestyles.includes('travel') && (
                            <li><span className="font-medium">Для путешествий:</span> Имейте компактный набор средств, удобный для поездок. Усиливайте защиту SPF при смене климата</li>
                          )}
                        </ul>
                      </div>
                      
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Полезные ингредиенты для вашей кожи</h3>
                        <ul className="space-y-3 text-sm ml-5 list-disc">
                          {skinAnalysis?.recommendations.ingredients.map((item, idx) => (
                            <li key={idx}><span className="font-medium">{item.name}</span> - {item.purpose}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </CardContent>
          </Card>
          
          {/* Рекомендуемые продукты */}
          <div>
            <h2 className="text-2xl font-bold mb-6">Рекомендуемые продукты</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
              {recommendations.map(product => (
                <Card key={product.id} className="overflow-hidden p-0">
                  <div className="relative h-48">
                    <img 
                      src={product.imageUrl} 
                      alt={product.name} 
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <CardContent className="p-5">
                    <h3 className="font-semibold text-base mb-1">{product.name}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{product.description}</p>
                    <div className="flex flex-wrap gap-1 mb-4">
                      {product.benefits?.map((benefit, index) => (
                        <span key={index} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                          {benefit}
                        </span>
                      ))}
                    </div>
                    <div className="flex justify-between items-center">
                      <div className="flex flex-col">
                        <span className="font-bold text-primary">
                          {product.salePrice || product.price} ₽
                        </span>
                        {product.salePrice && product.discount && (
                          <span className="text-xs text-muted-foreground line-through">
                            {product.price} ₽
                          </span>
                        )}
                      </div>
                      <Button 
                        size="sm" 
                        variant="default" 
                        onClick={() => window.open(product.url || `https://www.wildberries.ru/catalog/${product.id}/detail.aspx`, '_blank')}
                      >
                        <ShoppingBag className="h-4 w-4 mr-2" />
                        Купить
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
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
      `}</style>
    </div>
  );
};

export default CosmetologistAssistant; 