"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, ShoppingBag, ArrowRight, Upload, Calculator, Home } from 'lucide-react';
import { useAppContext } from '@/context/app-context';

interface FoodProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  imageUrl: string;
  category: string;
  nutrients: {
    calories: number;
    proteins: number;
    fats: number;
    carbs: number;
  };
  benefits: string[];
}

const mockProducts: FoodProduct[] = [
  {
    id: '1',
    name: 'Куриная грудка',
    description: 'Диетическое мясо птицы, богатое белком',
    price: 299,
    imageUrl: 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=500&auto=format',
    category: 'Мясо',
    nutrients: {
      calories: 165,
      proteins: 31,
      fats: 3.6,
      carbs: 0
    },
    benefits: ['Высокий белок', 'Низкий жир', 'B витамины']
  },
  {
    id: '2',
    name: 'Лосось атлантический',
    description: 'Жирная рыба, богатая омега-3',
    price: 899,
    imageUrl: 'https://images.unsplash.com/photo-1599084993091-1cb5c0721cc6?w=500&auto=format',
    category: 'Рыба',
    nutrients: {
      calories: 208,
      proteins: 22,
      fats: 13,
      carbs: 0
    },
    benefits: ['Омега-3', 'Витамин D', 'Белок']
  },
  {
    id: '3',
    name: 'Киноа',
    description: 'Полезная безглютеновая крупа',
    price: 259,
    imageUrl: 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500&auto=format',
    category: 'Крупы',
    nutrients: {
      calories: 120,
      proteins: 4.4,
      fats: 1.9,
      carbs: 21.3
    },
    benefits: ['Без глютена', 'Клетчатка', 'Растительный белок']
  },
  {
    id: '4',
    name: 'Авокадо',
    description: 'Источник полезных жиров и витаминов',
    price: 159,
    imageUrl: 'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=500&auto=format',
    category: 'Фрукты',
    nutrients: {
      calories: 160,
      proteins: 2,
      fats: 14.7,
      carbs: 8.5
    },
    benefits: ['Полезные жиры', 'Витамин E', 'Калий']
  }
];

const dietaryGoals = [
  { id: 'weight_loss', name: 'Снижение веса' },
  { id: 'muscle_gain', name: 'Набор мышечной массы' },
  { id: 'health', name: 'Здоровое питание' },
  { id: 'energy', name: 'Повышение энергии' },
  { id: 'special', name: 'Особые потребности' }
];

const restrictions = [
  { id: 'none', name: 'Нет ограничений' },
  { id: 'vegetarian', name: 'Вегетарианство' },
  { id: 'vegan', name: 'Веганство' },
  { id: 'gluten_free', name: 'Без глютена' },
  { id: 'lactose_free', name: 'Без лактозы' },
  { id: 'diabetes', name: 'Диабет' }
];

interface NutritionistAssistantProps {
  onReturnHome?: () => void;
}

