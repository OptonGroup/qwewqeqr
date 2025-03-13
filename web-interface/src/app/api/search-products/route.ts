import { NextRequest, NextResponse } from 'next/server';

// Интерфейс для товара Wildberries
interface WildberriesProduct {
  id: string;
  name: string;
  brand: string;
  price: number;
  priceWithDiscount: number;
  imageUrl: string;
  imageUrls?: string[]; // Опциональный массив альтернативных URL изображений
  url: string;
  rating?: number;
  category?: string;
}

// Путь к Python API
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// Проверка доступности Python API
async function checkApiAvailability() {
  try {
    const response = await fetch(`${PYTHON_API_URL}/health`, { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(3000) // Таймаут 3 секунды
    });
    return response.ok;
  } catch (error) {
    console.error('Ошибка при проверке доступности API:', error);
    return false;
  }
}

// Заглушка для тестирования, в реальном приложении здесь должен быть вызов к бэкенду
const mockProducts: WildberriesProduct[] = [
  {
    id: '1001',
    name: 'Футболка хлопковая базовая',
    brand: 'ТВОЕ',
    price: 999,
    priceWithDiscount: 699,
    imageUrl: 'https://basket-01.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-01.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/1.webp',
      'https://basket-02.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/2.webp',
      'https://basket-03.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/100135766/detail.aspx',
    rating: 4.8,
    category: 'Футболки'
  },
  {
    id: '1002',
    name: 'Футболка оверсайз женская',
    brand: 'ZARA',
    price: 1499,
    priceWithDiscount: 1299,
    imageUrl: 'https://basket-05.wbbasket.ru/vol1002/part100245/100245387/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-05.wbbasket.ru/vol1002/part100245/100245387/images/c516x688/1.webp',
      'https://basket-06.wbbasket.ru/vol1002/part100245/100245387/images/c516x688/2.webp',
      'https://basket-07.wbbasket.ru/vol1002/part100245/100245387/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/100245387/detail.aspx',
    rating: 4.6,
    category: 'Футболки'
  },
  {
    id: '1003',
    name: 'Джинсы классические женские',
    brand: 'Levi\'s',
    price: 5999,
    priceWithDiscount: 4499,
    imageUrl: 'https://basket-13.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-13.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/1.webp',
      'https://basket-12.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/2.webp',
      'https://basket-11.wbbasket.ru/vol1995/part199573/199573766/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/199573766/detail.aspx',
    rating: 4.9,
    category: 'Джинсы'
  },
  {
    id: '1004',
    name: 'Джинсы скинни женские',
    brand: 'ZARA',
    price: 3499,
    priceWithDiscount: 2799,
    imageUrl: 'https://basket-01.wbbasket.ru/vol68/part6898/6898953/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-01.wbbasket.ru/vol68/part6898/6898953/images/c516x688/1.webp',
      'https://basket-02.wbbasket.ru/vol68/part6898/6898953/images/c516x688/2.webp',
      'https://basket-03.wbbasket.ru/vol68/part6898/6898953/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/6898953/detail.aspx',
    rating: 4.7,
    category: 'Джинсы'
  },
  {
    id: '1005',
    name: 'Кожаная куртка женская',
    brand: 'Befree',
    price: 7999,
    priceWithDiscount: 5999,
    imageUrl: 'https://basket-16.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-16.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/1.webp',
      'https://basket-15.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/2.webp',
      'https://basket-14.wbbasket.ru/vol2573/part257301/257301422/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/257301422/detail.aspx',
    rating: 4.5,
    category: 'Верхняя одежда'
  },
  {
    id: '1006',
    name: 'Кеды белые женские',
    brand: 'Adidas',
    price: 4999,
    priceWithDiscount: 3999,
    imageUrl: 'https://basket-05.wbbasket.ru/vol758/part75846/75846387/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-05.wbbasket.ru/vol758/part75846/75846387/images/c516x688/1.webp',
      'https://basket-06.wbbasket.ru/vol758/part75846/75846387/images/c516x688/2.webp',
      'https://basket-07.wbbasket.ru/vol758/part75846/75846387/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/75846387/detail.aspx',
    rating: 4.8,
    category: 'Обувь'
  },
  {
    id: '1007',
    name: 'Платье миди женское',
    brand: 'ASOS Design',
    price: 3999,
    priceWithDiscount: 2799,
    imageUrl: 'https://basket-09.wbbasket.ru/vol456/part45612/45612547/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-09.wbbasket.ru/vol456/part45612/45612547/images/c516x688/1.webp',
      'https://basket-10.wbbasket.ru/vol456/part45612/45612547/images/c516x688/2.webp',
      'https://basket-11.wbbasket.ru/vol456/part45612/45612547/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/45612547/detail.aspx',
    rating: 4.6,
    category: 'Платья'
  },
  {
    id: '1008',
    name: 'Свитер крупной вязки женский',
    brand: 'Mango',
    price: 3499,
    priceWithDiscount: 2799,
    imageUrl: 'https://basket-12.wbbasket.ru/vol358/part35854/35854621/images/c516x688/1.webp',
    imageUrls: [
      'https://basket-12.wbbasket.ru/vol358/part35854/35854621/images/c516x688/1.webp',
      'https://basket-13.wbbasket.ru/vol358/part35854/35854621/images/c516x688/2.webp',
      'https://basket-14.wbbasket.ru/vol358/part35854/35854621/images/c516x688/3.webp'
    ],
    url: 'https://www.wildberries.ru/catalog/35854621/detail.aspx',
    rating: 4.7,
    category: 'Свитеры и кардиганы'
  }
];

