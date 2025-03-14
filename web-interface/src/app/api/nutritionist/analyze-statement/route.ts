import { NextResponse } from 'next/server';

/**
 * Заглушка для API-маршрута анализа банковской выписки
 * Этот функционал был удален из приложения
 */
export async function POST(request: Request) {
  return NextResponse.json(
    { 
      error: 'Функциональность анализа банковских выписок отключена', 
      message: 'Эта функция больше не поддерживается'
    }, 
    { status: 404 }
  );
} 