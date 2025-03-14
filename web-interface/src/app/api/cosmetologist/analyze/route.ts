import { NextResponse } from 'next/server';

/**
 * API-маршрут для анализа кожи и получения рекомендаций по косметике
 */
export async function POST(request: Request) {
  try {
    // Получаем данные из запроса
    const userData = await request.json();
    
    console.log('Получены данные пользователя:', userData);
    
    // Проверяем наличие обязательных полей
    if (!userData.skinType) {
      return NextResponse.json({ error: 'Не указан тип кожи' }, { status: 400 });
    }
    
    try {
      // Формируем запрос к бэкенду Python
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
      
      // Отправляем запрос к бэкенду для определения потребностей пользователя
      const response = await fetch(`${backendUrl}/determine_user_needs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'web-user', // Можно использовать сессию или cookie для идентификации пользователя
          role: 'косметолог',
          user_input: generateUserInput(userData),
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при запросе к бэкенду: ${response.status}`);
      }
      
      const backendData = await response.json();
      
      // Формируем данные для анализа кожи на основе определенных потребностей
      const skinAnalysis = generateSkinAnalysis(userData, backendData);
      
      // Формируем запрос к бэкенду для поиска рекомендуемых продуктов
      const productsResponse = await fetch(`${backendUrl}/find_similar_products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: generateProductSearchQuery(userData, backendData),
          limit: 8,
          min_price: userData.budget ? userData.budget * 0.1 : undefined,
          max_price: userData.budget || undefined,
        }),
      });
      
      let recommendedProducts = [];
      
      if (productsResponse.ok) {
        recommendedProducts = await productsResponse.json();
      }
      
      // Возвращаем результаты анализа и рекомендуемые продукты
      return NextResponse.json({
        success: true,
        skinAnalysis,
        recommendedProducts,
        identifiedNeeds: backendData.identified_needs || {},
      });
      
    } catch (error) {
      console.error('Ошибка при запросе к бэкенду:', error);
      
      // Создаем заглушку для анализа кожи и рекомендаций
      return NextResponse.json({
        success: false,
        error: 'Ошибка при запросе к бэкенду',
        // Возвращаем заглушку для анализа кожи
        skinAnalysis: generateFallbackSkinAnalysis(userData),
        recommendedProducts: [], // Фронтенд использует моковые данные при пустом массиве
      });
    }
    
  } catch (error) {
    console.error('Ошибка при обработке запроса:', error);
    return NextResponse.json({ error: 'Ошибка при обработке запроса' }, { status: 500 });
  }
}

/**
 * Генерирует текстовый ввод для API на основе данных пользователя
 */
function generateUserInput(userData: any): string {
  let input = `Мой тип кожи: ${getSkinTypeName(userData.skinType)}. `;
  
  if (userData.concerns && userData.concerns.length > 0) {
    input += `Меня беспокоит: ${userData.concerns.join(', ')}. `;
  }
  
  if (userData.age) {
    input += `Мой возраст: ${userData.age} лет. `;
  }
  
  if (userData.lifestyles && userData.lifestyles.length > 0) {
    const lifestyleMap: Record<string, string> = {
      'active': 'активный образ жизни',
      'office': 'работа в офисе',
      'sport': 'занятия спортом',
      'travel': 'частые путешествия'
    };
    
    const lifestyles = userData.lifestyles.map((id: string) => lifestyleMap[id] || id);
    input += `Мой образ жизни: ${lifestyles.join(', ')}. `;
  }
  
  if (userData.currentProducts) {
    input += `Сейчас я использую: ${userData.currentProducts}. `;
  }
  
  if (userData.allergies) {
    input += `У меня аллергия на: ${userData.allergies}. `;
  }
  
  return input;
}

/**
 * Получает название типа кожи по идентификатору
 */
function getSkinTypeName(skinTypeId: string): string {
  const skinTypeMap: Record<string, string> = {
    'normal': 'нормальная',
    'dry': 'сухая',
    'oily': 'жирная',
    'combination': 'комбинированная',
    'sensitive': 'чувствительная'
  };
  
  return skinTypeMap[skinTypeId] || skinTypeId;
}

/**
 * Генерирует запрос для поиска продуктов на основе данных пользователя
 */
function generateProductSearchQuery(userData: any, backendData: any): string {
  const skinType = getSkinTypeName(userData.skinType);
  
  let query = `косметика для ${skinType} кожи`;
  
  if (userData.concerns && userData.concerns.length > 0) {
    const concernsMap: Record<string, string> = {
      'aging': 'антивозрастная',
      'acne': 'против акне',
      'pigmentation': 'от пигментации',
      'redness': 'от покраснений',
      'dryness': 'увлажняющая',
      'oiliness': 'матирующая'
    };
    
    const concernTerms = userData.concerns
      .map((id: string) => concernsMap[id] || id)
      .filter(Boolean);
    
    if (concernTerms.length > 0) {
      query += ` ${concernTerms.join(' ')}`;
    }
  }
  
  if (userData.organic_only || (backendData?.identified_needs?.organic_only)) {
    query += ' органическая натуральная';
  }
  
  return query;
}

/**
 * Генерирует структуру анализа кожи на основе данных пользователя
 */
function generateSkinAnalysis(userData: any, backendData: any): any {
  // Используем данные из backend, если они доступны
  const identifiedNeeds = backendData?.identified_needs || {};
  
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
  
  if (userData.concerns?.includes('acne')) {
    analysisDescription += ' Высыпания указывают на необходимость противовоспалительных компонентов.';
  }
  
  if (userData.concerns?.includes('pigmentation')) {
    analysisDescription += ' Пигментация требует средств, выравнивающих тон кожи.';
  }
  
  // Если есть рекомендации от бэкенда, добавляем их
  const backendDescription = backendData?.description || '';
  if (backendDescription) {
    analysisDescription += ' ' + backendDescription;
  }
  
  // Формируем структуру анализа кожи
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
}

/**
 * Генерирует заглушку для анализа кожи при ошибке бэкенда
 */
function generateFallbackSkinAnalysis(userData: any): any {
  return generateSkinAnalysis(userData, {});
}