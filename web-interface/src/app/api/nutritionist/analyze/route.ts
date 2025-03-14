import { NextResponse } from 'next/server';

/**
 * API-маршрут для анализа питания и получения рекомендаций
 */
export async function POST(request: Request) {
  try {
    // Получаем данные из запроса
    const userData = await request.json();
    
    console.log('Получены данные пользователя для нутрициолога:', userData);
    
    // Проверяем наличие обязательных полей
    if (!userData.goal) {
      return NextResponse.json({ error: 'Не указана цель питания' }, { status: 400 });
    }
    
    try {
      // Формируем запрос к бэкенду Python
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
      
      // Отправляем запрос к бэкенду для определения потребностей пользователя
      const response = await fetch(`${backendUrl}/api/nutritionist/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'web-user', // Можно использовать сессию или cookie для идентификации пользователя
          goal: userData.goal,
          restrictions: userData.restrictions || [],
          personalInfo: userData.personalInfo || {},
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при запросе к бэкенду: ${response.status}`);
      }
      
      const backendData = await response.json();
      
      // Формируем данные для анализа питания на основе определенных потребностей
      const nutritionAnalysis = generateNutritionAnalysis(userData, backendData);
      
      // Формируем запрос к бэкенду для поиска рекомендуемых продуктов
      const productsResponse = await fetch(`${backendUrl}/api/search-products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: generateProductSearchQuery(userData, backendData),
          limit: 8,
          category: "products",
          min_price: userData.personalInfo?.budget ? userData.personalInfo.budget * 0.1 : undefined,
          max_price: userData.personalInfo?.budget || undefined,
        }),
      });
      
      let recommendedProducts = [];
      
      if (productsResponse.ok) {
        recommendedProducts = await productsResponse.json();
      }
      
      // Возвращаем результаты анализа и рекомендуемые продукты
      return NextResponse.json({
        success: true,
        nutritionAnalysis,
        recommendedProducts,
        identifiedNeeds: backendData.identified_needs || {},
      });
      
    } catch (error) {
      console.error('Ошибка при запросе к бэкенду:', error);
      
      // Создаем заглушку для анализа питания и рекомендаций
      return NextResponse.json({
        success: false,
        error: 'Ошибка при запросе к бэкенду',
        // Возвращаем заглушку для анализа питания
        nutritionAnalysis: generateFallbackNutritionAnalysis(userData),
        recommendedProducts: [], // Фронтенд использует моковые данные при пустом массиве
      });
    }
    
  } catch (error) {
    console.error('Ошибка при обработке запроса:', error);
    return NextResponse.json({ error: 'Ошибка при обработке запроса' }, { status: 500 });
  }
}

/**
 * Генерирует запрос для поиска продуктов на основе данных пользователя
 */
function generateProductSearchQuery(userData: any, backendData: any): string {
  const goal = getDietaryGoalName(userData.goal);
  
  let query = `продукты для ${goal}`;
  
  if (userData.restrictions && userData.restrictions.length > 0) {
    const restrictionsMap: Record<string, string> = {
      'vegetarian': 'вегетарианское',
      'vegan': 'веганское',
      'gluten_free': 'без глютена',
      'lactose_free': 'без лактозы',
      'diabetes': 'диабетическое'
    };
    
    const restrictionTerms = userData.restrictions
      .map((id: string) => restrictionsMap[id] || id)
      .filter(Boolean);
    
    if (restrictionTerms.length > 0) {
      query += ` ${restrictionTerms.join(' ')}`;
    }
  }
  
  return query;
}

/**
 * Получает название цели питания по идентификатору
 */
function getDietaryGoalName(goalId: string): string {
  const goalMap: Record<string, string> = {
    'weight_loss': 'похудение',
    'muscle_gain': 'набор мышечной массы',
    'health': 'здоровое питание',
    'energy': 'повышение энергии',
    'special': 'особых потребностей'
  };
  
  return goalMap[goalId] || goalId;
}

/**
 * Генерирует структуру анализа питания на основе данных пользователя
 */
function generateNutritionAnalysis(userData: any, backendData: any): any {
  // Используем данные из backend, если они доступны
  const identifiedNeeds = backendData?.identified_needs || {};
  
  // Рассчитываем базовые параметры
  const personalInfo = userData.personalInfo || {};
  const { age, weight, height, activity } = personalInfo;
  
  // Рассчитываем BMR по формуле Миффлина-Сан Жеора
  let bmr = 0;
  if (age && weight && height) {
    // Формула для мужчин (можно расширить с учетом пола)
    bmr = 10 * Number(weight) + 6.25 * Number(height) - 5 * Number(age) + 5;
  } else {
    // Если недостаточно данных, используем среднее значение
    bmr = 1800;
  }
  
  // Коэффициент активности
  const activityMultipliers: Record<string, number> = {
    low: 1.2,
    medium: 1.55,
    high: 1.725
  };
  
  const tdee = bmr * (activityMultipliers[activity as keyof typeof activityMultipliers] || 1.55);
  
  // Корректировка в зависимости от цели
  const goalMultipliers: Record<string, number> = {
    weight_loss: 0.85,
    muscle_gain: 1.1,
    health: 1,
    energy: 1,
    special: 1
  };
  
  const dailyCalories = Math.round(tdee * (goalMultipliers[userData.goal as keyof typeof goalMultipliers] || 1));
  
  // Расчет макронутриентов
  let proteinRatio = 0.3;
  let fatRatio = 0.3;
  let carbRatio = 0.4;
  
  if (userData.goal === 'weight_loss') {
    proteinRatio = 0.35;
    fatRatio = 0.35;
    carbRatio = 0.3;
  } else if (userData.goal === 'muscle_gain') {
    proteinRatio = 0.35;
    fatRatio = 0.25;
    carbRatio = 0.4;
  }
  
  const proteins = Math.round(dailyCalories * proteinRatio / 4); // 4 ккал/г белка
  const fats = Math.round(dailyCalories * fatRatio / 9); // 9 ккал/г жира
  const carbs = Math.round(dailyCalories * carbRatio / 4); // 4 ккал/г углеводов
  
  // Описание плана питания
  let description = `Ваш оптимальный рацион составляет ${dailyCalories} ккал в день с распределением БЖУ: ${Math.round(proteinRatio * 100)}% белков, ${Math.round(fatRatio * 100)}% жиров, ${Math.round(carbRatio * 100)}% углеводов.`;
  
  if (userData.goal === 'weight_loss') {
    description += ' Для похудения важно соблюдать дефицит калорий и увеличить потребление белка для сохранения мышечной массы.';
  } else if (userData.goal === 'muscle_gain') {
    description += ' Для набора мышечной массы необходим профицит калорий и достаточное количество белка.';
  }
  
  // Если у пользователя есть ограничения в питании
  if (userData.restrictions && userData.restrictions.length > 0) {
    if (userData.restrictions.includes('vegetarian')) {
      description += ' Учтены вегетарианские предпочтения в питании.';
    }
    if (userData.restrictions.includes('vegan')) {
      description += ' Учтены веганские предпочтения в питании.';
    }
    if (userData.restrictions.includes('gluten_free')) {
      description += ' Исключены продукты, содержащие глютен.';
    }
    if (userData.restrictions.includes('lactose_free')) {
      description += ' Исключены продукты, содержащие лактозу.';
    }
    if (userData.restrictions.includes('diabetes')) {
      description += ' Учтены особенности питания при диабете.';
    }
  }
  
  // Формируем структуру анализа питания
  return {
    description,
    dailyNutrition: {
      calories: dailyCalories,
      macros: {
        proteins,
        fats,
        carbs,
        proteinRatio: Math.round(proteinRatio * 100),
        fatRatio: Math.round(fatRatio * 100),
        carbRatio: Math.round(carbRatio * 100)
      }
    },
    mealPlan: {
      breakfast: {
        title: 'Завтрак',
        calories: Math.round(dailyCalories * 0.25),
        description: 'Оптимальное время: 7:00-9:00',
        recommendations: [
          'Сложные углеводы для энергии',
          'Белок для насыщения',
          'Клетчатка для пищеварения'
        ]
      },
      lunch: {
        title: 'Обед',
        calories: Math.round(dailyCalories * 0.35),
        description: 'Оптимальное время: 12:00-14:00',
        recommendations: [
          'Основной источник белка',
          'Сложные углеводы',
          'Овощи для витаминов'
        ]
      },
      dinner: {
        title: 'Ужин',
        calories: Math.round(dailyCalories * 0.30),
        description: 'Оптимальное время: 18:00-20:00',
        recommendations: [
          'Легкоусвояемый белок',
          'Минимум углеводов',
          'Полезные жиры'
        ]
      },
      snacks: {
        title: 'Перекусы',
        calories: Math.round(dailyCalories * 0.10),
        description: 'Между основными приемами пищи',
        recommendations: [
          'Фрукты и орехи',
          'Протеиновые снеки',
          'Овощные нарезки'
        ]
      }
    },
    recommendations: {
      lifestyle: [
        { text: 'Пить не менее 2 литров воды в день' },
        { text: 'Соблюдать режим питания и не пропускать приемы пищи' },
        { text: 'Готовить еду на пару, запекать или тушить вместо жарки' },
        { text: 'Ограничить потребление соли и сахара' },
        { text: 'Включать в рацион сезонные овощи и фрукты' }
      ],
      ingredients: [
        { name: 'Белки', sources: 'Нежирное мясо, рыба, яйца, бобовые' },
        { name: 'Сложные углеводы', sources: 'Цельнозерновые крупы, овощи, бобовые' },
        { name: 'Полезные жиры', sources: 'Авокадо, орехи, оливковое масло, жирная рыба' },
        { name: 'Клетчатка', sources: 'Овощи, фрукты, цельные злаки, отруби' },
        { name: 'Витамины и микроэлементы', sources: 'Разноцветные овощи и фрукты, зелень' }
      ]
    }
  };
}

/**
 * Генерирует заглушку для анализа питания при ошибке
 */
function generateFallbackNutritionAnalysis(userData: any): any {
  // Базовые значения для заглушки
  const dailyCalories = 2000;
  const proteins = 150;
  const fats = 67;
  const carbs = 200;
  
  return {
    description: 'Примерный план питания. Для получения точных рекомендаций обратитесь к нутрициологу.',
    dailyNutrition: {
      calories: dailyCalories,
      macros: {
        proteins,
        fats,
        carbs,
        proteinRatio: 30,
        fatRatio: 30,
        carbRatio: 40
      }
    },
    mealPlan: {
      breakfast: {
        title: 'Завтрак',
        calories: 500,
        description: 'Оптимальное время: 7:00-9:00',
        recommendations: [
          'Сложные углеводы для энергии',
          'Белок для насыщения',
          'Клетчатка для пищеварения'
        ]
      },
      lunch: {
        title: 'Обед',
        calories: 700,
        description: 'Оптимальное время: 12:00-14:00',
        recommendations: [
          'Основной источник белка',
          'Сложные углеводы',
          'Овощи для витаминов'
        ]
      },
      dinner: {
        title: 'Ужин',
        calories: 600,
        description: 'Оптимальное время: 18:00-20:00',
        recommendations: [
          'Легкоусвояемый белок',
          'Минимум углеводов',
          'Полезные жиры'
        ]
      },
      snacks: {
        title: 'Перекусы',
        calories: 200,
        description: 'Между основными приемами пищи',
        recommendations: [
          'Фрукты и орехи',
          'Протеиновые снеки',
          'Овощные нарезки'
        ]
      }
    },
    recommendations: {
      lifestyle: [
        { text: 'Пить не менее 2 литров воды в день' },
        { text: 'Соблюдать режим питания и не пропускать приемы пищи' },
        { text: 'Готовить еду на пару, запекать или тушить вместо жарки' },
        { text: 'Ограничить потребление соли и сахара' },
        { text: 'Включать в рацион сезонные овощи и фрукты' }
      ],
      ingredients: [
        { name: 'Белки', sources: 'Нежирное мясо, рыба, яйца, бобовые' },
        { name: 'Сложные углеводы', sources: 'Цельнозерновые крупы, овощи, бобовые' },
        { name: 'Полезные жиры', sources: 'Авокадо, орехи, оливковое масло, жирная рыба' },
        { name: 'Клетчатка', sources: 'Овощи, фрукты, цельные злаки, отруби' },
        { name: 'Витамины и микроэлементы', sources: 'Разноцветные овощи и фрукты, зелень' }
      ]
    }
  };
} 