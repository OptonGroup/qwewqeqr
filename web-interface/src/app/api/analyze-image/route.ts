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
    const file = formData.get('file') as File | null;

    if (!file) {
      return NextResponse.json(
        { error: 'Файл не найден' },
        { status: 400 }
      );
    }

    // Проверяем тип файла
    if (!file.type.startsWith('image/')) {
      return NextResponse.json(
        { error: 'Пожалуйста, загрузите изображение' },
        { status: 400 }
      );
    }

    // Создаем директорию для загрузок, если она не существует
    const uploadDir = join(process.cwd(), 'public', 'uploads');
    try {
      await access(uploadDir);
    } catch {
      await mkdir(uploadDir, { recursive: true });
    }

    // Создаем уникальное имя файла
    const fileExt = path.extname(file.name) || '.jpg';
    const filename = `${uuidv4()}${fileExt}`;
    const filepath = join(uploadDir, filename);

    try {
      // Читаем содержимое файла
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);

      // Сохраняем файл локально
      await writeFile(filepath, buffer);

      // URL файла для использования во фронтенде
      const fileUrl = `/uploads/${filename}`;

      try {
        // Если API недоступен, сразу возвращаем заглушку с предупреждением
        if (!isApiAvailable) {
          console.error('Python API недоступен, возвращаем тестовые данные');
          return NextResponse.json({
            ...getMockAnalysisResponse(fileUrl),
            imageUrl: fileUrl,
            error: 'Python API недоступен. Возможно, сервер не запущен или запущен не на порту 8000. Возвращены тестовые данные.'
          });
        }
        
        // Создаем новый FormData для отправки в Python API
        const pythonApiFormData = new FormData();
        
        // В Python API ожидается файл с именем 'file'
        pythonApiFormData.append('file', new Blob([buffer], { type: file.type }), filename);
        
        console.log(`Отправляем запрос к Python API: ${PYTHON_API_URL}/analyze-image`);
        
        // Пытаемся отправить запрос на анализ изображения в Python API
        const pythonApiResponse = await fetch(`${PYTHON_API_URL}/analyze-image`, {
          method: 'POST',
          body: pythonApiFormData,
        });

        if (pythonApiResponse.ok) {
          // Если успешно получили ответ от Python API
          const analysisData = await pythonApiResponse.json();
          console.log('Ответ от Python API:', analysisData);
          
          return NextResponse.json({
            items: parseClothingItemsFromAnalysis(analysisData),
            fullDescription: analysisData.analysis || '',
            imageUrl: fileUrl
          });
        } else {
          const errorText = await pythonApiResponse.text();
          console.error(`Ошибка Python API: ${pythonApiResponse.status} ${pythonApiResponse.statusText}`, errorText);
          
          // Если не удалось получить ответ от Python API, используем моковые данные
          return NextResponse.json({
            ...getMockAnalysisResponse(fileUrl),
            imageUrl: fileUrl,
            error: `Не удалось подключиться к серверу анализа изображений: ${pythonApiResponse.status} ${pythonApiResponse.statusText}. Возвращены тестовые данные.`
          });
        }
      } catch (error) {
        console.error('Ошибка при обращении к Python API:', error);
        // В случае ошибки вызова Python API возвращаем моковые данные
        return NextResponse.json({
          ...getMockAnalysisResponse(fileUrl),
          imageUrl: fileUrl,
          error: `Не удалось подключиться к серверу анализа изображений: ${error.message}. Возвращены тестовые данные.`
        });
      }
    } catch (error) {
      console.error('Ошибка при сохранении файла:', error);
      return NextResponse.json(
        { error: 'Ошибка при обработке файла' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Ошибка при обработке запроса:', error);
    return NextResponse.json(
      { error: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
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