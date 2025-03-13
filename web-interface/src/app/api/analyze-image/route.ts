import { NextRequest, NextResponse } from 'next/server';
import { join } from 'path';
import { writeFile } from 'fs/promises';
import { v4 as uuidv4 } from 'uuid';
import { mkdir, access } from 'fs/promises';
import path from 'path';

// Тип ответа от AI на анализ изображения
interface ClothingRecognitionData {
  items: Array<{
    type: string;
    description: string;
    color: string;
    pattern?: string;
    material?: string;
    gender?: string;
  }>;
  fullDescription: string;
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

export async function POST(request: NextRequest) {
  try {
    // Проверяем доступность Python API
    const isApiAvailable = await checkApiAvailability();
    console.log(`Python API доступен: ${isApiAvailable}`);
    
    // Получаем FormData из запроса
    const formData = await request.formData();
    const image = formData.get('image') as File | null;
    const gender = formData.get('gender') as string || 'унисекс';

    if (!image) {
      return NextResponse.json(
        { error: 'Изображение не найдено' },
        { status: 400 }
      );
    }

    console.log(`Параметр gender: ${gender}`);

    // Создаем временный путь для сохранения изображения
    const bytes = await image.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const tempDir = path.join(process.cwd(), 'public', 'temp');
    
    // Создаем директорию temp, если она не существует
    try {
      await access(tempDir);
    } catch {
      await mkdir(tempDir, { recursive: true });
      console.log(`Создана директория: ${tempDir}`);
    }
    
    const fileName = `${Date.now()}_${image.name}`;
    const filePath = path.join(tempDir, fileName);
    const fileUrl = `/temp/${fileName}`;

    // Сохраняем изображение
    await writeFile(filePath, buffer);
    console.log(`Изображение сохранено: ${filePath}`);

    // Если Python API доступен, отправляем запрос туда
    if (isApiAvailable) {
      try {
        console.log('Отправляем запрос на Python API');
        
        // Создаем новый FormData для отправки в Python API
        const pythonApiFormData = new FormData();
        
        // В Python API ожидается файл с именем 'file'
        pythonApiFormData.append('file', new Blob([buffer], { type: image.type }), fileName);
        // Добавляем параметр gender
        pythonApiFormData.append('gender', gender);
        
        // Отправляем запрос на Python API
        const pythonApiResponse = await fetch(`${PYTHON_API_URL}/analyze-image`, {
          method: 'POST',
          body: pythonApiFormData,
        });
        
        if (!pythonApiResponse.ok) {
          const errorText = await pythonApiResponse.text();
          console.error(`Ошибка Python API: ${pythonApiResponse.status}`, errorText);
          throw new Error(`Ошибка Python API: ${pythonApiResponse.status}`);
        }
        
        const analysisData = await pythonApiResponse.json();
        console.log('Получен ответ от Python API:', analysisData);
        
        // Обрабатываем ответ от Python API и преобразуем в формат для фронтенда
        let results = [];
        
        if (analysisData.results && Array.isArray(analysisData.results)) {
          results = analysisData.results;
        } else if (analysisData.items && Array.isArray(analysisData.items)) {
          // Преобразуем формат данных из Python API в формат для фронтенда
          results = analysisData.items.map((item: any, index: number) => ({
            id: `${index + 1}`,
            name: item.name || item.type || 'Предмет одежды',
            description: item.description || `${item.color || ''} ${item.material || ''}`.trim(),
            price: Math.floor(Math.random() * 5000) + 500, // Демо-цена
            imageUrl: item.imageUrl || `https://basket-0${(index % 9) + 1}.wbbasket.ru/vol${index + 1}00/part${index + 1}00${index + 1}/100${index + 1}${index + 1}${index + 1}/images/c516x688/1.webp`,
            category: item.category || 'Одежда',
            gender: item.gender || 'унисекс'
          }));
        } else if (analysisData.elements && Array.isArray(analysisData.elements)) {
          // Обрабатываем формат с полем elements
          let allProducts: any[] = [];
          
          // Проходим по каждому элементу одежды
          for (const element of analysisData.elements) {
            if (element.wb_products && Array.isArray(element.wb_products)) {
              // Преобразуем продукты из Wildberries в наш формат
              const products = element.wb_products.map((product: any, idx: number) => {
                // Обработка цен
                let price = 0;
                let oldPrice = undefined;
                let salePrice = undefined;
                
                // Получаем цены из разных возможных полей
                if (product.price !== undefined) price = Number(product.price);
                
                // Получаем старую цену
                if (product.priceU !== undefined) oldPrice = Number(product.priceU);
                else if (product.oldPrice !== undefined) oldPrice = Number(product.oldPrice);
                
                // Получаем цену со скидкой
                if (product.sale_price !== undefined) salePrice = Number(product.sale_price);
                else if (product.salePriceU !== undefined) salePrice = Number(product.salePriceU);
                
                // Если у нас есть только старая цена и нет скидочной, используем цену как скидочную
                if (oldPrice !== undefined && (salePrice === undefined || salePrice === 0)) {
                  if (price > 0 && price < oldPrice) {
                    salePrice = price;
                  } else {
                    salePrice = oldPrice;
                  }
                }
                
                // Если у нас есть только скидочная цена и нет старой, используем скидочную как основную
                if (salePrice !== undefined && oldPrice === undefined) {
                  if (price > salePrice) {
                    oldPrice = price;
                  } else {
                    oldPrice = salePrice;
                  }
                }
                
                // Если у нас нет цен вообще, используем случайную цену
                if (price === 0 && oldPrice === undefined && salePrice === undefined) {
                  price = Math.floor(Math.random() * 5000) + 500;
                }
                
                // Сформируем объект продукта
                return {
                  id: product.id || `${element.type}-${idx}`,
                  name: product.name || `${element.color} ${element.type}`,
                  description: product.description || element.description || `${element.color} ${element.type}`,
                  price: salePrice || price,
                  oldPrice: oldPrice,
                  imageUrl: product.imageUrl || product.img || (product.pics && product.pics[0]),
                  category: element.type || 'Одежда',
                  gender: element.gender || gender || 'унисекс',
                  url: product.url || product.link || `https://www.wildberries.ru/catalog/${product.id}/detail.aspx`,
                  brand: product.brand
                };
              });
              
              allProducts = [...allProducts, ...products];
            } else {
              // Если нет wb_products, создаем демо-продукт на основе описания элемента
              allProducts.push({
                id: `${element.type}-demo`,
                name: `${element.color} ${element.type}`,
                description: element.description || `${element.color} ${element.type}`,
                price: Math.floor(Math.random() * 5000) + 500,
                imageUrl: `https://basket-0${(allProducts.length % 9) + 1}.wbbasket.ru/vol${allProducts.length + 1}00/part${allProducts.length + 1}00${allProducts.length + 1}/100${allProducts.length + 1}${allProducts.length + 1}${allProducts.length + 1}/images/c516x688/1.webp`,
                category: element.type || 'Одежда',
                gender: element.gender || gender || 'унисекс'
              });
            }
          }
          
          results = allProducts;
        } else {
          // Если ничего не найдено, используем моковые данные
          console.log('Неизвестный формат данных от Python API, используем моковые данные');
          results = getMockResults(gender).results;
        }
        
        return NextResponse.json({ 
          results,
          imageUrl: fileUrl,
          api_source: 'python',
          analysis: analysisData.analysis || ""
        });
        
      } catch (error) {
        console.error('Ошибка при обращении к Python API:', error);
        
        // В случае ошибки возвращаем моковые данные
        const mockData = getMockResults(gender);
        return NextResponse.json({ 
          results: mockData.results,
          imageUrl: fileUrl,
          error: `Ошибка при обращении к Python API: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`,
          api_source: 'mock',
          analysis: "Не удалось проанализировать изображение из-за ошибки API."
        });
      }
    } else {
      // Если Python API недоступен, используем моковые данные
      console.log('Python API недоступен, используем моковые данные');
      const mockData = getMockResults(gender);
      return NextResponse.json({ 
        results: mockData.results,
        imageUrl: fileUrl,
        api_source: 'mock',
        analysis: "Анализ недоступен - сервер анализа изображений не отвечает."
      });
    }
  } catch (error) {
    console.error('Ошибка при обработке изображения:', error);
    return NextResponse.json(
      { error: 'Произошла ошибка при обработке изображения' },
      { status: 500 }
    );
  }
}

// Функция для получения моковых данных
function getMockResults(gender: string = 'унисекс') {
  const userGender = gender.toLowerCase();
  
  return {
    results: [
      {
        id: '1',
        name: 'Белая хлопковая футболка',
        description: 'Базовая футболка из органического хлопка с круглым вырезом',
        price: 999,
        imageUrl: 'https://basket-01.wbbasket.ru/vol1001/part100135/100135766/images/c516x688/1.webp',
        category: 'Верх',
        gender: userGender
      },
      {
        id: '2',
        name: 'Белая футболка оверсайз',
        description: 'Свободная футболка свободного кроя из мягкого хлопка',
        price: 1299,
        imageUrl: 'https://basket-03.wbbasket.ru/vol283/part28364/28364770/images/c516x688/1.webp',
        category: 'Верх',
        gender: userGender
      },
      {
        id: '3',
        name: 'Футболка с принтом',
        description: 'Стильная хлопковая футболка с графическим принтом',
        price: 1599,
        imageUrl: 'https://basket-05.wbbasket.ru/vol758/part75846/75846387/images/c516x688/1.webp',
        category: 'Верх',
        gender: userGender === 'мужской' ? 'мужской' : 'женский'
      },
      {
        id: '4',
        name: 'Базовая белая блузка',
        description: 'Элегантная блузка из смесового хлопка со свободным силуэтом',
        price: 2499,
        imageUrl: 'https://basket-11.wbbasket.ru/vol1457/part145766/145766287/images/c516x688/1.webp',
        category: 'Верх',
        gender: 'женский'
      },
      {
        id: '5',
        name: 'Черная хлопковая футболка',
        description: 'Классическая черная футболка из премиального хлопка',
        price: 1099,
        imageUrl: 'https://basket-10.wbbasket.ru/vol1418/part141812/141812883/images/c516x688/1.webp',
        category: 'Верх',
        gender: 'мужской'
      },
      {
        id: '6',
        name: 'Белая рубашка',
        description: 'Классическая рубашка из хлопка с длинным рукавом',
        price: 2999,
        imageUrl: 'https://basket-12.wbbasket.ru/vol1688/part168842/168842122/images/c516x688/1.webp',
        category: 'Верх',
        gender: userGender === 'женский' ? 'женский' : 'мужской'
      }
    ]
  };
}

// Функция для разбора ответа от Python API и преобразования в формат ClothingRecognitionData
function parseClothingItemsFromAnalysis(analysisData: any): ClothingRecognitionData['items'] {
  // Если API вернул уже правильно отформатированные данные
  if (analysisData.elements && Array.isArray(analysisData.elements)) {
    return analysisData.elements.map((item: any) => ({
      type: item.type || item.name || 'Предмет одежды',
      color: item.color || 'неизвестный',
      description: item.description || '',
      material: item.material,
      pattern: item.pattern,
      gender: item.gender
    }));
  }

  // Если API вернул данные в поле 'analysis'
  if (analysisData.analysis) {
    console.log('Получен анализ текста:', analysisData.analysis);
  }
  
  // Если API вернул данные в нестандартной структуре, проверяем все возможные поля
  const possibleDataFields = ['data', 'result', 'results', 'items', 'clothing_items'];
  for (const field of possibleDataFields) {
    if (analysisData[field] && (Array.isArray(analysisData[field]) || typeof analysisData[field] === 'object')) {
      console.log(`Найдены данные в поле ${field}:`, analysisData[field]);
      if (Array.isArray(analysisData[field])) {
        return analysisData[field].map((item: any) => ({
          type: item.type || item.name || 'Предмет одежды',
          color: item.color || 'неизвестный',
          description: item.description || '',
          material: item.material,
          pattern: item.pattern,
          gender: item.gender
        }));
      }
    }
  }

  // Если API вернул анализ в текстовом формате, пытаемся извлечь информацию о предметах одежды
  const analysisText = analysisData.analysis || analysisData.description || '';
  
  if (!analysisText) {
    console.log('Нет текстового анализа, возвращаем моковые данные');
    return getMockAnalysisResponse().items;
  }

  // Пытаемся извлечь элементы одежды из текста
  const clothingItems = [];
  
  // Ищем упоминания предметов одежды в тексте
  const commonClothingItems = [
    'футболка', 'рубашка', 'блузка', 'платье', 'юбка', 'брюки', 'джинсы',
    'шорты', 'куртка', 'пальто', 'свитер', 'кардиган', 'худи', 'джемпер',
    'кроссовки', 'туфли', 'ботинки', 'сапоги', 'кеды', 'шапка', 'шляпа',
    'берет', 'кепка', 'шарф', 'перчатки', 'носки', 'колготки', 'белье',
    'костюм', 'пиджак', 'жакет', 'блейзер'
  ];
  
  // Ищем цвета
  const commonColors = [
    'белый', 'черный', 'красный', 'синий', 'зеленый', 'желтый', 'оранжевый',
    'фиолетовый', 'розовый', 'коричневый', 'серый', 'бежевый', 'голубой'
  ];

  // Ищем материалы
  const commonMaterials = [
    'хлопок', 'лен', 'шерсть', 'кожа', 'замша', 'шелк', 'деним', 'полиэстер',
    'нейлон', 'трикотаж', 'вискоза', 'акрил', 'вельвет', 'твид', 'кашемир'
  ];

  console.log('Анализируем текст:', analysisText);

  // Для каждого предмета одежды проверяем, упоминается ли он в тексте
  for (const item of commonClothingItems) {
    const regex = new RegExp(`\\b${item}\\b`, 'i');
    if (regex.test(analysisText.toLowerCase())) {
      console.log(`Найден предмет: ${item}`);
      
      // Если предмет найден, пытаемся найти его цвет
      let color = 'неизвестный';
      for (const c of commonColors) {
        const colorRegex = new RegExp(`\\b${c}\\w*\\s+${item}\\b|\\b${item}\\s+${c}\\w*\\b`, 'i');
        if (colorRegex.test(analysisText.toLowerCase())) {
          color = c;
          console.log(`  Найден цвет: ${color}`);
          break;
        }
      }
      
      // Пытаемся найти материал
      let material;
      for (const m of commonMaterials) {
        const materialRegex = new RegExp(`\\b${m}\\w*\\s+${item}\\b|\\b${item}\\s+из\\s+${m}\\w*\\b|\\b${m}\\w*\\s+${item}\\b`, 'i');
        if (materialRegex.test(analysisText.toLowerCase())) {
          material = m;
          console.log(`  Найден материал: ${material}`);
          break;
        }
      }
      
      clothingItems.push({
        type: item.charAt(0).toUpperCase() + item.slice(1),
        color,
        description: '',
        ...(material && { material }),
        gender: determineGender(analysisText, item)
      });
    }
  }
  
  if (clothingItems.length > 0) {
    console.log('Найдены предметы одежды:', clothingItems);
    return clothingItems;
  } else {
    console.log('Не удалось распознать предметы одежды в тексте, возвращаем моковые данные');
    return getMockAnalysisResponse().items;
  }
}

// Заглушка для тестирования, используется когда нет доступа к Python API
function getMockAnalysisResponse(imageUrl?: string): ClothingRecognitionData {
  return {
    items: [
      {
        type: 'Футболка',
        color: 'белая',
        description: 'хлопковая с круглым вырезом',
        material: 'хлопок',
        gender: 'женский'
      },
      {
        type: 'Джинсы',
        color: 'синие',
        description: 'классические прямого кроя',
        material: 'деним',
        gender: 'женский'
      }
    ],
    fullDescription: 'На изображении представлен повседневный комплект, состоящий из белой хлопковой футболки с круглым вырезом и классических прямых синих джинсов.'
  };
}

// Функция для определения пола из текста анализа
function determineGender(text: string, itemName: string): string | undefined {
  // Ищем явное указание пола для всего образа
  const generalGenderMatch = text.match(/ПОЛ:\s*(мужской|женский|унисекс)/i);
  let generalGender = generalGenderMatch ? generalGenderMatch[1].toLowerCase() : undefined;
  
  // Ищем указание пола для конкретного предмета
  const itemGenderRegex = new RegExp(`(${itemName}).*?пол:\\s*(мужской|женский|унисекс)`, 'i');
  const itemGenderMatch = text.match(itemGenderRegex);
  
  // Возвращаем пол для конкретного предмета, если найден, иначе общий пол
  return itemGenderMatch ? itemGenderMatch[2].toLowerCase() : generalGender;
} 