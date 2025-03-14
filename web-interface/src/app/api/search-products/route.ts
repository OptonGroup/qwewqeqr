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
const PYTHON_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';

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

// Функция для поиска товаров через Python API
async function searchProductsViaAPI(query: string, limit: number, minPrice: number, maxPrice: number, gender: string): Promise<WildberriesProduct[]> {
  try {
    const response = await fetch(`${PYTHON_API_URL}/api/search-products-direct`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        limit,
        min_price: minPrice,
        max_price: maxPrice,
        gender
      }),
      signal: AbortSignal.timeout(10000) // Таймаут 10 секунд
    });

    if (!response.ok) {
      console.error(`Ошибка API: ${response.status} - ${response.statusText}`);
      const errorText = await response.text();
      console.error(`Детали ошибки: ${errorText}`);
      return [];
    }

    const data = await response.json();
    
    if (Array.isArray(data)) {
      return data.map(product => ({
        id: product.id.toString(),
        name: product.name || 'Товар без названия',
        brand: product.brand || 'Бренд не указан',
        price: product.price || 0,
        priceWithDiscount: product.sale_price || product.price || 0,
        imageUrl: product.imageUrl || product.image_url || '',
        imageUrls: product.imageUrls || (product.imageUrl ? [product.imageUrl] : []),
        url: product.url || product.product_url || `https://www.wildberries.ru/catalog/${product.id}/detail.aspx`,
        rating: product.rating || 0,
        category: product.category || ''
      }));
    } else {
      console.error('Неожиданный формат данных от API:', data);
      return [];
    }
  } catch (error) {
    console.error('Ошибка при поиске товаров через API:', error);
    return [];
  }
}

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
    const gender = searchParams.get('gender') || '';

    // Валидация параметров
    if (!query) {
      return NextResponse.json(
        { error: 'Параметр query обязателен' },
        { status: 400 }
      );
    }

    let products: WildberriesProduct[] = [];

    // Если API доступно, используем его для поиска товаров
    if (isApiAvailable) {
      console.log(`Выполняем поиск через API: ${query}, лимит: ${limit}`);
      products = await searchProductsViaAPI(query, limit, minPrice, maxPrice, gender);
      console.log(`Получено ${products.length} товаров от API`);
    } 
    
    // Возвращаем результаты поиска
    return NextResponse.json(products);
  } catch (error) {
    console.error('Ошибка при обработке запроса:', error);
    return NextResponse.json(
      { error: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
} 