"use client";

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { CATEGORY_COLORS, CATEGORY_ICONS } from '@/constants';
import { CategorySpending } from '@/types/bank-statement';

interface RecommendedBudgetProps {
  categorySpending: CategorySpending[];
  totalIncome: number;
  month: string;
}

const RecommendedBudget = ({ categorySpending, totalIncome, month }: RecommendedBudgetProps) => {
  const budgetRecommendations = useMemo(() => {
    // Рассчитываем рекомендуемый бюджет на основе доходов и текущих трат
    const recommendedPercentages: Record<string, number> = {
      'Продукты': 25,
      'Жилье': 30,
      'Транспорт': 10,
      'Здоровье': 10,
      'Развлечения': 5,
      'Одежда': 5,
      'Рестораны': 5,
      'Красота': 3,
      'Подписки': 2,
      'Другое': 5,
    };
    
    const recommendations = Object.entries(recommendedPercentages).map(([category, percentage]) => {
      const recommendedAmount = (totalIncome * percentage) / 100;
      const currentSpending = categorySpending.find(item => item.category === category)?.amount || 0;
      const difference = recommendedAmount - currentSpending;
      const percentOfRecommended = currentSpending / recommendedAmount * 100;
      
      let status: 'normal' | 'warning' | 'danger' = 'normal';
      if (percentOfRecommended > 110) {
        status = 'danger';
      } else if (percentOfRecommended > 90) {
        status = 'warning';
      }
      
      return {
        category,
        recommendedAmount,
        currentSpending,
        difference,
        percentOfRecommended: Math.min(percentOfRecommended, 150), // Ограничиваем для отображения
        status
      };
    });
    
    return recommendations;
  }, [categorySpending, totalIncome]);

  return (
    <Card className="col-span-3">
      <CardHeader>
        <CardTitle>Рекомендуемый бюджет</CardTitle>
        <CardDescription>
          Анализ и рекомендации по распределению бюджета на {month}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {budgetRecommendations.map((item) => {
            const Icon = CATEGORY_ICONS[item.category as keyof typeof CATEGORY_ICONS] || CATEGORY_ICONS['Другое'];
            const color = CATEGORY_COLORS[item.category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS['Другое'];
            
            return (
              <div key={item.category} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon className="h-4 w-4" style={{ color }} />
                    <span className="font-medium">{item.category}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    <span>{Math.round(item.currentSpending).toLocaleString('ru-RU')} ₽</span>
                    <span className="mx-1">/</span>
                    <span>{Math.round(item.recommendedAmount).toLocaleString('ru-RU')} ₽</span>
                  </div>
                </div>
                <Progress 
                  value={item.percentOfRecommended} 
                  className={
                    item.status === 'danger' 
                      ? 'bg-gray-200 text-red-500' 
                      : item.status === 'warning'
                        ? 'bg-gray-200 text-yellow-500'
                        : 'bg-gray-200'
                  }
                  indicatorClassName={
                    item.status === 'danger' 
                      ? 'bg-red-500' 
                      : item.status === 'warning'
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                  }
                />
                <div className="text-xs text-gray-500">
                  {item.difference > 0 
                    ? `Вы можете потратить еще ${Math.round(item.difference).toLocaleString('ru-RU')} ₽`
                    : `Превышение на ${Math.abs(Math.round(item.difference)).toLocaleString('ru-RU')} ₽`}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default RecommendedBudget; 