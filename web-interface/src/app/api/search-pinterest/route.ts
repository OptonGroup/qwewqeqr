import { NextRequest, NextResponse } from 'next/server';

// Интерфейс для результата поиска в Pinterest
interface PinterestSearchResult {
  pin_id: string;
  title: string;
  description: string;
  image_url: string;
  link: string;
  clothing_items: ClothingItem[];
  gender?: 'male' | 'female';
}

// Интерфейс для предмета одежды
interface ClothingItem {
  id: string;       // Уникальный идентификатор
  type: string;     // Тип предмета (футболка, джинсы и т.д.)
  color: string;    // Цвет предмета
  description: string; // Описание (принт, фасон и т.д.)
  gender: 'male' | 'female'; // Пол (мужской, женский)
}

// Путь к Python API
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// Кэширование результатов поиска
const resultsCache = new Map<string, { timestamp: number, results: PinterestSearchResult[] }>();
const CACHE_TTL = 3600000; // 1 час в миллисекундах

/**
 * Получает резервные результаты при проблемах с API
 */
function getFallbackResults(query: string, gender: string): PinterestSearchResult[] {
  const cacheKey = `${query.toLowerCase()}-${gender}`;
  
  // Проверяем кэш
  if (resultsCache.has(cacheKey)) {
    const cachedData = resultsCache.get(cacheKey)!;
    const now = Date.now();
    
    // Если кэш не устарел, используем его
    if (now - cachedData.timestamp < CACHE_TTL) {
      console.log(`Используем кэшированные данные для запроса "${query}"`);
      return cachedData.results;
    }
  }

  // Ключевые слова для разных типов запросов
  const keywords = {
    basic: ['простой', 'базовый', 'классический', 'повседневный'],
    casual: ['кэжуал', 'повседневный', 'casual', 'на каждый день'],
    formal: ['формальный', 'деловой', 'офисный', 'строгий', 'на работу'],
    evening: ['вечерний', 'нарядный', 'выход', 'на вечеринку'],
    sport: ['спортивный', 'спорт', 'тренировка', 'фитнес'],
    beach: ['пляжный', 'на пляж', 'летний', 'для отпуска'],
    winter: ['зимний', 'теплый', 'холодный', 'для зимы']
  };
  
  // Определяем тип запроса на основе ключевых слов
  let outfitType = 'basic';
  const queryLower = query.toLowerCase();
  
  for (const [type, typeKeywords] of Object.entries(keywords)) {
    if (typeKeywords.some(keyword => queryLower.includes(keyword))) {
      outfitType = type;
      break;
    }
  }
  
  // Словарь заготовленных образов по типам
  const outfits: Record<string, PinterestSearchResult[]> = {
    basic: getFallbackOutfits('basic', gender),
    casual: getFallbackOutfits('casual', gender),
    formal: getFallbackOutfits('formal', gender),
    evening: getFallbackOutfits('evening', gender),
    sport: getFallbackOutfits('sport', gender),
    beach: getFallbackOutfits('beach', gender),
    winter: getFallbackOutfits('winter', gender)
  };

  // Возвращаем соответствующие образы (или базовые, если тип не определен)
  const results = outfits[outfitType] || outfits.basic;
  
  // Сохраняем результаты в кэш
  resultsCache.set(cacheKey, {
    timestamp: Date.now(),
    results
  });
  
  console.log(`Возвращаем резервные данные типа "${outfitType}" для запроса "${query}"`);
  return results;
}

/**
 * Создает заготовленные образы для разных типов и гендера
 */
function getFallbackOutfits(type: string, gender: string): PinterestSearchResult[] {
  const genderSpecific = gender === 'male' ? 'мужской' : gender === 'female' ? 'женский' : 'унисекс';
  
  // Базовый шаблон для результатов
  const baseOutfits: Partial<PinterestSearchResult>[] = [
    {
      pin_id: `fallback-${type}-1`,
      title: `${capitalizeFirstLetter(type)} ${genderSpecific} образ 1`,
      description: `${capitalizeFirstLetter(genderSpecific)} ${type} образ с Pinterest. Резервные данные.`,
      image_url: `/images/fallback/${gender}/${type}-1.jpg`,
      link: `https://pinterest.com/fallback/${gender}/${type}-1`,
      gender: gender === 'any' ? undefined : gender
    },
    {
      pin_id: `fallback-${type}-2`,
      title: `${capitalizeFirstLetter(type)} ${genderSpecific} образ 2`,
      description: `${capitalizeFirstLetter(genderSpecific)} ${type} образ с Pinterest. Резервные данные.`,
      image_url: `/images/fallback/${gender}/${type}-2.jpg`,
      link: `https://pinterest.com/fallback/${gender}/${type}-2`,
      gender: gender === 'any' ? undefined : gender
    },
    {
      pin_id: `fallback-${type}-3`,
      title: `${capitalizeFirstLetter(type)} ${genderSpecific} образ 3`,
      description: `${capitalizeFirstLetter(genderSpecific)} ${type} образ с Pinterest. Резервные данные.`,
      image_url: `/images/fallback/${gender}/${type}-3.jpg`,
      link: `https://pinterest.com/fallback/${gender}/${type}-3`,
      gender: gender === 'any' ? undefined : gender
    }
  ];
  
  // Возвращаем результаты как полные объекты PinterestSearchResult
  return baseOutfits.map(outfit => ({
    pin_id: outfit.pin_id || `fallback-${Date.now()}`,
    title: outfit.title || 'Резервный образ',
    description: outfit.description || 'Описание отсутствует',
    image_url: outfit.image_url || '/images/fallback/no-image.jpg',
    link: outfit.link || 'https://pinterest.com',
    clothing_items: getClothingItemsForType(type, gender),
    gender: outfit.gender as 'male' | 'female' | undefined
  }));
}