export async function GET(request: NextRequest) {
  try {
    // Проверяем доступность Python API
    const isApiAvailable = await checkApiAvailability();
    console.log(`Python API доступен: ${isApiAvailable}`);
    
    // Получаем параметры запроса
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('query') || '';
    const limit = parseInt(searchParams.get('limit') || '10', 10);
    const minPrice = parseFloat(searchParams.get('minPrice') || '0');
    const maxPrice = parseFloat(searchParams.get('maxPrice') || '1000000');
    const gender = searchParams.get('gender') || '';  // Получаем параметр пола

    // Валидация параметров
    if (!query) {
      return NextResponse.json(
        { error: 'Параметр query обязателен' },
        { status: 400 }
      );
    }

    try {
      // Формируем тело запроса для Python API
      const requestBody = {
        query,
        number_of_photos: limit,
        source: 'wildberries',
        gender: gender || 'женский' // Всегда передаем пол, по умолчанию - женский
      };
      
      // Добавляем опциональные параметры только если они заданы
      if (minPrice > 0) {
        requestBody['min_price'] = minPrice;
      }
      
      if (maxPrice < 1000000) {
        requestBody['max_price'] = maxPrice;
      }
      
      console.log(`Отправляем запрос к Python API: ${PYTHON_API_URL}/search`, requestBody);

      // Отправляем POST запрос к Python API с JSON-телом
      const pythonApiResponse = await fetch(`${PYTHON_API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (pythonApiResponse.ok) {
        // Получаем ID задачи
        const responseData = await pythonApiResponse.json();
        console.log('Ответ от Python API:', responseData);
        
        const task_id = responseData.task_id;
        if (!task_id) {
          console.error('API не вернул task_id');
          throw new Error('API не вернул task_id');
        }
        
        // Дожидаемся завершения задачи поиска (с таймаутом 10 секунд)
        let taskResult = null;
        let attempts = 0;
        const maxAttempts = 20;
        
        while (attempts < maxAttempts) {
          attempts++;
          
          // Делаем паузу перед следующим запросом
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Проверяем статус задачи
          const statusResponse = await fetch(`${PYTHON_API_URL}/status/${task_id}`, {
            method: 'GET',
          });
          
          if (!statusResponse.ok) {
            console.error(`Ошибка при проверке статуса задачи: ${statusResponse.status} ${statusResponse.statusText}`);
            continue;
          }
          
          const statusData = await statusResponse.json();
          console.log(`Статус задачи (попытка ${attempts}):`, statusData.status);
          
          if (statusData.status === 'completed') {
            taskResult = statusData;
            break;
          } else if (statusData.status === 'failed') {
            console.error(`Задача завершилась с ошибкой: ${statusData.message}`);
            break;
          }
          
          // Если задача всё ещё выполняется, продолжаем ждать
          if (attempts === maxAttempts) {
            console.error('Превышено максимальное количество попыток проверки статуса задачи');
          }
        }
        
        // Если задача успешно завершена и есть результаты
        if (taskResult && taskResult.product_details && taskResult.product_details.length > 0) {
          console.log(`Найдено ${taskResult.product_details.length} товаров`);
          
          // Преобразуем данные в формат WildberriesProduct
          const products: WildberriesProduct[] = taskResult.product_details.map((product: any) => {
            // Создаем категорию на основе названия товара
            const category = product.name && product.name.toLowerCase().includes('джинсы') ? 'jeans' :
              product.name && product.name.toLowerCase().includes('футболка') ? 'tshirt' :
              product.name && product.name.toLowerCase().includes('куртка') ? 'jacket' :
              product.name && product.name.toLowerCase().includes('платье') ? 'dress' :
              product.name && product.name.toLowerCase().includes('свитер') ? 'sweater' :
              product.name && product.name.toLowerCase().includes('обувь') || product.name && product.name.toLowerCase().includes('кеды') ? 'shoes' : 'fashion';
            
            // Получаем ID товара для формирования корректных URL изображений
            const productId = product.id ? String(product.id) : '';
            
            // Проверяем формат URL изображения
            let imageUrl = '';
            let imageUrls: string[] = [];
            
            if (product.image_url) {
              // Если есть image_url, используем его
              imageUrl = product.image_url;
              
              // Проверяем, соответствует ли формат URL нашему ожидаемому формату
              const isWbBasketUrl = /basket-\d+\.wbbasket\.ru\/vol/.test(imageUrl);
              
              if (!isWbBasketUrl && productId) {
                // Если URL не соответствует формату, создаем новый согласно правильной структуре
                // Определяем части URL на основе ID товара
                // Для vol берем первые 3-4 цифры ID
                const volDigits = productId.length >= 4 ? 4 : (productId.length >= 3 ? 3 : 1);
                const vol = productId.slice(0, volDigits);
                
                // Для part берем первые 5-6 цифр ID
                const partDigits = productId.length >= 6 ? 6 : (productId.length >= 5 ? 5 : productId.length);
                const part = productId.slice(0, partDigits);
                
                // Определяем номер бакета на основе ID
                // Используем остаток от деления последних 2 цифр ID на 20 + 1
                // чтобы получить номера от 1 до 20
                const lastTwoDigits = productId.slice(-2);
                const bucketNum = (parseInt(lastTwoDigits) % 20) + 1;
                const bucketStr = bucketNum.toString().padStart(2, '0');
                
                // Создаем массив URL изображений для разных ракурсов
                imageUrls = [1, 2, 3, 4].map(index => 
                  `https://basket-${bucketStr}.wbbasket.ru/vol${vol}/part${part}/${productId}/images/c516x688/${index}.webp`
                );
                
                // Используем первый URL в качестве основного
                imageUrl = imageUrls[0];
              } else if (isWbBasketUrl) {
                // Если URL уже в правильном формате, генерируем альтернативные URL для других ракурсов
                // Получаем базовый URL без номера изображения
                const baseUrl = imageUrl.replace(/\/\d+\.webp$/, '');
                imageUrls = [1, 2, 3, 4].map(index => `${baseUrl}/${index}.webp`);
              }
            }
            
            // Если есть imageUrls в ответе, используем их
            if (product.image_urls && Array.isArray(product.image_urls) && product.image_urls.length > 0) {
              if (!imageUrl) imageUrl = product.image_urls[0];
              if (imageUrls.length === 0) imageUrls = product.image_urls;
            }
            
            // Если все предыдущие проверки не дали результата, генерируем URL
            if (!imageUrl && productId) {
              // Определяем части URL на основе ID товара
              // Для vol берем первые 3-4 цифры ID
              const volDigits = productId.length >= 4 ? 4 : (productId.length >= 3 ? 3 : 1);
              const vol = productId.slice(0, volDigits);
              
              // Для part берем первые 5-6 цифр ID
              const partDigits = productId.length >= 6 ? 6 : (productId.length >= 5 ? 5 : productId.length);
              const part = productId.slice(0, partDigits);
              
              // Определяем номер бакета на основе ID
              // Используем остаток от деления последних 2 цифр ID на 20 + 1
              // чтобы получить номера от 1 до 20
              const lastTwoDigits = productId.slice(-2);
              const bucketNum = (parseInt(lastTwoDigits) % 20) + 1;
              const bucketStr = bucketNum.toString().padStart(2, '0');
              
              imageUrl = `https://basket-${bucketStr}.wbbasket.ru/vol${vol}/part${part}/${productId}/images/c516x688/1.webp`;
              
              // Создаем альтернативные URL для разных ракурсов (2.webp, 3.webp и т.д.)
              imageUrls = [1, 2, 3, 4].map(index => 
                `https://basket-${bucketStr}.wbbasket.ru/vol${vol}/part${part}/${productId}/images/c516x688/${index}.webp`
              );
            }
            
            return {
              id: product.id.toString(),
              name: product.name || '',
              brand: product.brand || '',
              price: product.price || 0,
              priceWithDiscount: product.sale_price || product.price || 0,
              imageUrl: imageUrl,
              imageUrls: imageUrls.length > 0 ? imageUrls : [imageUrl],
              url: product.url || `https://www.wildberries.ru/catalog/${product.id}/detail.aspx`,
              rating: product.rating || 0,
              category: category
            };
          });
          
          return NextResponse.json(products);
        }
      } else {
        // Логируем ошибку от API
        const errorText = await pythonApiResponse.text();
        console.error(`Ошибка API: ${pythonApiResponse.status} ${pythonApiResponse.statusText}`, errorText);
      }
      
      // Если что-то пошло не так при обращении к API или задача не завершилась успешно,
      // используем моковые данные
      console.log('Использование моковых данных для поиска товаров');
    } catch (error) {
      console.error('Ошибка при обращении к Python API:', error);
      // В случае ошибки используем моковые данные
    }

    // Фильтруем моковые данные для имитации поиска
    const queryLower = query.toLowerCase();
    const genderLower = gender.toLowerCase();
    
    let filteredProducts = mockProducts.filter(product => {
      const nameMatch = product.name.toLowerCase().includes(queryLower);
      const brandMatch = product.brand.toLowerCase().includes(queryLower);
      const categoryMatch = product.category?.toLowerCase().includes(queryLower) || false;
      const priceInRange = product.priceWithDiscount >= minPrice && product.priceWithDiscount <= maxPrice;
      
      // Применяем фильтр по полу, если он указан
      let genderMatch = true;
      if (genderLower) {
        // Проверяем, содержит ли название или категория товара упоминание пола
        const nameHasGender = product.name.toLowerCase().includes(genderLower) || 
                             (product.name.toLowerCase().includes('муж') && genderLower === 'мужской') ||
                             (product.name.toLowerCase().includes('жен') && genderLower === 'женский');
        
        const categoryHasGender = product.category?.toLowerCase().includes(genderLower) || false;
        
        genderMatch = nameHasGender || categoryHasGender;
      }
      
      return (nameMatch || brandMatch || categoryMatch) && priceInRange && genderMatch;
    });

    // Ограничиваем количество результатов
    filteredProducts = filteredProducts.slice(0, limit);

    return NextResponse.json(filteredProducts);
  } catch (error) {
    console.error('Ошибка при поиске товаров:', error);
    return NextResponse.json(
      { error: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
} 