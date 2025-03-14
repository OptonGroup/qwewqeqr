import { NextRequest, NextResponse } from 'next/server';

// Путь к Python API
const PYTHON_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json({ error: 'Файл не загружен' }, { status: 400 });
    }
    
    // Создаем новый FormData для отправки файла на бэкенд
    const backendFormData = new FormData();
    backendFormData.append('file', file);
    
    // Отправляем файл на бэкенд
    const response = await fetch(`${PYTHON_API_URL}/upload`, {
      method: 'POST',
      body: backendFormData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json({ error: errorData.detail || 'Ошибка при загрузке файла' }, { status: response.status });
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Ошибка при загрузке файла:', error);
    return NextResponse.json({ error: 'Внутренняя ошибка сервера' }, { status: 500 });
  }
} 