/**
 * Возвращает предметы одежды для конкретного типа образа и гендера
 */
function getClothingItemsForType(type: string, gender: string): ClothingItem[] {
  // Предметы одежды для разных типов образов
  const clothingByType: Record<string, Record<string, string[]>> = {
    basic: {
      male: ['Базовая футболка', 'Джинсы классические', 'Кеды белые'],
      female: ['Базовая футболка', 'Джинсы с высокой посадкой', 'Кеды белые']
    },
    casual: {
      male: ['Футболка с принтом', 'Джинсы свободного кроя', 'Кроссовки'],
      female: ['Блузка', 'Джинсы скинни', 'Лоферы']
    },
    formal: {
      male: ['Рубашка белая', 'Брюки классические', 'Туфли кожаные'],
      female: ['Блузка строгая', 'Юбка-карандаш', 'Туфли на каблуке']
    },
    evening: {
      male: ['Рубашка темная', 'Брюки темные', 'Туфли лакированные'],
      female: ['Платье вечернее', 'Туфли на шпильке', 'Клатч']
    },
    sport: {
      male: ['Футболка спортивная', 'Шорты спортивные', 'Кроссовки беговые'],
      female: ['Топ спортивный', 'Леггинсы', 'Кроссовки беговые']
    },
    beach: {
      male: ['Футболка легкая', 'Шорты пляжные', 'Сандалии'],
      female: ['Сарафан легкий', 'Шляпа пляжная', 'Сандалии']
    },
    winter: {
      male: ['Свитер теплый', 'Джинсы утепленные', 'Ботинки зимние', 'Куртка'],
      female: ['Свитер теплый', 'Джинсы утепленные', 'Сапоги зимние', 'Пуховик']
    }
  };
  
  // Определяем гендер для получения предметов
  const genderKey = gender === 'male' ? 'male' : 
                   gender === 'female' ? 'female' : 
                   Math.random() > 0.5 ? 'male' : 'female';
  
  // Получаем предметы для типа и гендера (или базовые, если тип не определен)
  const items = clothingByType[type]?.[genderKey] || clothingByType.basic[genderKey];
  
  // Создаем объекты ClothingItem
  return items.map((item, index) => ({
    id: `${type}-${genderKey}-${index}`,
    type: getItemType(item),
    description: item,
    color: getItemColor(item),
    gender: genderKey as 'male' | 'female'
  }));
}

/**
 * Определяет тип предмета одежды по описанию
 */
function getItemType(description: string): string {
  const typeMap: Record<string, string[]> = {
    'top': ['футболка', 'рубашка', 'блузка', 'топ', 'свитер', 'пуловер', 'худи'],
    'bottom': ['джинсы', 'брюки', 'шорты', 'юбка', 'леггинсы'],
    'dress': ['платье', 'сарафан'],
    'outerwear': ['куртка', 'пальто', 'плащ', 'пуховик'],
    'shoes': ['кеды', 'кроссовки', 'туфли', 'ботинки', 'сапоги', 'сандалии', 'лоферы'],
    'accessory': ['шляпа', 'шапка', 'шарф', 'клатч', 'сумка']
  };
  
  const descLower = description.toLowerCase();
  
  for (const [type, keywords] of Object.entries(typeMap)) {
    if (keywords.some(keyword => descLower.includes(keyword))) {
      return type;
    }
  }
  
  // Если тип не определен, возвращаем "other"
  return 'other';
}

/**
 * Определяет цвет предмета одежды по описанию
 */
