/**
 * Конфигурация API для взаимодействия с бэкендом
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Интерфейсы для типизации ответов API
 */
export interface SkinAnalysis {
  description: string;
  daily: {
    morning: { steps: Array<{ name: string; product: string }> };
    evening: { steps: Array<{ name: string; product: string }> };
  };
  weekly: {
    procedures: Array<{ name: string; product: string; frequency: string }>;
    additional: Array<{ name: string; description: string }>;
  };
  recommendations: {
    lifestyle: Array<{ text: string }>;
    ingredients: Array<{ name: string; purpose: string }>;
  };
}

export interface CosmetologistAnalysisResponse {
  skinAnalysis: SkinAnalysis;
  productRecommendations?: any[];
  identifiedNeeds?: any;
  [key: string]: any;
}

// Интерфейсы для дизайнера интерьера
export interface DesignAnalysis {
  roomType: string;
  style: string;
  colorPalette: string[];
  recommendedMaterials: string[];
  designPrinciples: {
    title: string;
    description: string;
  }[];
  area: number;
  identifiedNeeds: any;
}

export interface TextRecommendation {
  title: string;
  description: string;
}

export interface DesignConcept {
  mainIdea: string;
  styleDescription: string;
  moodBoard: string[];
  keyElements: {
    name: string;
    description: string;
  }[];
}

export interface FloorPlan {
  dimensions: {
    width: number;
    length: number;
    area: number;
  };
  zoning: {
    name: string;
    area: number;
    position: string;
  }[];
  furnitureLayout: {
    name: string;
    position: string;
    dimensions: string;
  }[];
  recommendations: string[];
}

export interface DesignerApiResponse {
  success: boolean;
  designAnalysis?: DesignAnalysis;
  textRecommendations?: TextRecommendation[];
  designConcept?: DesignConcept;
  floorPlan?: FloorPlan;
  error?: string;
}

export interface NutritionAnalysis {
  overview: string;
  goals: {
    title: string;
    description: string;
  }[];
  restrictions: {
    title: string;
    description: string;
  }[];
  recommendations: {
    category: string;
    items: string[];
  }[];
}

export interface MealPlan {
  days: {
    day: string;
    meals: {
      type: string;
      name: string;
      description: string;
      ingredients: string[];
      nutrition?: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
      };
    }[];
  }[];
  nutritionSummary: {
    dailyCalories: number;
    macroDistribution: {
      protein: number;
      carbs: number;
      fat: number;
    };
  };
}

export interface NutritionistAnalysisResponse {
  success: boolean;
  nutritionAnalysis?: NutritionAnalysis;
  mealPlan?: MealPlan;
  productRecommendations?: any[];
  error?: string;
}

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
  analyze: async (userData: any): Promise<CosmetologistAnalysisResponse> => {
    return fetchApi<CosmetologistAnalysisResponse>('/api/cosmetologist/analyze', 'POST', userData);
  },
};

/**
 * API для работы с ассистентом нутрициолога
 */
export const nutritionistApi = {
  /**
   * Анализирует данные пользователя и возвращает рекомендации по питанию
   */
  analyze: async (userData: any): Promise<NutritionistAnalysisResponse> => {
    return fetchApi<NutritionistAnalysisResponse>('/api/nutritionist/analyze', 'POST', userData);
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
  analyze: async (userData: any): Promise<DesignerApiResponse> => {
    return fetchApi<DesignerApiResponse>('/api/designer/analyze', 'POST', userData);
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