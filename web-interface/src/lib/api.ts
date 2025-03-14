/**
 * Конфигурация API для взаимодействия с бэкендом
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Функция для отправки запроса к API
 * @param endpoint - конечная точка API
 * @param method - HTTP-метод
 * @param data - данные для отправки
 * @returns Promise с результатом запроса
 */
export async function fetchApi<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: any
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'same-origin',
  };
  
  if (data) {
    options.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Ошибка API: ${response.status} ${response.statusText}`
      );
    }
    
    return await response.json() as T;
  } catch (error) {
    console.error('Ошибка при запросе к API:', error);
    throw error;
  }
}

/**
 * API для работы с ассистентом косметолога
 */
export const cosmetologistApi = {
  /**
   * Анализирует данные пользователя и возвращает рекомендации
   */
  analyze: async (userData: any) => {
    return fetchApi('/api/cosmetologist/analyze', 'POST', userData);
  },
};

/**
 * API для работы с ассистентом нутрициолога
 */
export const nutritionistApi = {
  /**
   * Анализирует данные пользователя и возвращает рекомендации по питанию
   */
  analyze: async (userData: any) => {
    return fetchApi('/api/nutritionist/analyze', 'POST', userData);
  }
};

/**
 * API для работы с ассистентом дизайнера интерьера
 */
export const designerApi = {
  /**
   * Анализирует данные пользователя и возвращает комплексные рекомендации по дизайну интерьера:
   * - дизайн-анализ (designAnalysis): цветовая палитра, материалы, принципы дизайна
   * - текстовые рекомендации (textRecommendations): что передвинуть, что докупить, что убрать
   * - дизайн-концепция (designConcept): основная идея, описание стиля, ключевые элементы
   * - планировка (floorPlan): размеры, зонирование, расстановка мебели, рекомендации
   */
  analyze: async (userData: any) => {
    return fetchApi('/api/designer/analyze', 'POST', userData);
  }
};

/**
 * API для поиска продуктов на Wildberries
 */
export const productsApi = {
  /**
   * Поиск продуктов по запросу
   */
  search: async (query: string, limit: number = 10, minPrice?: number, maxPrice?: number) => {
    return fetchApi<any[]>(`/api/search-products?query=${encodeURIComponent(query)}&limit=${limit}${minPrice ? `&min_price=${minPrice}` : ''}${maxPrice ? `&max_price=${maxPrice}` : ''}`);
  },
  
  /**
   * Поиск продуктов с расширенными параметрами
   */
  searchAdvanced: async (params: any) => {
    return fetchApi<any[]>('/api/search-products-direct', 'POST', params);
  },
};

/**
 * API для определения потребностей пользователя
 */
export const userNeedsApi = {
  /**
   * Определяет потребности пользователя на основе ввода
   */
  determine: async (userId: string, role: string, message: string) => {
    return fetchApi('/api/determine_user_needs', 'POST', {
      user_id: userId,
      role,
      message,
    });
  },
}; 