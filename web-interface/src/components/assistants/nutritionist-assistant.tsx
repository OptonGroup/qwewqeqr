"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, ShoppingBag, ArrowRight, Calculator, Home, Loader2 } from 'lucide-react';
import { useAppContext } from '@/context/app-context';
import { nutritionistApi } from '@/lib/api';

interface NutritionistApiResponse {
  success: boolean;
  nutritionAnalysis?: any;
  recommendedProducts?: any[];
  error?: string;
}

interface FoodProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  originalPrice?: number; // Исходная цена до скидки
  imageUrl: string;
  category: string;
  productUrl?: string; // URL страницы товара
  nutrients: {
    calories: number;
    proteins: number;
    fats: number;
    carbs: number;
  };
  benefits: string[];
}

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

// Интерфейс для запроса к нейронной сети
interface MealPlanRequest {
  calories: number;
  proteins: number;
  fats: number;
  carbs: number;
  goal: string | null;
  restrictions: string[];
  age: number;
  weight: number;
  height: number;
  activityLevel: string;
}

// Интерфейс для ответа от нейронной сети
interface MealPlanResponse {
  success: boolean;
  weeklyMealPlan?: Record<string, any>;
  error?: string;
}

export function NutritionistAssistant({ onReturnHome }: NutritionistAssistantProps): JSX.Element {
  const { setSelectedRole } = useAppContext();
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [selectedRestrictions, setSelectedRestrictions] = useState<string[]>([]);
  const [personalInfo, setPersonalInfo] = useState({
    age: '',
    weight: '',
    height: '',
    activity: 'medium'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<FoodProduct[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [nutritionAnalysis, setNutritionAnalysis] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<string>('Понедельник');
  const [isGeneratingMealPlan, setIsGeneratingMealPlan] = useState(false);
  
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
  
  const handleNextStep = () => {
    setCurrentStep(currentStep + 1);
  };
  
  const handlePrevStep = () => {
    setCurrentStep(currentStep - 1);
  };
  
  // Функция для генерации плана питания через нейронную сеть
  const generateMealPlanWithAI = async (request: MealPlanRequest): Promise<Record<string, any>> => {
    setIsGeneratingMealPlan(true);
    
    try {
      // Здесь будет запрос к API нейронной сети
      // Для примера используем эмуляцию запроса через timeout
      console.log('Отправляем запрос к нейронной сети:', request);
      
      // В реальном приложении здесь должен быть вызов API
      // const response = await fetch('/api/generate-meal-plan', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(request)
      // });
      // const data: MealPlanResponse = await response.json();
      
      // Эмуляция задержки запроса к API
      return new Promise((resolve) => {
        setTimeout(() => {
          // Используем локальную генерацию пока нет реального API
          const weeklyPlan = generateDefaultMealPlan(
            request.calories,
            request.proteins,
            request.fats,
            request.carbs
          );
          resolve(weeklyPlan);
        }, 1500);
      });
    } catch (error) {
      console.error('Ошибка при генерации плана питания:', error);
      // В случае ошибки возвращаем план по умолчанию
      return generateDefaultMealPlan(
        request.calories,
        request.proteins,
        request.fats,
        request.carbs
      );
    } finally {
      setIsGeneratingMealPlan(false);
    }
  };

  // Переименовываем текущую функцию generateWeeklyMealPlan в generateDefaultMealPlan
  const generateDefaultMealPlan = (
    calories: number,
    proteins: number,
    fats: number,
    carbs: number
  ) => {
    // Распределение калорий по приемам пищи
    const breakfastCalories = Math.round(calories * 0.25);
    const lunchCalories = Math.round(calories * 0.35);
    const dinnerCalories = Math.round(calories * 0.30);
    const snackCalories = Math.round(calories * 0.10);

    // Распределение макронутриентов по приемам пищи
    const breakfastProteins = Math.round(proteins * 0.25);
    const lunchProteins = Math.round(proteins * 0.35);
    const dinnerProteins = Math.round(proteins * 0.30);
    const snackProteins = Math.round(proteins * 0.10);

    const breakfastFats = Math.round(fats * 0.25);
    const lunchFats = Math.round(fats * 0.35);
    const dinnerFats = Math.round(fats * 0.30);
    const snackFats = Math.round(fats * 0.10);

    const breakfastCarbs = Math.round(carbs * 0.35); // Больше углеводов на завтрак
    const lunchCarbs = Math.round(carbs * 0.35);
    const dinnerCarbs = Math.round(carbs * 0.20); // Меньше углеводов на ужин
    const snackCarbs = Math.round(carbs * 0.10);

    // Варианты блюд для каждого приема пищи
    const breakfastOptions = [
      { 
        name: 'Овсянка с фруктами и орехами', 
        description: 'Питательный завтрак с клетчаткой и белком',
        ingredients: ['Овсяные хлопья', 'Банан', 'Яблоко', 'Грецкие орехи', 'Мед', 'Корица'],
        recipe: 'Залить овсяные хлопья горячей водой или молоком, добавить нарезанные фрукты, орехи, мед и корицу по вкусу.'
      },
      { 
        name: 'Творожная запеканка с ягодами', 
        description: 'Высокобелковый завтрак для энергичного начала дня',
        ingredients: ['Творог 5%', 'Яйца', 'Ягоды', 'Мед', 'Овсяная мука'],
        recipe: 'Смешать творог с яйцами и медом, добавить овсяную муку, выложить в форму, посыпать ягодами и запечь при 180°C около 25 минут.'
      },
      { 
        name: 'Омлет с овощами и цельнозерновым тостом', 
        description: 'Сбалансированный белковый завтрак',
        ingredients: ['Яйца', 'Молоко', 'Шпинат', 'Помидоры', 'Сыр', 'Цельнозерновой хлеб'],
        recipe: 'Взбить яйца с молоком, добавить нарезанные овощи, вылить на сковороду и готовить до золотистой корочки. Подавать с тостом.'
      },
      { 
        name: 'Протеиновый коктейль с бананом и арахисовой пастой', 
        description: 'Быстрый питательный завтрак для занятых дней',
        ingredients: ['Протеиновый порошок', 'Банан', 'Арахисовая паста', 'Молоко', 'Лед'],
        recipe: 'Смешать все ингредиенты в блендере до однородной массы. При желании добавить мед или ягоды для вкуса.'
      },
      { 
        name: 'Греческий йогурт с гранолой и свежими ягодами', 
        description: 'Легкий и питательный завтрак',
        ingredients: ['Греческий йогурт', 'Домашняя гранола', 'Свежие ягоды', 'Мед', 'Семена чиа'],
        recipe: 'Выложить йогурт в миску, добавить домашнюю гранолу, свежие ягоды, мед и семена чиа.'
      },
      { 
        name: 'Яичница с авокадо и лососем', 
        description: 'Высокобелковый завтрак с полезными жирами',
        ingredients: ['Яйца', 'Авокадо', 'Копченый лосось', 'Цельнозерновой хлеб', 'Зелень'],
        recipe: 'Приготовить яичницу на оливковом масле, подавать с нарезанным авокадо, копченым лососем и тостом.'
      },
      { 
        name: 'Банановые панкейки с ягодным соусом', 
        description: 'Вкусный и питательный завтрак',
        ingredients: ['Банан', 'Овсяная мука', 'Яйца', 'Молоко', 'Свежие ягоды', 'Мед'],
        recipe: 'Смешать измельченный банан, овсяную муку, яйца и молоко, обжарить панкейки на сковороде, подавать с ягодным соусом.'
      }
    ];

    const lunchOptions = [
      {
        name: 'Гречневая каша с индейкой и овощами',
        description: 'Сбалансированный обед с полноценным белком',
        ingredients: ['Гречка', 'Филе индейки', 'Брокколи', 'Морковь', 'Лук', 'Оливковое масло'],
        recipe: 'Отварить гречку, обжарить индейку с овощами, смешать и приправить по вкусу.'
      },
      {
        name: 'Киноа с куриной грудкой и запеченными овощами',
        description: 'Питательный и легкоусвояемый обед',
        ingredients: ['Киноа', 'Куриная грудка', 'Цукини', 'Болгарский перец', 'Помидоры черри', 'Специи'],
        recipe: 'Отварить киноа, запечь куриную грудку и овощи с оливковым маслом и специями, подавать вместе.'
      },
      {
        name: 'Рыбный стейк с печеным картофелем и зеленым салатом',
        description: 'Богатый белком и полезными жирами обед',
        ingredients: ['Стейк лосося', 'Картофель', 'Листья салата', 'Огурец', 'Помидоры', 'Оливковое масло'],
        recipe: 'Запечь рыбу и картофель, приготовить свежий салат, заправить оливковым маслом и лимонным соком.'
      },
      {
        name: 'Чечевичный суп с овощами и гренками',
        description: 'Богатый клетчаткой и растительным белком обед',
        ingredients: ['Чечевица', 'Морковь', 'Лук', 'Сельдерей', 'Томатная паста', 'Цельнозерновой хлеб'],
        recipe: 'Сварить чечевицу с овощами и специями, подавать с цельнозерновыми гренками.'
      },
      {
        name: 'Булгур с тефтелями из говядины и томатным соусом',
        description: 'Сбалансированный обед с полноценным белком',
        ingredients: ['Булгур', 'Говяжий фарш', 'Лук', 'Томаты в собственном соку', 'Зелень', 'Специи'],
        recipe: 'Отварить булгур, приготовить тефтели, запечь в томатном соусе, подавать вместе, посыпав зеленью.'
      },
      {
        name: 'Бурый рис с тушеной курицей и грибами',
        description: 'Питательный обед с медленными углеводами',
        ingredients: ['Бурый рис', 'Куриное филе', 'Грибы', 'Лук', 'Сметана', 'Зелень'],
        recipe: 'Отварить бурый рис, отдельно потушить курицу с грибами и луком в сметанном соусе, подавать вместе.'
      },
      {
        name: 'Фасолевый суп с курицей и овощами',
        description: 'Богатый белком и клетчаткой обед',
        ingredients: ['Фасоль', 'Куриное филе', 'Морковь', 'Лук', 'Сельдерей', 'Томаты'],
        recipe: 'Сварить фасоль, добавить обжаренную с овощами курицу, томаты и специи, варить до готовности.'
      }
    ];

    const dinnerOptions = [
      {
        name: 'Запеченная куриная грудка с овощным рагу',
        description: 'Легкий белковый ужин с минимумом углеводов',
        ingredients: ['Куриная грудка', 'Кабачки', 'Баклажаны', 'Помидоры', 'Чеснок', 'Прованские травы'],
        recipe: 'Запечь куриную грудку с травами, отдельно приготовить овощное рагу, подавать вместе.'
      },
      {
        name: 'Рыбный терин с овощным гарниром',
        description: 'Богатый белком ужин с полезными жирами',
        ingredients: ['Филе белой рыбы', 'Шпинат', 'Морковь', 'Цветная капуста', 'Оливковое масло', 'Лимон'],
        recipe: 'Запечь рыбу с овощами, приправить лимонным соком и зеленью.'
      },
      {
        name: 'Омлет с овощами и сыром',
        description: 'Легкий белковый ужин',
        ingredients: ['Яйца', 'Шпинат', 'Помидоры черри', 'Сыр фета', 'Зелень', 'Оливковое масло'],
        recipe: 'Взбить яйца, добавить нарезанные овощи и сыр, запечь на сковороде или в духовке.'
      },
      {
        name: 'Тушеная индейка с брокколи и шпинатом',
        description: 'Легкоусвояемый белковый ужин',
        ingredients: ['Филе индейки', 'Брокколи', 'Шпинат', 'Чеснок', 'Лимонный сок', 'Оливковое масло'],
        recipe: 'Обжарить индейку, добавить брокколи и шпинат, тушить до готовности, приправить чесноком и лимонным соком.'
      },
      {
        name: 'Креветки на гриле с авокадо и овощным салатом',
        description: 'Легкий ужин с полезными жирами и белком',
        ingredients: ['Креветки', 'Авокадо', 'Помидоры', 'Огурцы', 'Листья салата', 'Лимонный сок'],
        recipe: 'Обжарить креветки на гриле, приготовить салат из овощей и авокадо, заправить оливковым маслом и лимонным соком.'
      },
      {
        name: 'Творожная запеканка с зеленью и овощами',
        description: 'Высокобелковый лёгкий ужин',
        ingredients: ['Творог 5%', 'Яйца', 'Шпинат', 'Помидоры', 'Зелень', 'Специи'],
        recipe: 'Смешать творог с яйцами и овощами, запечь при 180°C около 25 минут.'
      },
      {
        name: 'Тыквенный суп-пюре с креветками',
        description: 'Легкий и питательный ужин',
        ingredients: ['Тыква', 'Креветки', 'Лук', 'Чеснок', 'Кокосовое молоко', 'Имбирь'],
        recipe: 'Сварить тыкву с луком и чесноком, измельчить в блендере, добавить кокосовое молоко и обжаренные креветки.'
      }
    ];

    const snackOptions = [
      {
        name: 'Греческий йогурт с орехами и медом',
        description: 'Питательный перекус с белком',
        ingredients: ['Греческий йогурт', 'Миндаль', 'Мед', 'Корица'],
        recipe: 'Смешать йогурт с измельченными орехами, добавить мед и корицу по вкусу.'
      },
      {
        name: 'Протеиновый батончик и яблоко',
        description: 'Быстрый перекус для восполнения энергии',
        ingredients: ['Протеиновый батончик', 'Яблоко'],
        recipe: 'Съесть протеиновый батончик с яблоком.'
      },
      {
        name: 'Творог с ягодами',
        description: 'Белковый перекус с антиоксидантами',
        ingredients: ['Творог 5%', 'Свежие ягоды', 'Мед'],
        recipe: 'Смешать творог с ягодами, при желании добавить мед или стевию.'
      },
      {
        name: 'Хумус с овощными палочками',
        description: 'Питательный перекус с растительным белком',
        ingredients: ['Хумус', 'Морковь', 'Огурец', 'Болгарский перец'],
        recipe: 'Нарезать овощи палочками, подавать с хумусом.'
      },
      {
        name: 'Миндаль и сухофрукты',
        description: 'Энергетический перекус с полезными жирами',
        ingredients: ['Миндаль', 'Курага', 'Чернослив', 'Изюм'],
        recipe: 'Смешать орехи и сухофрукты в небольшой порции.'
      },
      {
        name: 'Протеиновый коктейль',
        description: 'Быстрый способ восполнить белок',
        ingredients: ['Протеиновый порошок', 'Банан', 'Молоко', 'Лед'],
        recipe: 'Смешать все ингредиенты в блендере до однородной массы.'
      },
      {
        name: 'Яйца вкрутую и авокадо',
        description: 'Питательный перекус с полноценным белком',
        ingredients: ['Яйца', 'Авокадо', 'Соль', 'Перец'],
        recipe: 'Сварить яйца вкрутую, очистить и разрезать пополам, подавать с нарезанным авокадо.'
      }
    ];

    // Дни недели
    const daysOfWeek = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];

    // Создаем план на неделю
    const weeklyPlan: Record<string, any> = {};

    daysOfWeek.forEach((day, index) => {
      // Выбираем разные блюда для каждого дня
      const breakfastIndex = index % breakfastOptions.length;
      const lunchIndex = index % lunchOptions.length;
      const dinnerIndex = index % dinnerOptions.length;
      const snackIndex = index % snackOptions.length;

      // Создаем объект для текущего дня
      const breakfast = {
        ...breakfastOptions[breakfastIndex],
        calories: breakfastCalories,
        nutrients: {
          proteins: breakfastProteins,
          fats: breakfastFats,
          carbs: breakfastCarbs
        }
      };

      const lunch = {
        ...lunchOptions[lunchIndex],
        calories: lunchCalories,
        nutrients: {
          proteins: lunchProteins,
          fats: lunchFats,
          carbs: lunchCarbs
        }
      };

      const dinner = {
        ...dinnerOptions[dinnerIndex],
        calories: dinnerCalories,
        nutrients: {
          proteins: dinnerProteins,
          fats: dinnerFats,
          carbs: dinnerCarbs
        }
      };

      const snack = {
        ...snackOptions[snackIndex],
        calories: snackCalories,
        nutrients: {
          proteins: snackProteins,
          fats: snackFats,
          carbs: snackCarbs
        }
      };

      weeklyPlan[day] = {
        breakfast,
        lunch,
        dinner,
        snack,
        totalCalories: calories,
        totalNutrients: {
          proteins,
          fats,
          carbs
        }
      };
    });

    return weeklyPlan;
  };

  // Новая функция generateWeeklyMealPlan, которая использует нейронную сеть
  const generateWeeklyMealPlan = async () => {
    // Получаем калорийность и макронутриенты
    const calories = nutritionAnalysis ? nutritionAnalysis.dailyNutrition.calories : calculateDailyCalories() || 3222;
    const proteins = nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.proteins : Math.round(calories * 0.3 / 4) || 281;
    const fats = nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.fats : Math.round(calories * 0.3 / 9) || 89;
    const carbs = nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.carbs : Math.round(calories * 0.4 / 4) || 322;

    // Создаем запрос к нейронной сети
    const request: MealPlanRequest = {
      calories,
      proteins,
      fats,
      carbs,
      goal: selectedGoal,
      restrictions: selectedRestrictions,
      age: Number(personalInfo.age) || 30,
      weight: Number(personalInfo.weight) || 70,
      height: Number(personalInfo.height) || 170,
      activityLevel: personalInfo.activity
    };

    // Генерируем план питания через нейронную сеть
    return await generateMealPlanWithAI(request);
  };

  // Обновляем handleGetRecommendations для использования асинхронной генерации
  const handleGetRecommendations = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    
    try {
      // Собираем данные пользователя
      const userData = {
        goal: selectedGoal,
        restrictions: selectedRestrictions,
        personalInfo: {
          ...personalInfo,
          // Преобразуем строки в числа
          age: Number(personalInfo.age),
          weight: Number(personalInfo.weight),
          height: Number(personalInfo.height),
        }
      };
      
      // Отправляем запрос к API
      const response = await nutritionistApi.analyze(userData);
      
      // Обрабатываем успешный ответ
      const typedResponse = response as NutritionistApiResponse;
      if (typedResponse.success) {
        // Обогащаем данные о питании недельным планом
        const nutritionData = typedResponse.nutritionAnalysis || {};
        const weeklyMealPlan = await generateWeeklyMealPlan();
        
        // Сохраняем анализ питания вместе с недельным планом
        setNutritionAnalysis({
          ...nutritionData,
          weeklyMealPlan
        });

        if (typedResponse.recommendedProducts && typedResponse.recommendedProducts.length > 0) {
          // Преобразуем продукты из API в формат, используемый в компоненте
          const formattedProducts = typedResponse.recommendedProducts.map((product: any) => {
            // Получение правильного изображения с учетом батча
            let imageUrl = '';
            let debugInfo = {};
            
            if (product.id) {
              const id = parseInt(product.id);
              
              // Правильный алгоритм формирования URL изображения Wildberries:
              // 1. Извлекаем необходимые части из ID
              const idStr = id.toString();
              
              // Получаем первые N цифр для разных частей URL
              const vol = idStr.substring(0, 4); // Первые 4 цифры
              const part = idStr.substring(0, 6); // Первые 6 цифр
              
              // Вычисляем номер корзины (basket)
              // basket = ID / 16000000, округляем до целого
              const basketNum = Math.floor(id / 16000000);
              
              // Сохраняем отладочную информацию
              debugInfo = { id, vol, part, basketNum };
              console.log(`Формирование URL для товара ${id}:`, debugInfo);
              
              if (product.photos && product.photos.length > 0) {
                // Если у продукта есть фото в массиве photos
                const photoId = product.photos[0];
                // Проверяем, не полный ли это URL
                if (photoId.startsWith('http')) {
                  imageUrl = photoId;
                } else {
                  imageUrl = `https://cdn.wildberries.ru/product/big/${photoId}.jpg`;
                }
              } else if (product.pic_url) {
                // Используем pic_url, если он есть
                imageUrl = product.pic_url;
              } else if (product.img) {
                // Используем img, если он есть
                imageUrl = product.img;
              } else if (product.image) {
                // Используем image, если он есть
                imageUrl = product.image;
              } else {
                // Формируем URL в новом формате с basket-XX
                imageUrl = `https://basket-${basketNum}.wbbasket.ru/vol${vol}/part${part}/${id}/images/big/1.webp`;
                console.log(`Сформирован URL: ${imageUrl}`);
              }
            } else if (product.image) {
              imageUrl = product.image;
            } else if (product.pic_url) {
              imageUrl = product.pic_url;
            } else if (product.img) {
              imageUrl = product.img;
            } else {
              // Если не можем получить изображение, используем заглушку
              imageUrl = 'https://via.placeholder.com/300?text=Изображение+недоступно';
            }
            
            return {
              id: product.id || String(Math.random()).slice(2),
              name: product.name || "Товар без названия",
              description: product.description || 'Нет описания',
              price: product.salePriceU ? Math.floor(product.salePriceU/100) : product.price || 0,
              originalPrice: product.priceU ? Math.floor(product.priceU/100) : Math.round((product.price || 0) * 1.3),
              imageUrl: imageUrl,
              productUrl: product.link || product.url || (product.id ? `https://www.wildberries.ru/catalog/${product.id}/detail.aspx` : '#'),
              category: product.category || 'Спортивное питание',
              nutrients: {
                calories: product.nutrients?.calories || 0,
                proteins: product.nutrients?.proteins || 0,
                fats: product.nutrients?.fats || 0,
                carbs: product.nutrients?.carbs || 0
              },
              benefits: product.benefits || ['Спортивное питание']
            };
          });
          
          setRecommendations(formattedProducts);
        } else {
          // Если продуктов нет, покажем пустой массив и сообщение
          setRecommendations([]);
          setErrorMessage("К сожалению, по вашему запросу не удалось найти подходящие продукты. Попробуйте изменить параметры поиска.");
        }
      } else {
        // Обрабатываем ошибку от API
        setErrorMessage(typedResponse.error || 'Произошла ошибка при получении рекомендаций');
        setRecommendations([]);
      }
      
      // Переходим к шагу с рекомендациями
      setCurrentStep(4);
    } catch (error) {
      console.error('Ошибка при получении рекомендаций:', error);
      setErrorMessage('Произошла ошибка при получении рекомендаций. Пожалуйста, попробуйте позже.');
      setRecommendations([]);
      setCurrentStep(4);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleBuyProduct = (url: string) => {
    if (url) {
      window.open(url, '_blank');
    }
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

  // Обновляем также функцию generateLocalNutritionAnalysis
  const generateLocalNutritionAnalysis = async () => {
    const calories = calculateDailyCalories() || 3222;
    const proteins = Math.round(calories * 0.3 / 4); // 30% калорий из белков
    const fats = Math.round(calories * 0.3 / 9); // 30% калорий из жиров
    const carbs = Math.round(calories * 0.4 / 4); // 40% калорий из углеводов
    
    const proteinRatio = 30; // Процент белков в рационе
    const fatRatio = 30; // Процент жиров в рационе
    const carbRatio = 40; // Процент углеводов в рационе
    
    // Генерируем недельный план питания
    const weeklyMealPlan = await generateWeeklyMealPlan();
    
    return {
      dailyNutrition: {
        calories,
        macros: {
          proteins,
          fats,
          carbs,
          proteinRatio,
          fatRatio,
          carbRatio
        }
      },
      weeklyMealPlan
    };
  };

  // Восстанавливаем функцию handleImageError
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>, product: FoodProduct) => {
    const img = e.target as HTMLImageElement;
    
    if (product.id) {
      const id = parseInt(product.id);
      
      // Правильный алгоритм формирования URL изображения Wildberries:
      // 1. Извлекаем необходимые части из ID
      const idStr = id.toString();
      
      // Получаем первые N цифр для разных частей URL
      const vol = idStr.substring(0, 4); // Первые 4 цифры
      const part = idStr.substring(0, 6); // Первые 6 цифр
      
      // Вычисляем номер корзины (basket)
      // basket = ID / 16000000, округляем до целого
      const basketNum = Math.floor(id / 16000000);
      
      // Создаем массив возможных URL
      const possibleUrls: string[] = [];
      
      // Проверяем соседние корзины (текущую и ±1)
      const baskets = [
        basketNum,      // Основной basket
        basketNum + 1,  // Следующий basket
        basketNum - 1,  // Предыдущий basket
      ].filter(b => b >= 0); // Отфильтровываем отрицательные значения
      
      // Добавляем URL с разными basket в новом формате
      for (const basket of baskets) {
        possibleUrls.push(`https://basket-${basket}.wbbasket.ru/vol${vol}/part${part}/${id}/images/big/1.webp`);
      }
      
      // Добавляем старые форматы URL для совместимости
      // Извлекаем последние 5 цифр ID для старого формата
      const lastDigits = id % 100000;
      possibleUrls.push(
        `https://images.wbstatic.net/big/new/${vol}0000/${lastDigits}-1.jpg`,
        `https://images.wbstatic.net/c246x328/new/${vol}0000/${lastDigits}-1.jpg`,
        `https://images.wbstatic.net/tm/new/${vol}0000/${lastDigits}-1.jpg`,
        `https://cdn.wildberries.ru/c246x328/images/product/${id}/1.jpg`
      );
      
      // Отладочная информация
      console.log(`Ошибка загрузки изображения для товара ${id}, текущий URL: ${img.src}`);
      console.log(`Доступные альтернативные URL:`, possibleUrls);
      
      // Индекс текущего URL, который мы пробуем
      const currentUrlIndex = possibleUrls.indexOf(img.src);
      
      if (currentUrlIndex < possibleUrls.length - 1 && currentUrlIndex !== -1) {
        // Пробуем следующий URL из списка
        console.log(`Пробуем следующий URL: ${possibleUrls[currentUrlIndex + 1]}`);
        img.src = possibleUrls[currentUrlIndex + 1];
      } else if (currentUrlIndex === -1 && possibleUrls.length > 0) {
        // Текущий URL не найден в списке, пробуем первый из списка
        console.log(`Текущий URL не найден в списке, пробуем: ${possibleUrls[0]}`);
        img.src = possibleUrls[0];
      } else {
        // Если все URL уже испробованы, используем заглушку
        console.log(`Не удалось загрузить изображение, используем заглушку`);
        img.src = 'https://via.placeholder.com/300?text=Нет+изображения';
      }
    } else {
      // Если у товара нет ID, сразу используем заглушку
      img.src = 'https://via.placeholder.com/300?text=Нет+изображения';
    }
  };

  // Восстанавливаем функцию renderDayMealPlan
  const renderDayMealPlan = (dayPlan: any) => {
    if (!dayPlan) return null;
    
    return (
      <div className="space-y-6">
        {['breakfast', 'lunch', 'dinner', 'snack'].map((mealType) => {
          const meal = dayPlan[mealType];
          const mealNames = {
            breakfast: 'Завтрак',
            lunch: 'Обед',
            dinner: 'Ужин',
            snack: 'Перекус'
          };
          
          return (
            <div key={mealType} className="bg-secondary/20 rounded-lg p-4">
              <h4 className="font-medium text-lg mb-1 flex justify-between">
                <span>{mealNames[mealType as keyof typeof mealNames]}</span>
                <span className="text-primary/90">{meal.calories} ккал</span>
              </h4>
              <div className="text-muted-foreground text-sm mb-3">{meal.description}</div>
              
              <div className="mb-4">
                <h5 className="font-medium mb-2">{meal.name}</h5>
                
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-xs p-2 bg-blue-500/10 rounded">
                    <span className="font-medium block">Белки:</span> {meal.nutrients.proteins}г
                  </div>
                  <div className="text-xs p-2 bg-yellow-500/10 rounded">
                    <span className="font-medium block">Жиры:</span> {meal.nutrients.fats}г
                  </div>
                  <div className="text-xs p-2 bg-green-500/10 rounded">
                    <span className="font-medium block">Углеводы:</span> {meal.nutrients.carbs}г
                  </div>
                </div>
                
                <div className="mb-3">
                  <h6 className="font-medium mb-1 text-sm">Ингредиенты:</h6>
                  <div className="flex flex-wrap gap-1">
                    {meal.ingredients.map((ingredient: string, idx: number) => (
                      <span key={idx} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                        {ingredient}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h6 className="font-medium mb-1 text-sm">Способ приготовления:</h6>
                  <p className="text-xs text-muted-foreground">{meal.recipe}</p>
                </div>
              </div>
            </div>
          );
        })}
        
        <div className="mt-4 p-3 bg-primary/5 rounded-lg">
          <div className="font-medium flex justify-between">
            <span>Итого за день:</span>
            <span>{dayPlan.totalCalories} ккал</span>
          </div>
          <div className="text-sm text-muted-foreground">
            Белки: {dayPlan.totalNutrients.proteins}г, 
            Жиры: {dayPlan.totalNutrients.fats}г, 
            Углеводы: {dayPlan.totalNutrients.carbs}г
          </div>
        </div>
      </div>
    );
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
          {errorMessage && (
            <div className="p-4 border border-red-200 bg-red-50 text-red-600 rounded-md">
              {errorMessage}
            </div>
          )}
          
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
                      {nutritionAnalysis ? nutritionAnalysis.dailyNutrition.calories : calculateDailyCalories()} <span className="text-base font-medium text-primary/80">ккал</span>
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
                          <span className="font-medium">
                            {nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.proteins : Math.round(calculateDailyCalories()! * 0.3 / 4)}г
                          </span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 rounded-full" 
                            style={{ width: `${nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.proteinRatio : 30}%` }}
                          ></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm">Жиры</span>
                          <span className="font-medium">
                            {nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.fats : Math.round(calculateDailyCalories()! * 0.3 / 9)}г
                          </span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-yellow-500 rounded-full" 
                            style={{ width: `${nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.fatRatio : 30}%` }}
                          ></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm">Углеводы</span>
                          <span className="font-medium">
                            {nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.carbs : Math.round(calculateDailyCalories()! * 0.4 / 4)}г
                          </span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full" 
                            style={{ width: `${nutritionAnalysis ? nutritionAnalysis.dailyNutrition.macros.carbRatio : 40}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <Tabs defaultValue="diet" className="w-full">
                  <TabsList className="mb-6">
                    <TabsTrigger value="diet">План питания</TabsTrigger>
                    <TabsTrigger value="products">Товары</TabsTrigger>
                    <TabsTrigger value="weekly">Недельный план</TabsTrigger>
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
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                      {recommendations.length > 0 ? (
                        recommendations.map((product) => (
                          <div key={product.id} className="card rounded-xl border border-border/40 bg-card shadow-sm transition-all duration-200 hover:shadow-md overflow-hidden p-0">
                            <div className="relative h-48">
                              <img 
                                src={product.imageUrl} 
                                alt={product.name} 
                                className="w-full h-full object-cover"
                                onError={(e) => handleImageError(e, product)}
                              />
                            </div>
                            <div className="p-5">
                              <h3 className="font-semibold text-base mb-1">{product.name}</h3>
                              <p className="text-sm text-muted-foreground mb-3">{product.description}</p>
                              <div className="flex flex-wrap gap-1 mb-4">
                                {product.benefits && product.benefits.length > 0 && product.benefits.map((benefit, index) => (
                                  <span key={index} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                                    {benefit}
                                  </span>
                                ))}
                              </div>
                              <div className="flex justify-between items-center">
                                <div className="flex flex-col">
                                  <span className="font-bold text-primary">{product.price} ₽</span>
                                  {product.originalPrice && product.originalPrice > product.price && (
                                    <span className="text-xs text-muted-foreground line-through">{product.originalPrice} ₽</span>
                                  )}
                                </div>
                                <Button 
                                  size="sm" 
                                  onClick={() => handleBuyProduct(product.productUrl)}
                                  className="bg-primary text-primary-foreground shadow hover:bg-primary/90 active:scale-[0.98]"
                                >
                                  <ShoppingBag className="h-4 w-4 mr-2" />
                                  Купить
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="col-span-4 text-center py-12">
                          <div className="mx-auto w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-4">
                            <ShoppingBag className="h-10 w-10 text-muted-foreground/60" />
                          </div>
                          <h3 className="text-lg font-medium mb-2">Товары не найдены</h3>
                          <p className="text-muted-foreground max-w-md mx-auto">
                            К сожалению, не удалось найти подходящие товары по вашему запросу. Попробуйте изменить параметры или выбрать другую цель.
                          </p>
                          <Button 
                            onClick={() => setCurrentStep(1)} 
                            variant="outline" 
                            className="mt-4"
                          >
                            Изменить параметры
                          </Button>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="weekly">
                    <div className="space-y-6">
                      <div className="border rounded-xl p-5">
                        <h3 className="font-semibold text-lg mb-4">Ваш недельный план питания</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          План составлен с учетом ваших целей, ограничений и рассчитанной суточной нормы калорий.
                        </p>
                        
                        {/* Переключатель дней недели */}
                        <div className="flex flex-wrap gap-2 mb-6">
                          {['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'].map((day, index) => (
                            <Button 
                              key={day}
                              variant="outline" 
                              size="sm"
                              className={`rounded-full ${selectedDay === day ? 'bg-primary text-primary-foreground' : ''}`}
                              onClick={() => setSelectedDay(day)}
                            >
                              {day}
                            </Button>
                          ))}
                        </div>
                        
                        {/* Отображение плана питания на выбранный день */}
                        {isGeneratingMealPlan ? (
                          <div className="text-center py-20">
                            <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto mb-4" />
                            <p className="text-muted-foreground">Генерация плана питания с помощью ИИ...</p>
                          </div>
                        ) : (
                          <>
                            {(() => {
                              // Если данные от API отсутствуют, но есть персональные данные, генерируем план локально
                              if (!nutritionAnalysis) {
                                if (personalInfo.age && personalInfo.weight && personalInfo.height) {
                                  // Используем useEffect для асинхронной загрузки данных при первой отрисовке
                                  const [localPlan, setLocalPlan] = useState<any>(null);
                                  
                                  useEffect(() => {
                                    const fetchLocalPlan = async () => {
                                      const localAnalysis = await generateLocalNutritionAnalysis();
                                      setLocalPlan(localAnalysis.weeklyMealPlan[selectedDay]);
                                    };
                                    
                                    fetchLocalPlan();
                                  }, [selectedDay]);
                                  
                                  if (localPlan) {
                                    return renderDayMealPlan(localPlan);
                                  }
                                  
                                  return (
                                    <div className="text-center py-10">
                                      <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto mb-2" />
                                      <p className="text-muted-foreground">Загрузка плана питания...</p>
                                    </div>
                                  );
                                }
                                
                                return (
                                  <div className="text-center py-10 text-muted-foreground">
                                    <p>Недельный план питания недоступен. Пожалуйста, заполните ваши данные и нажмите "Получить рекомендации".</p>
                                  </div>
                                );
                              }
                              
                              // Используем данные из API, если они есть
                              if (nutritionAnalysis.weeklyMealPlan && nutritionAnalysis.weeklyMealPlan[selectedDay]) {
                                return renderDayMealPlan(nutritionAnalysis.weeklyMealPlan[selectedDay]);
                              }
                              
                              // Если план отсутствует в API-ответе, используем генерацию
                              return (
                                <div className="text-center py-10">
                                  <p className="text-muted-foreground mb-4">План питания еще не сгенерирован.</p>
                                  <Button 
                                    onClick={async () => {
                                      setIsGeneratingMealPlan(true);
                                      try {
                                        const plan = await generateWeeklyMealPlan();
                                        setNutritionAnalysis(prev => ({
                                          ...prev,
                                          weeklyMealPlan: plan
                                        }));
                                      } catch (error) {
                                        console.error('Ошибка при генерации плана:', error);
                                      } finally {
                                        setIsGeneratingMealPlan(false);
                                      }
                                    }}
                                    className="flex items-center gap-2"
                                  >
                                    <RefreshCw className="h-4 w-4" />
                                    Сгенерировать план питания
                                  </Button>
                                </div>
                              );
                            })()}
                          </>
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
}

export default NutritionistAssistant; 