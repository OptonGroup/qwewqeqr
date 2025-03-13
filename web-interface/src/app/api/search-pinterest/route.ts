import { NextRequest, NextResponse } from 'next/server';

// Интерфейс для результата поиска в Pinterest
interface PinterestSearchResult {
  imageUrl: string;
  sourceUrl: string;
  description: string;
  clothingItems: ClothingItem[];
}

// Интерфейс для предмета одежды
interface ClothingItem {
  type: string;    // Тип предмета (футболка, джинсы и т.д.)
  color: string;   // Цвет предмета
  description: string; // Описание (принт, фасон и т.д.)
  gender: string;  // Пол (мужской, женский)
}

// Путь к Python API
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// Моковые данные для тестирования
const mockPinterestResults: PinterestSearchResult[] = [
  {
    imageUrl: 'https://i.pinimg.com/564x/f2/a6/d9/f2a6d9088d0e2a82b8b342c6116c7151.jpg',
    sourceUrl: 'https://www.pinterest.com/pin/123456789/',
    description: 'Повседневный женский образ в стиле кэжуал с джинсами и белой футболкой',
    clothingItems: [
      {
        type: 'футболка',
        color: 'белая',
        description: 'базовая хлопковая',
        gender: 'женский'
      },
      {
        type: 'джинсы',
        color: 'синие',
        description: 'классические прямые',
        gender: 'женский'
      },
      {
        type: 'кеды',
        color: 'белые',
        description: 'низкие',
        gender: 'женский'
      }
    ]
  },
  {
    imageUrl: 'https://i.pinimg.com/564x/e1/f5/54/e1f554ab930cd5a21ee6ecb018ddcec0.jpg',
    sourceUrl: 'https://www.pinterest.com/pin/987654321/',
    description: 'Элегантный образ с черным пиджаком и джинсами',
    clothingItems: [
      {
        type: 'пиджак',
        color: 'черный',
        description: 'классический',
        gender: 'женский'
      },
      {
        type: 'футболка',
        color: 'белая',
        description: 'базовая',
        gender: 'женский'
      },
      {
        type: 'джинсы',
        color: 'синие',
        description: 'момы свободного кроя',
        gender: 'женский'
      },
      {
        type: 'туфли',
        color: 'черные',
        description: 'лодочки на каблуке',
        gender: 'женский'
      }
    ]
  },
  {
    imageUrl: 'https://i.pinimg.com/564x/43/2b/1e/432b1e52c3c9a4b3c474e771ab812d67.jpg',
    sourceUrl: 'https://www.pinterest.com/pin/456789123/',
    description: 'Стильный образ с кожаной курткой и черными джинсами',
    clothingItems: [
      {
        type: 'куртка',
        color: 'черная',
        description: 'кожаная',
        gender: 'женский'
      },
      {
        type: 'футболка',
        color: 'черная',
        description: 'базовая',
        gender: 'женский'
      },
      {
        type: 'джинсы',
        color: 'черные',
        description: 'скинни',
        gender: 'женский'
      },
      {
        type: 'ботинки',
        color: 'черные',
        description: 'на шнуровке',
        gender: 'женский'
      }
    ]
  }
];

export async function POST(request: NextRequest) {
  try {
    // Получаем запрос от пользователя
    const body = await request.json();
    const { query, gender = 'женский' } = body;

    // Проверяем наличие запроса
    if (!query) {
      return NextResponse.json(
        { error: 'Необходимо указать поисковый запрос' },
        { status: 400 }
      );
    }

    try {
      // Пытаемся отправить запрос к Python API для поиска в Pinterest
      const pinterestSearchResponse = await fetch(`${PYTHON_API_URL}/search-pinterest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          gender,
          num_results: 3
        }),
      });

      if (pinterestSearchResponse.ok) {
        // Получаем ID задачи
        const responseData = await pinterestSearchResponse.json();
        console.log('Ответ от Pinterest API:', responseData);
        
        const task_id = responseData.task_id;
        if (!task_id) {
          console.error('API не вернул task_id');
          throw new Error('API не вернул task_id');
        }
        
        // Дожидаемся завершения задачи поиска (с таймаутом 15 секунд)
        let taskResult = null;
        let attempts = 0;
        const maxAttempts = 30;
        
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
        if (taskResult && taskResult.pinterest_results && taskResult.pinterest_results.length > 0) {
          console.log(`Найдено ${taskResult.pinterest_results.length} образов из Pinterest`);
          
          return NextResponse.json(taskResult.pinterest_results);
        }
      } else {
        // Логируем ошибку от API
        const errorText = await pinterestSearchResponse.text();
        console.error(`Ошибка Pinterest API: ${pinterestSearchResponse.status} ${pinterestSearchResponse.statusText}`, errorText);
      }
      
      // В случае ошибки или отсутствия результатов используем моковые данные
      console.log('Использование моковых данных Pinterest');
      
      // Фильтруем моковые данные по полу, если указан
      let filteredResults = mockPinterestResults;
      if (gender) {
        const genderLower = gender.toLowerCase();
        filteredResults = mockPinterestResults.filter(result => {
          // Проверяем, есть ли хотя бы один предмет одежды для указанного пола
          return result.clothingItems.some(item => 
            item.gender.toLowerCase() === genderLower
          );
        });
      }

      return NextResponse.json(filteredResults);
    } catch (error) {
      console.error('Ошибка при обращении к Python API Pinterest:', error);
      // В случае ошибки используем моковые данные
      return NextResponse.json(mockPinterestResults);
    }
  } catch (error) {
    console.error('Ошибка при обработке запроса к Pinterest API:', error);
    return NextResponse.json(
      { error: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
} 