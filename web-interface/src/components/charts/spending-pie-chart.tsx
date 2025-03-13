"use client";

import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { CategorySpending } from '@/types/bank-statement';
import { CATEGORY_COLORS } from '@/constants';

interface SpendingPieChartProps {
  categorySpending: CategorySpending[];
}

const SpendingPieChart: React.FC<SpendingPieChartProps> = ({ categorySpending }) => {
  const data = useMemo(() => {
    return categorySpending.map(item => ({
      name: item.category,
      value: item.amount,
      color: CATEGORY_COLORS[item.category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS['Другое']
    }));
  }, [categorySpending]);

  const totalSpending = useMemo(() => {
    return categorySpending.reduce((sum, item) => sum + item.amount, 0);
  }, [categorySpending]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = ((data.value / totalSpending) * 100).toFixed(1);
      
      return (
        <div className="bg-white p-3 shadow-md rounded-md border">
          <p className="font-medium">{data.name}</p>
          <p className="text-gray-600">{Math.round(data.value).toLocaleString('ru-RU')} ₽</p>
          <p className="text-gray-500">{percentage}% от общих расходов</p>
        </div>
      );
    }
    
    return null;
  };

  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    index,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    // Отображаем процент только для сегментов, которые занимают более 5% диаграммы
    if (percent < 0.05) return null;

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  const CustomLegend = ({ payload }: any) => {
    return (
      <ul className="flex flex-wrap justify-center gap-4 mt-4">
        {payload.map((entry: any, index: number) => (
          <li key={`item-${index}`} className="flex items-center">
            <div
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm">{entry.value}</span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomizedLabel}
            outerRadius="80%"
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SpendingPieChart; 