const NutritionistAssistant: React.FC<NutritionistAssistantProps> = ({ onReturnHome }) => {
  const { setSelectedRole } = useAppContext();
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [selectedRestrictions, setSelectedRestrictions] = useState<string[]>([]);
  const [personalInfo, setPersonalInfo] = useState({
    age: '',
    weight: '',
    height: '',
    activity: 'medium'
  });
  const [bankStatement, setBankStatement] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<FoodProduct[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  
  const handleGoalSelect = (goal: string) => {
    setSelectedGoal(goal);
  };
  
  const handleRestrictionToggle = (restriction: string) => {
    if (selectedRestrictions.includes(restriction)) {
      setSelectedRestrictions(selectedRestrictions.filter(r => r !== restriction));
    } else {
      setSelectedRestrictions([...selectedRestrictions, restriction]);
    }
  };
  
  const handlePersonalInfoChange = (field: string, value: string) => {
    setPersonalInfo(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setBankStatement(file);
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
      setRecommendations(mockProducts);
      setCurrentStep(4);
      setIsLoading(false);
    }, 1500);
  };

  const calculateDailyCalories = () => {
    const weight = parseFloat(personalInfo.weight);
    const height = parseFloat(personalInfo.height);
    const age = parseFloat(personalInfo.age);
    
    if (isNaN(weight) || isNaN(height) || isNaN(age)) return null;
    
    // Формула Миффлина-Сан Жеора
    const bmr = 10 * weight + 6.25 * height - 5 * age + 5;
    
    // Коэффициент активности
    const activityMultipliers = {
      low: 1.2,
      medium: 1.55,
      high: 1.725
    };
    
    const tdee = bmr * activityMultipliers[personalInfo.activity as keyof typeof activityMultipliers];
    
    // Корректировка в зависимости от цели
    const goalMultipliers = {
      weight_loss: 0.85,
      muscle_gain: 1.1,
      health: 1,
      energy: 1,
      special: 1
    };
    
    return Math.round(tdee * (selectedGoal ? goalMultipliers[selectedGoal as keyof typeof goalMultipliers] : 1));
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Ассистент нутрициолога</h1>
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
          {currentStep === 1 && 'Шаг 1: Выберите цель'}
          {currentStep === 2 && 'Шаг 2: Укажите ограничения'}
          {currentStep === 3 && 'Шаг 3: Персональные данные'}
          {currentStep === 4 && 'Шаг 4: Ваши рекомендации'}
        </div>
      </div>
      
      {/* Шаг 1: Цель */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Выберите вашу цель</CardTitle>
            <CardDescription>
              От этого будет зависеть расчет калорий и подбор продуктов
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
              {dietaryGoals.map((goal) => (
                <div 
                  key={goal.id}
                  className={`p-5 border rounded-xl cursor-pointer hover:border-primary transition-all ${
                    selectedGoal === goal.id ? 'border-primary bg-primary/5 shadow-sm' : 'border-border/60'
                  }`}
                  onClick={() => handleGoalSelect(goal.id)}
                >
                  <h3 className="font-semibold text-lg mb-1">{goal.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {goal.id === 'weight_loss' && 'Снижение калорийности с сохранением питательности'}
                    {goal.id === 'muscle_gain' && 'Увеличение белка и общей калорийности'}
                    {goal.id === 'health' && 'Баланс нутриентов и витаминов'}
                    {goal.id === 'energy' && 'Продукты для поддержания энергии'}
                    {goal.id === 'special' && 'Особый рацион под ваши потребности'}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end mt-8">
              <Button onClick={handleNextStep} disabled={!selectedGoal} className="px-6">
                Далее <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Шаг 2: Ограничения */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Укажите ограничения</CardTitle>
            <CardDescription>
              Выберите все подходящие варианты
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
              {restrictions.map((restriction) => (
                <div 
                  key={restriction.id}
                  className={`p-5 border rounded-xl cursor-pointer hover:border-primary transition-all ${
                    selectedRestrictions.includes(restriction.id) ? 'border-primary bg-primary/5 shadow-sm' : 'border-border/60'
                  }`}
                  onClick={() => handleRestrictionToggle(restriction.id)}
                >
                  <h3 className="font-semibold text-lg mb-1">{restriction.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {restriction.id === 'vegetarian' && 'Без мяса, но с яйцами и молочными продуктами'}
                    {restriction.id === 'vegan' && 'Исключительно растительная пища'}
                    {restriction.id === 'gluten_free' && 'Без продуктов, содержащих глютен'}
                    {restriction.id === 'lactose_free' && 'Без молочных продуктов'}
                    {restriction.id === 'diabetes' && 'Контроль гликемического индекса'}
                    {restriction.id === 'none' && 'Нет специальных ограничений в питании'}
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
      
      {/* Шаг 3: Персональные данные */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Персональные данные</CardTitle>
            <CardDescription>
              Эта информация поможет рассчитать ваши потребности в калориях и нутриентах
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                <div className="space-y-2">
                  <label htmlFor="age" className="text-sm font-medium">
                    Возраст
                  </label>
                  <Input
                    id="age"
                    type="number"
                    placeholder="Лет"
                    value={personalInfo.age}
                    onChange={(e) => handlePersonalInfoChange('age', e.target.value)}
                    className="h-11"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="weight" className="text-sm font-medium">
                    Вес
                  </label>
                  <Input
                    id="weight"
                    type="number"
                    placeholder="кг"
                    value={personalInfo.weight}
                    onChange={(e) => handlePersonalInfoChange('weight', e.target.value)}
                    className="h-11"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="height" className="text-sm font-medium">
                    Рост
                  </label>
                  <Input
                    id="height"
                    type="number"
                    placeholder="см"
                    value={personalInfo.height}
                    onChange={(e) => handlePersonalInfoChange('height', e.target.value)}
                    className="h-11"
                  />
                </div>
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Уровень физической активности
                </label>
                <div className="flex flex-wrap gap-3">
                  <Button 
                    variant={personalInfo.activity === 'low' ? 'default' : 'outline'} 
                    size="sm" 
                    onClick={() => handlePersonalInfoChange('activity', 'low')}
                    className="rounded-full"
                  >
                    Низкий
                  </Button>
                  <Button 
                    variant={personalInfo.activity === 'medium' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => handlePersonalInfoChange('activity', 'medium')}
                    className="rounded-full"
                  >
                    Средний
                  </Button>
                  <Button 
                    variant={personalInfo.activity === 'high' ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => handlePersonalInfoChange('activity', 'high')}
                    className="rounded-full"
                  >
                    Высокий
                  </Button>
                </div>
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Банковская выписка (для анализа расходов на питание)
                </label>
                <div className="border-2 border-dashed rounded-xl p-8 transition-colors hover:border-primary/50 bg-background">
                  <input
                    type="file"
                    id="bank-statement"
                    className="hidden"
                    accept=".pdf,.txt"
                    onChange={handleFileChange}
                  />
                  <label 
                    htmlFor="bank-statement" 
                    className="cursor-pointer flex flex-col items-center justify-center"
                  >
                    <Upload className="h-12 w-12 text-muted-foreground mb-3" />
                    <p className="text-muted-foreground text-center">
                      Загрузите выписку в формате PDF или TXT
                      <br />
                      <span className="text-sm">
                        Это поможет оптимизировать расходы на питание
                      </span>
                    </p>
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
                disabled={isLoading || !personalInfo.age || !personalInfo.weight || !personalInfo.height}
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
          <Card>
            <CardHeader>
              <CardTitle>Ваш персональный план питания</CardTitle>
              <CardDescription>
                Рекомендации составлены на основе ваших данных и целей
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {/* Калории и макронутриенты */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-6 bg-primary/5 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Calculator className="h-5 w-5 text-primary" />
                      <h3 className="font-semibold text-lg">Ваша суточная норма калорий</h3>
                    </div>
                    <div className="text-4xl font-bold mb-2 text-primary">
                      {calculateDailyCalories()} <span className="text-base font-medium text-primary/80">ккал</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Расчет учитывает ваши параметры, уровень активности и цель
                    </p>
                  </div>
                  
                  <div className="p-6 border rounded-xl">
                    <h3 className="font-semibold text-lg mb-4">Рекомендуемое соотношение БЖУ</h3>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm">Белки</span>
                          <span className="font-medium">{Math.round(calculateDailyCalories()! * 0.3 / 4)}г</span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: '30%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm">Жиры</span>
                          <span className="font-medium">{Math.round(calculateDailyCalories()! * 0.3 / 9)}г</span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-yellow-500 rounded-full" style={{ width: '30%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm">Углеводы</span>
                          <span className="font-medium">{Math.round(calculateDailyCalories()! * 0.4 / 4)}г</span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 rounded-full" style={{ width: '40%' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <Tabs defaultValue="diet" className="w-full">
                  <TabsList className="mb-6">
                    <TabsTrigger value="diet">План питания</TabsTrigger>
                    <TabsTrigger value="products">Продукты</TabsTrigger>
                    <TabsTrigger value="budget">Бюджет</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="diet">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Режим питания</h3>
                        <div className="space-y-6">
                          <div>
                            <h4 className="text-base font-medium mb-2">Завтрак <span className="text-primary/90 text-sm">(25% калорий)</span></h4>
                            <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                              <li>Сложные углеводы для энергии</li>
                              <li>Белок для насыщения</li>
                              <li>Клетчатка для пищеварения</li>
                            </ul>
                          </div>
                          
                          <div>
                            <h4 className="text-base font-medium mb-2">Обед <span className="text-primary/90 text-sm">(35% калорий)</span></h4>
                            <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                              <li>Основной источник белка</li>
                              <li>Сложные углеводы</li>
                              <li>Овощи для витаминов</li>
                            </ul>
                          </div>
                          
                          <div>
                            <h4 className="text-base font-medium mb-2">Ужин <span className="text-primary/90 text-sm">(30% калорий)</span></h4>
                            <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                              <li>Легкоусвояемый белок</li>
                              <li>Минимум углеводов</li>
                              <li>Полезные жиры</li>
                            </ul>
                          </div>
                          
                          <div>
                            <h4 className="text-base font-medium mb-2">Перекусы <span className="text-primary/90 text-sm">(10% калорий)</span></h4>
                            <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                              <li>Фрукты и орехи</li>
                              <li>Протеиновые снеки</li>
                              <li>Овощные нарезки</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="products">
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
                            <h3 className="font-semibold text-base">{product.name}</h3>
                            <p className="text-sm text-muted-foreground mb-3">{product.description}</p>
                            <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                              <div className="p-2 bg-primary/5 rounded">
                                <span className="font-medium block">Калории:</span> {product.nutrients.calories}
                              </div>
                              <div className="p-2 bg-primary/5 rounded">
                                <span className="font-medium block">Белки:</span> {product.nutrients.proteins}г
                              </div>
                              <div className="p-2 bg-primary/5 rounded">
                                <span className="font-medium block">Жиры:</span> {product.nutrients.fats}г
                              </div>
                              <div className="p-2 bg-primary/5 rounded">
                                <span className="font-medium block">Углеводы:</span> {product.nutrients.carbs}г
                              </div>
                            </div>
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
                  </TabsContent>
                  
                  <TabsContent value="budget">
                    <div className="space-y-5">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Анализ расходов на питание</h3>
                        {bankStatement ? (
                          <div className="space-y-6">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                              <div className="p-5 bg-primary/5 rounded-xl">
                                <div className="text-sm text-muted-foreground mb-1">Средние расходы в месяц</div>
                                <div className="text-2xl font-bold">15 780 ₽</div>
                              </div>
                              <div className="p-5 bg-primary/5 rounded-xl">
                                <div className="text-sm text-muted-foreground mb-1">Рекомендуемый бюджет</div>
                                <div className="text-2xl font-bold">12 500 ₽</div>
                              </div>
                              <div className="p-5 bg-primary/5 rounded-xl">
                                <div className="text-sm text-muted-foreground mb-1">Потенциальная экономия</div>
                                <div className="text-2xl font-bold text-green-600">3 280 ₽</div>
                              </div>
                            </div>
                            
                            <div>
                              <h4 className="font-medium mb-3">Рекомендации по оптимизации:</h4>
                              <ul className="list-disc list-inside text-sm space-y-2 text-muted-foreground">
                                <li>Покупайте сезонные овощи и фрукты</li>
                                <li>Используйте оптовые закупки для длительного хранения</li>
                                <li>Планируйте меню на неделю вперед</li>
                                <li>Готовьте большими порциями с заморозкой</li>
                                <li>Следите за акциями в магазинах</li>
                              </ul>
                            </div>
                          </div>
                        ) : (
                          <div className="text-center py-10 text-muted-foreground">
                            <p>Загрузите банковскую выписку для анализа расходов</p>
                            <Button variant="outline" className="mt-4" onClick={() => setCurrentStep(3)}>
                              Загрузить выписку
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default NutritionistAssistant; 