function getItemColor(description: string): string {
  const colorMap: Record<string, string[]> = {
    'black': ['черный', 'черная', 'черное'],
    'white': ['белый', 'белая', 'белое', 'белые'],
    'red': ['красный', 'красная', 'красное'],
    'blue': ['синий', 'синяя', 'синее', 'голубой'],
    'green': ['зеленый', 'зеленая', 'зеленое'],
    'yellow': ['желтый', 'желтая', 'желтое'],
    'gray': ['серый', 'серая', 'серое'],
    'beige': ['бежевый', 'бежевая', 'бежевое'],
    'brown': ['коричневый', 'коричневая', 'коричневое'],
    'pink': ['розовый', 'розовая', 'розовое']
  };
  
  const descLower = description.toLowerCase();
  
  for (const [color, keywords] of Object.entries(colorMap)) {
    if (keywords.some(keyword => descLower.includes(keyword))) {
      return color;
    }
  }
  
  // Если цвет не определен, возвращаем пустую строку
  return '';
}

/**
 * Делает первую букву строки заглавной
 */
function capitalizeFirstLetter(string: string): string {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

// Проверка доступности Python API
async function checkApiAvailability() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);  // Увеличиваем таймаут до 5 секунд
    
    const response = await fetch(`${PYTHON_API_URL}/health`, { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    console.error('Ошибка при проверке доступности API:', error);
    return false;
  }
}

