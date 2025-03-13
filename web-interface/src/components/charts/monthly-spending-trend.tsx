"use client";

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { MonthlyTrend } from '@/types/bank-statement';
import { CATEGORY_COLORS } from '@/constants';

interface MonthlySpendingTrendChartProps {
  monthlyTrend: MonthlyTrend[];
}

const MonthlySpendingTrendChart: React.FC<MonthlySpendingTrendChartProps> = ({ monthlyTrend }) => {
  // Преобразуем данные для отображения на графике
  const chartData = useMemo(() => {
    return monthlyTrend.map(item => {
      const result: Record<string, any> = { month: item.month };
      
      item.categories.forEach(category => {
        result[category.category] = category.amount;
      });
      
      return result;
    });
  }, [monthlyTrend]);

  // Получаем уникальные категории из всех месяцев
  const categories = useMemo(() => {
    const allCategories = new Set<string>();
    
    monthlyTrend.forEach(month => {
      month.categories.forEach(category => {
        allCategories.add(category.category);
      });
    });
    
    return Array.from(allCategories);
  }, [monthlyTrend]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const totalAmount = payload.reduce((sum: number, entry: any) => sum + (entry.value || 0), 0);
      
      return (
        <div className="bg-white p-3 shadow-md rounded-md border">
          <p className="font-medium mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={`tooltip-${index}`} className="flex justify-between items-center mb-1">
              <div className="flex items-center">
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm">{entry.name}</span>
              </div>
              <span className="text-sm font-medium">
                {Math.round(entry.value).toLocaleString('ru-RU')} ₽
              </span>
            </div>
          ))}
          <div className="border-t mt-2 pt-2 flex justify-between">
            <span className="font-medium">Всего:</span>
            <span className="font-medium">
              {Math.round(totalAmount).toLocaleString('ru-RU')} ₽
            </span>
          </div>
        </div>
      );
    }
    
    return null;
  };

  const formatYAxis = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(0)}K`;
    }
    return value;
  };

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis tickFormatter={formatYAxis} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {categories.map((category, index) => (
            <Bar
              key={`bar-${index}`}
              dataKey={category}
              stackId="a"
              fill={CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS['Другое']}
              name={category}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MonthlySpendingTrendChart; 