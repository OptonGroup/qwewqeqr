import React from 'react';
import { Pie } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  ArcElement, 
  Tooltip, 
  Legend,
  Colors
} from 'chart.js';
import { CategorySpending, CATEGORY_COLORS } from '@/types';
import { formatCurrency } from '@/utils';

// Регистрируем необходимые компоненты Chart.js
ChartJS.register(ArcElement, Tooltip, Legend, Colors);

interface SpendingByCategoryChartProps {
  data: CategorySpending[];
  className?: string;
}

export function SpendingByCategoryChart({ 
  data, 
  className
}: SpendingByCategoryChartProps) {
  // Отсортируем данные по сумме в порядке убывания
  const sortedData = [...data].sort((a, b) => b.Сумма - a.Сумма);
  
  // Если категорий больше 8, объединяем остальные в "Другое"
  let chartData = sortedData;
  if (sortedData.length > 8) {
    const topCategories = sortedData.slice(0, 7);
    const otherCategories = sortedData.slice(7);
    
    const otherSum = otherCategories.reduce((sum, item) => sum + item.Сумма, 0);
    chartData = [
      ...topCategories,
      { Категория: 'Другое', Сумма: otherSum }
    ];
  }
  
  // Подготавливаем данные для диаграммы
  const chartLabels = chartData.map(item => item.Категория);
  const chartValues = chartData.map(item => item.Сумма);
  const backgroundColors = chartData.map(item => {
    return CATEGORY_COLORS[item.Категория] || 'hsl(0, 0%, 70%)';
  });
  
  const chartConfig = {
    labels: chartLabels,
    datasets: [
      {
        data: chartValues,
        backgroundColor: backgroundColors,
        borderColor: 'rgba(255, 255, 255, 0.5)',
        borderWidth: 1,
        hoverOffset: 15,
      },
    ],
  };
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          boxWidth: 15,
          padding: 15,
          font: {
            size: 12,
          },
          generateLabels: function(chart: any) {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              return data.labels.map((label: string, i: number) => {
                const value = data.datasets[0].data[i];
                const formattedValue = formatCurrency(value);
                
                return {
                  text: `${label}: ${formattedValue}`,
                  fillStyle: data.datasets[0].backgroundColor[i],
                  strokeStyle: data.datasets[0].borderColor[i],
                  lineWidth: data.datasets[0].borderWidth,
                  hidden: false,
                  index: i
                };
              });
            }
            return [];
          }
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            let label = context.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed !== null) {
              label += formatCurrency(context.parsed);
            }
            return label;
          }
        }
      }
    },
    layout: {
      padding: 10
    },
  };

  return (
    <div className={`w-full h-[400px] ${className || ''}`}>
      <Pie data={chartConfig} options={options} />
    </div>
  );
} 