// Функция для поиска образов в Pinterest через Python API
async function searchPinterestViaAPI(query: string, gender: string, limit: number): Promise<PinterestSearchResult[]> {
  try {
    // Отправляем запрос на поиск
    console.log(`Отправляем запрос на поиск в Pinterest: ${query}, пол: ${gender}, лимит: ${limit}`);
    
    // Объявляем taskId перед блоком try
    let taskId: string | undefined;
    
    // Увеличиваем таймаут до 120 секунд для более надежного выполнения запроса
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log("Прерываем запрос из-за таймаута (120 секунд)");
      controller.abort();
    }, 120000); // 2 минуты вместо 60 секунд
    
    try {
      const searchResponse = await fetch(`${PYTHON_API_URL}/search-pinterest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          gender,
          num_results: limit
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
  
      if (!searchResponse.ok) {
        console.error(`Ошибка API при поиске: ${searchResponse.status} - ${searchResponse.statusText}`);
        const errorText = await searchResponse.text();
        console.error(`Детали ошибки: ${errorText}`);
        console.log("Возвращаем резервные данные из-за ошибки API");
        return getFallbackResults(query, gender);
      }
  
      // Получаем ID задачи
      const searchData = await searchResponse.json();
      taskId = searchData.task_id;
      
      if (!taskId) {
        console.error('API не вернул идентификатор задачи');
        console.log("Возвращаем резервные данные из-за отсутствия task_id");
        return getFallbackResults(query, gender);
      }
      
      console.log(`Получен идентификатор задачи: ${taskId}, статус: ${searchData.status}`);
      
      // Если задача уже завершена, возвращаем результаты
      if (searchData.status === 'completed' && searchData.results) {
        console.log(`Задача ${taskId} уже завершена, получено ${searchData.results.length} результатов`);
        return searchData.results;
      }
    } catch (fetchError) {
      clearTimeout(timeoutId);
      console.error("Ошибка при выполнении запроса на поиск:", fetchError);
      if (fetchError.name === 'AbortError') {
        console.log("Запрос был прерван из-за таймаута");
      }
      console.log("Возвращаем резервные данные из-за ошибки запроса");
      return getFallbackResults(query, gender);
    }
    
    // Проверяем, что taskId был получен
    if (!taskId) {
      console.error('Не удалось получить идентификатор задачи после запроса');
      return getFallbackResults(query, gender);
    }
    
    // Ожидаем завершения задачи (с таймаутом)
    let attempts = 0;
    const maxAttempts = 90; // Увеличиваем до 90 секунд максимум
    
    while (attempts < maxAttempts) {
      attempts++;
      
      // Делаем паузу перед следующим запросом
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Проверяем статус задачи с отдельным таймаутом
      const statusController = new AbortController();
      const statusTimeoutId = setTimeout(() => {
        console.log(`Прерываем запрос статуса на попытке ${attempts} из-за таймаута`);
        statusController.abort();
      }, 10000); // 10 секунд
      
      try {
        const statusResponse = await fetch(`${PYTHON_API_URL}/search-pinterest/${taskId}`, {
          method: 'GET',
          signal: statusController.signal
        });
        
        clearTimeout(statusTimeoutId);
        
        if (!statusResponse.ok) {
          console.error(`Ошибка при проверке статуса задачи: ${statusResponse.status} ${statusResponse.statusText}`);
          continue;
        }
        
        const statusData = await statusResponse.json();
        console.log(`Статус задачи (попытка ${attempts}): ${statusData.status}, прогресс: ${statusData.progress}%`);
        
        if (statusData.status === 'completed' && statusData.results) {
          console.log(`Задача ${taskId} завершена, получено ${statusData.results.length} результатов`);
          return statusData.results;
        } else if (statusData.status === 'failed') {
          console.error(`Задача завершилась с ошибкой: ${statusData.message}`);
          console.log("Возвращаем резервные данные из-за ошибки задачи");
          return getFallbackResults(query, gender);
        }
      } catch (error) {
        clearTimeout(statusTimeoutId);
        console.error(`Ошибка при проверке статуса задачи (попытка ${attempts}):`, error);
        if (error.name === 'AbortError') {
          console.log("Запрос статуса был прерван из-за таймаута");
        }
        // Продолжаем попытки, не прерывая цикл
      }
      
      // Если достигли максимального количества попыток
      if (attempts === maxAttempts) {
        console.error('Превышено максимальное время ожидания результатов');
        console.log("Возвращаем резервные данные из-за истечения времени ожидания");
        return getFallbackResults(query, gender);
      }
    }
    
    console.log("Возвращаем резервные данные по завершении цикла");
    return getFallbackResults(query, gender);
  } catch (error) {
    console.error('Ошибка при поиске образов в Pinterest:', error);
    if (error.name === 'AbortError') {
      console.log("Операция была прервана из-за таймаута");
    }
    console.log("Возвращаем резервные данные из-за общей ошибки");
    return getFallbackResults(query, gender);
  }
}

export async function GET(request: NextRequest) {
  try {
    // Проверяем параметры запроса
    const query = request.nextUrl.searchParams.get('query');
    const gender = request.nextUrl.searchParams.get('gender') || 'any';
    const limit = parseInt(request.nextUrl.searchParams.get('limit') || '10', 10);

    // Если запрос пустой, возвращаем ошибку
    if (!query) {
      console.error('Отсутствует обязательный параметр query');
      return NextResponse.json({ error: 'Параметр query обязателен' }, { status: 400 });
    }

    console.log(`Поступил запрос на поиск образов: ${query}, пол: ${gender}, лимит: ${limit}`);
    
    let results: PinterestSearchResult[] = [];
    const requestStartTime = Date.now();

    try {
      // Проверяем доступность Python API
      const isApiAvailable = await checkApiAvailability();
      console.log(`Python API доступен: ${isApiAvailable}`);

      // Если API доступно, используем его для поиска товаров
      if (isApiAvailable) {
        console.log(`Выполняем поиск через API: ${query}, пол: ${gender}, лимит: ${limit}`);
        try {
          results = await searchPinterestViaAPI(query, gender, limit);
          console.log(`Получено ${results.length} образов от API`);
        } catch (apiError) {
          console.error('Ошибка при поиске через API:', apiError);
          if (apiError.name === 'AbortError') {
            console.log('Запрос был прерван из-за таймаута. Используем резервные данные');
          } else {
            console.log('Ошибка API. Используем резервные данные');
          }
          results = getFallbackResults(query, gender);
        }
      } else {
        // Если API недоступно, используем резервные данные
        console.log(`API недоступно, используем резервные данные для ${query}`);
        results = getFallbackResults(query, gender);
        console.log(`Сгенерировано ${results.length} образов из резервных данных`);
      }

      // Если результатов нет, используем резервные данные
      if (!results || results.length === 0) {
        console.log(`Не получено результатов от API, используем резервные данные`);
        results = getFallbackResults(query, gender);
      }

      const requestDuration = Date.now() - requestStartTime;
      console.log(`Запрос обработан за ${requestDuration}ms, возвращаем ${results.length} образов`);

      // Возвращаем результаты поиска
      return NextResponse.json(results);
    } catch (innerError) {
      console.error('Внутренняя ошибка при обработке запроса:', innerError);
      if (innerError.name === 'AbortError') {
        console.log('Запрос был прерван из-за таймаута в процессе обработки');
      }
      
      // В случае внутренней ошибки возвращаем резервные данные
      const fallbackResults = getFallbackResults(query, gender);
      return NextResponse.json(fallbackResults);
    }
  } catch (error) {
    console.error('Критическая ошибка при обработке запроса:', error);
    
    try {
      // В случае критической ошибки пытаемся вернуть хоть какие-то данные
      const query = request.nextUrl.searchParams.get('query') || '';
      const gender = request.nextUrl.searchParams.get('gender') || 'any';
      const fallbackResults = getFallbackResults(query, gender);
      
      return NextResponse.json(fallbackResults);
    } catch (fallbackError) {
      // Если даже резервные данные не удалось получить, возвращаем пустой массив и сообщение об ошибке
      console.error('Не удалось получить даже резервные данные:', fallbackError);
      return NextResponse.json({ error: 'Внутренняя ошибка сервера', results: [] }, { status: 500 });
    }
  }
} 