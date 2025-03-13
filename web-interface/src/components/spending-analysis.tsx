"use client";

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { CategorySpending } from '@/types/bank-statement';
import { ArrowDownIcon, ArrowUpIcon, TrendingUpIcon, TrendingDownIcon } from 'lucide-react';

interface SpendingAnalysisProps {
  currentMonthSpending: CategorySpending[];
  previousMonthSpending: CategorySpending[];
  averageMonthlySpending: CategorySpending[];
  startDate: string;
  endDate: string;
}

const SpendingAnalysis = ({
  currentMonthSpending,
  previousMonthSpending,
  averageMonthlySpending,
  startDate,
  endDate,
}: SpendingAnalysisProps) => {
  const analysis = useMemo(() => {
    const currentTotal = currentMonthSpending.reduce((sum, item) => sum + item.amount, 0);
    const previousTotal = previousMonthSpending.reduce((sum, item) => sum + item.amount, 0);
    const averageTotal = averageMonthlySpending.reduce((sum, item) => sum + item.amount, 0);
    
    const changeFromPrevious = previousTotal > 0 
      ? ((currentTotal - previousTotal) / previousTotal) * 100 
      : 0;
    
    const changeFromAverage = averageTotal > 0 
      ? ((currentTotal - averageTotal) / averageTotal) * 100 
      : 0;
      
    // Находим самую большую категорию расходов
    const topCategory = currentMonthSpending.length > 0 
      ? currentMonthSpending.reduce((max, item) => max.amount > item.amount ? max : item)
      : null;
      
    // Находим категорию с наибольшим ростом
    const categoriesWithGrowth = currentMonthSpending.map(current => {
      const previous = previousMonthSpending.find(item => item.category === current.category);
      if (!previous) return { category: current.category, growth: 100, amount: current.amount };
      
      const growth = ((current.amount - previous.amount) / previous.amount) * 100;
      return {
        category: current.category,
        growth,
        amount: current.amount
      };
    });
    
    const topGrowthCategory = categoriesWithGrowth.length > 0
      ? categoriesWithGrowth.reduce((max, item) => (max.growth > item.growth ? max : item))
      : null;
      
    return {
      currentTotal,
      previousTotal,
      averageTotal,
      changeFromPrevious,
      changeFromAverage,
      topCategory,
      topGrowthCategory
    };
  }, [currentMonthSpending, previousMonthSpending, averageMonthlySpending]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Анализ расходов</CardTitle>
        <CardDescription>
          Обзор ваших трат с {startDate} по {endDate}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
          <div className="p-4 border rounded-lg">
            <div className="text-sm text-gray-500">Общие расходы</div>
            <div className="text-2xl font-bold mt-1">
              {Math.round(analysis.currentTotal).toLocaleString('ru-RU')} ₽
            </div>
            <div className="flex items-center mt-1">
              {analysis.changeFromPrevious > 0 ? (
                <ArrowUpIcon className="h-4 w-4 text-red-500 mr-1" />
              ) : (
                <ArrowDownIcon className="h-4 w-4 text-green-500 mr-1" />
              )}
              <span 
                className={analysis.changeFromPrevious > 0 ? 'text-red-500' : 'text-green-500'}
              >
                {Math.abs(Math.round(analysis.changeFromPrevious))}% от прошлого месяца
              </span>
            </div>
          </div>

          <div className="p-4 border rounded-lg">
            <div className="text-sm text-gray-500">Сравнение со средним</div>
            <div className="text-2xl font-bold mt-1">
              {Math.round(analysis.averageTotal).toLocaleString('ru-RU')} ₽
            </div>
            <div className="flex items-center mt-1">
              {analysis.changeFromAverage > 0 ? (
                <TrendingUpIcon className="h-4 w-4 text-red-500 mr-1" />
              ) : (
                <TrendingDownIcon className="h-4 w-4 text-green-500 mr-1" />
              )}
              <span 
                className={analysis.changeFromAverage > 0 ? 'text-red-500' : 'text-green-500'}
              >
                {Math.abs(Math.round(analysis.changeFromAverage))}% от среднего
              </span>
            </div>
          </div>

          {analysis.topCategory && (
            <div className="p-4 border rounded-lg">
              <div className="text-sm text-gray-500">Самая большая категория расходов</div>
              <div className="text-xl font-bold mt-1">{analysis.topCategory.category}</div>
              <div className="text-lg mt-1">
                {Math.round(analysis.topCategory.amount).toLocaleString('ru-RU')} ₽
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {Math.round((analysis.topCategory.amount / analysis.currentTotal) * 100)}% от общих расходов
              </div>
            </div>
          )}

          {analysis.topGrowthCategory && analysis.topGrowthCategory.growth > 0 && (
            <div className="p-4 border rounded-lg">
              <div className="text-sm text-gray-500">Наибольший рост расходов</div>
              <div className="text-xl font-bold mt-1">{analysis.topGrowthCategory.category}</div>
              <div className="text-lg mt-1">
                {Math.round(analysis.topGrowthCategory.amount).toLocaleString('ru-RU')} ₽
              </div>
              <div className="flex items-center mt-1">
                <ArrowUpIcon className="h-4 w-4 text-red-500 mr-1" />
                <span className="text-red-500">
                  {Math.abs(Math.round(analysis.topGrowthCategory.growth))}% рост
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default SpendingAnalysis; 