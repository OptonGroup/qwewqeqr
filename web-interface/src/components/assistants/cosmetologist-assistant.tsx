"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, ShoppingBag, ArrowRight } from 'lucide-react';

interface CosmeticProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  imageUrl: string;
  category: string;
  benefits: string[];
}

const mockProducts: CosmeticProduct[] = [
  {
    id: '1',
    name: 'Увлажняющий крем для лица',
    description: 'Интенсивное увлажнение для сухой и чувствительной кожи',
    price: 1290,
    imageUrl: 'https://images.unsplash.com/photo-1570194065650-d99fb4ee2063?w=500&auto=format',
    category: 'Уход за лицом',
    benefits: ['Увлажнение', 'Питание', 'Защита']
  },
  {
    id: '2',
    name: 'Сыворотка с гиалуроновой кислотой',
    description: 'Интенсивное увлажнение и разглаживание мелких морщин',
    price: 1890,
    imageUrl: 'https://images.unsplash.com/photo-1556229174-5e42a09e36c5?w=500&auto=format',
    category: 'Уход за лицом',
    benefits: ['Увлажнение', 'Антивозрастной эффект', 'Выравнивание тона']
  },
  {
    id: '3',
    name: 'Очищающий гель для умывания',
    description: 'Бережное очищение для всех типов кожи',
    price: 790,
    imageUrl: 'https://images.unsplash.com/photo-1610705267928-1b9f2fa7f1c5?w=500&auto=format',
    category: 'Очищение',
    benefits: ['Очищение', 'Тонизирование', 'Мягкое воздействие']
  },
  {
    id: '4',
    name: 'Ночная восстанавливающая маска',
    description: 'Интенсивное восстановление кожи во время сна',
    price: 1490,
    imageUrl: 'https://images.unsplash.com/photo-1599305090598-fe179d501227?w=500&auto=format',
    category: 'Маски',
    benefits: ['Восстановление', 'Питание', 'Регенерация']
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

const CosmetologistAssistant: React.FC = () => {
  const [selectedSkinType, setSelectedSkinType] = useState<string | null>(null);
  const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);
  const [age, setAge] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<CosmeticProduct[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  
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
      setRecommendations(mockProducts);
      setCurrentStep(4);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-8 text-foreground/90">Персональный косметолог</h1>
      
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
                    <Button variant="outline" size="sm" className="rounded-full">Активный</Button>
                    <Button variant="outline" size="sm" className="rounded-full">Офис</Button>
                    <Button variant="outline" size="sm" className="rounded-full">Спорт</Button>
                    <Button variant="outline" size="sm" className="rounded-full">Путешествия</Button>
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
                />
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Ограничения и аллергии (необязательно)
                </label>
                <Input
                  placeholder="Например: аллергия на эфирные масла"
                  className="h-11"
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
                    {selectedSkinType === 'dry' && 'У вас сухая кожа, которая нуждается в интенсивном увлажнении и питании.'}
                    {selectedSkinType === 'oily' && 'У вас жирная кожа, которой нужно бережное очищение и контроль себорегуляции.'}
                    {selectedSkinType === 'combination' && 'У вас комбинированная кожа, требующая балансирующего ухода.'}
                    {selectedSkinType === 'sensitive' && 'У вас чувствительная кожа, которой необходим бережный уход без агрессивных компонентов.'}
                    {selectedSkinType === 'normal' && 'У вас нормальная кожа, которой нужно поддерживающий уход и защита.'}
                    {selectedConcerns.includes('aging') && ' Также заметны признаки возрастных изменений, требующие средств с антивозрастным эффектом.'}
                    {selectedConcerns.includes('acne') && ' Высыпания указывают на необходимость противовоспалительных компонентов.'}
                    {selectedConcerns.includes('pigmentation') && ' Пигментация требует средств, выравнивающих тон кожи.'}
                  </p>
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
                          <li>Очищение: <span className="text-primary font-medium">Очищающий гель для умывания</span></li>
                          <li>Тонизирование: <span className="text-primary font-medium">Увлажняющий тоник без спирта</span></li>
                          <li>Сыворотка: <span className="text-primary font-medium">Сыворотка с гиалуроновой кислотой</span></li>
                          <li>Увлажнение: <span className="text-primary font-medium">Увлажняющий крем для лица</span></li>
                          <li>Защита: <span className="text-primary font-medium">Солнцезащитный крем SPF 30+</span></li>
                        </ol>
                      </div>
                      
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Вечерний уход</h3>
                        <ol className="space-y-3 text-sm ml-5 list-decimal">
                          <li>Очищение: <span className="text-primary font-medium">Очищающий гель для умывания</span></li>
                          <li>Тонизирование: <span className="text-primary font-medium">Увлажняющий тоник без спирта</span></li>
                          <li>Сыворотка: <span className="text-primary font-medium">Ночная восстанавливающая сыворотка</span></li>
                          <li>Увлажнение: <span className="text-primary font-medium">Ночная восстанавливающая маска</span> (2-3 раза в неделю)</li>
                          <li>Крем для глаз: <span className="text-primary font-medium">Увлажняющий крем для области вокруг глаз</span></li>
                        </ol>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="weekly">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Еженедельный уход</h3>
                        <ol className="space-y-3 text-sm ml-5 list-decimal">
                          <li>Эксфолиация: <span className="text-primary font-medium">Мягкий пилинг с AHA-кислотами</span> (1-2 раза в неделю)</li>
                          <li>Маска: <span className="text-primary font-medium">Увлажняющая тканевая маска</span> (1-2 раза в неделю)</li>
                          <li>Глубокое очищение: <span className="text-primary font-medium">Очищающая маска с глиной</span> (1 раз в неделю)</li>
                        </ol>
                      </div>
                      
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Дополнительный уход</h3>
                        <ul className="space-y-3 text-sm ml-5 list-disc">
                          <li>Уход за губами: <span className="text-primary font-medium">Увлажняющий бальзам для губ</span></li>
                          <li>Уход за руками: <span className="text-primary font-medium">Питательный крем для рук</span></li>
                          <li>Массаж лица: использование нефритового роллера для улучшения микроциркуляции</li>
                        </ul>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="recommendations">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Рекомендации по образу жизни</h3>
                        <ul className="space-y-3 text-sm ml-5 list-disc">
                          <li>Пить не менее 1,5-2 литров воды в день</li>
                          <li>Защищать кожу от солнца круглый год</li>
                          <li>Избегать горячей воды при умывании</li>
                          <li>Регулярно менять наволочки (минимум раз в неделю)</li>
                          <li>Ограничить потребление сахара и быстрых углеводов</li>
                        </ul>
                      </div>
                      
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Полезные ингредиенты для вашей кожи</h3>
                        <ul className="space-y-3 text-sm ml-5 list-disc">
                          <li><span className="font-medium">Гиалуроновая кислота</span> - для глубокого увлажнения</li>
                          <li><span className="font-medium">Ниацинамид</span> - для укрепления барьерной функции кожи</li>
                          <li><span className="font-medium">Пептиды</span> - для стимуляции выработки коллагена</li>
                          <li><span className="font-medium">Церамиды</span> - для восстановления защитного барьера</li>
                          <li><span className="font-medium">Антиоксиданты</span> - для защиты от свободных радикалов</li>
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
                      {product.benefits.map((benefit, index) => (
                        <span key={index} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                          {benefit}
                        </span>
                      ))}
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="font-bold">{product.price} ₽</span>
                      <Button size="sm" variant="outline">
                        <ShoppingBag className="h-4 w-4 mr-2" />
                        В корзину
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