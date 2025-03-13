"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Transaction, CategorySpending, MonthlyTrend } from '@/types/bank-statement';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import TransactionsTable from './transactions-table';
import SpendingPieChart from './charts/spending-pie-chart';
import MonthlySpendingTrendChart from './charts/monthly-spending-trend';
import SpendingAnalysis from './spending-analysis';
import RecommendedBudget from './recommended-budget';
import { FileUploadButton } from './file-upload-button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { formatDate, getCurrentMonthName } from '@/utils/date';
import { Download, Upload, RefreshCw } from 'lucide-react';

// Моковые данные для демонстрации
const mockTransactions: Transaction[] = [
  // Данные будут получены с сервера
];

const mockCategorySpending: CategorySpending[] = [
  { category: 'Продукты', amount: 15000 },
  { category: 'Транспорт', amount: 5000 },
  { category: 'Рестораны', amount: 8000 },
  { category: 'Развлечения', amount: 6000 },
  { category: 'Одежда', amount: 10000 },
  { category: 'Здоровье', amount: 4000 },
  { category: 'Жилье', amount: 30000 },
  { category: 'Красота', amount: 3000 },
  { category: 'Подписки', amount: 1500 },
  { category: 'Другое', amount: 5000 },
];

const mockPreviousMonthSpending: CategorySpending[] = [
  { category: 'Продукты', amount: 14000 },
  { category: 'Транспорт', amount: 4800 },
  { category: 'Рестораны', amount: 7000 },
  { category: 'Развлечения', amount: 6500 },
  { category: 'Одежда', amount: 9000 },
  { category: 'Здоровье', amount: 3500 },
  { category: 'Жилье', amount: 30000 },
  { category: 'Красота', amount: 2800 },
  { category: 'Подписки', amount: 1500 },
  { category: 'Другое', amount: 4800 },
];

const mockAverageMonthlySpending: CategorySpending[] = [
  { category: 'Продукты', amount: 14500 },
  { category: 'Транспорт', amount: 4900 },
  { category: 'Рестораны', amount: 7500 },
  { category: 'Развлечения', amount: 6200 },
  { category: 'Одежда', amount: 9500 },
  { category: 'Здоровье', amount: 3800 },
  { category: 'Жилье', amount: 30000 },
  { category: 'Красота', amount: 2900 },
  { category: 'Подписки', amount: 1500 },
  { category: 'Другое', amount: 4900 },
];

const mockMonthlyTrend: MonthlyTrend[] = [
  {
    month: 'Январь',
    categories: [
      { category: 'Продукты', amount: 14000 },
      { category: 'Транспорт', amount: 4800 },
      { category: 'Рестораны', amount: 7000 },
      { category: 'Другое', amount: 22000 },
    ]
  },
  {
    month: 'Февраль',
    categories: [
      { category: 'Продукты', amount: 14500 },
      { category: 'Транспорт', amount: 4900 },
      { category: 'Рестораны', amount: 7500 },
      { category: 'Другое', amount: 21000 },
    ]
  },
  {
    month: 'Март',
    categories: [
      { category: 'Продукты', amount: 15000 },
      { category: 'Транспорт', amount: 5000 },
      { category: 'Рестораны', amount: 8000 },
      { category: 'Другое', amount: 23000 },
    ]
  },
];

const DashboardPage = () => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categorySpending, setCategorySpending] = useState<CategorySpending[]>([]);
  const [previousMonthSpending, setPreviousMonthSpending] = useState<CategorySpending[]>([]);
  const [averageMonthlySpending, setAverageMonthlySpending] = useState<CategorySpending[]>([]);
  const [monthlyTrend, setMonthlyTrend] = useState<MonthlyTrend[]>([]);
  const [hasStatement, setHasStatement] = useState(false);
  const [totalIncome, setTotalIncome] = useState(120000); // Моковый доход
  const [startDate, setStartDate] = useState('01.01.2023');
  const [endDate, setEndDate] = useState('31.03.2023');

  useEffect(() => {
    // В реальном приложении здесь будет запрос к серверу для проверки наличия загруженной выписки
    // и получения данных из неё
    const hasExistingData = false;
    
    if (hasExistingData) {
      // Загрузка данных с сервера
      setIsLoading(true);
      // Имитация загрузки данных
      setTimeout(() => {
        setTransactions(mockTransactions);
        setCategorySpending(mockCategorySpending);
        setPreviousMonthSpending(mockPreviousMonthSpending);
        setAverageMonthlySpending(mockAverageMonthlySpending);
        setMonthlyTrend(mockMonthlyTrend);
        setHasStatement(true);
        setIsLoading(false);
      }, 1000);
    } else {
      // Использование моковых данных для демонстрации
      setTransactions(mockTransactions);
      setCategorySpending(mockCategorySpending);
      setPreviousMonthSpending(mockPreviousMonthSpending);
      setAverageMonthlySpending(mockAverageMonthlySpending);
      setMonthlyTrend(mockMonthlyTrend);
      setHasStatement(true);
    }
  }, []);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);

    // В реальном приложении здесь будет отправка файла на сервер и получение результатов обработки
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // Имитация загрузки и обработки файла
      setTimeout(() => {
        // Использование моковых данных
        setTransactions(mockTransactions);
        setCategorySpending(mockCategorySpending);
        setPreviousMonthSpending(mockPreviousMonthSpending);
        setAverageMonthlySpending(mockAverageMonthlySpending);
        setMonthlyTrend(mockMonthlyTrend);
        setHasStatement(true);
        setIsLoading(false);
      }, 2000);
    } catch (error) {
      console.error('Ошибка при загрузке файла:', error);
      setIsLoading(false);
    }
  };

  const handleRefreshData = () => {
    setIsLoading(true);
    
    // Имитация обновления данных
    setTimeout(() => {
      setTransactions(mockTransactions);
      setCategorySpending(mockCategorySpending);
      setPreviousMonthSpending(mockPreviousMonthSpending);
      setAverageMonthlySpending(mockAverageMonthlySpending);
      setMonthlyTrend(mockMonthlyTrend);
      setIsLoading(false);
    }, 1000);
  };

  const handleExportReport = () => {
    // В реальном приложении здесь будет запрос на генерацию и скачивание отчета
    alert('Отчет будет скачан в формате PDF');
  };

  if (!hasStatement) {
    return (
      <div className="container mx-auto py-12">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-3xl font-bold mb-6">Анализ банковской выписки</h1>
          <p className="text-gray-600 mb-8">
            Загрузите вашу выписку из Тинькофф банка в формате PDF или TXT для анализа расходов и получения рекомендаций по бюджету.
          </p>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-md">
                <FileUploadButton 
                  onFileSelected={handleFileUpload}
                  isLoading={isLoading}
                  accept=".pdf,.txt"
                  className="w-full"
                >
                  {isLoading ? 'Анализируем выписку...' : 'Загрузить банковскую выписку'}
                </FileUploadButton>
                <p className="text-sm text-gray-500 mt-4">
                  Поддерживаемые форматы: PDF, TXT. Максимальный размер файла: 10MB
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Финансовый анализ</h1>
        <div className="flex gap-2">
          <FileUploadButton
            onFileSelected={handleFileUpload}
            isLoading={isLoading}
            accept=".pdf,.txt"
            variant="outline"
          >
            <Upload className="h-4 w-4 mr-2" />
            Загрузить новую выписку
          </FileUploadButton>
          <Button variant="outline" onClick={handleRefreshData} disabled={isLoading}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Обновить
          </Button>
          <Button onClick={handleExportReport} disabled={isLoading}>
            <Download className="h-4 w-4 mr-2" />
            Скачать отчет
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full mb-8">
        <TabsList>
          <TabsTrigger value="overview">Обзор</TabsTrigger>
          <TabsTrigger value="transactions">Транзакции</TabsTrigger>
          <TabsTrigger value="budget">Бюджет</TabsTrigger>
          <TabsTrigger value="trends">Тренды</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <SpendingAnalysis
              currentMonthSpending={categorySpending}
              previousMonthSpending={previousMonthSpending}
              averageMonthlySpending={averageMonthlySpending}
              startDate={startDate}
              endDate={endDate}
            />
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Структура расходов</CardTitle>
                <CardDescription>
                  Распределение ваших трат по категориям за текущий период
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[350px]">
                <SpendingPieChart categorySpending={categorySpending} />
              </CardContent>
            </Card>
          </div>
          
          <Card>
            <CardHeader>
              <CardTitle>Тренд расходов по месяцам</CardTitle>
              <CardDescription>
                Как меняются ваши расходы по категориям с течением времени
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <MonthlySpendingTrendChart monthlyTrend={monthlyTrend} />
            </CardContent>
          </Card>
          
          <RecommendedBudget 
            categorySpending={categorySpending}
            totalIncome={totalIncome}
            month={getCurrentMonthName()}
          />
        </TabsContent>
        
        <TabsContent value="transactions">
          <Card>
            <CardHeader>
              <CardTitle>История транзакций</CardTitle>
              <CardDescription>
                Все транзакции за выбранный период
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TransactionsTable transactions={transactions} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="budget">
          <RecommendedBudget 
            categorySpending={categorySpending}
            totalIncome={totalIncome}
            month={getCurrentMonthName()}
          />
        </TabsContent>
        
        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Динамика расходов</CardTitle>
              <CardDescription>
                Изменение расходов по категориям с течением времени
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[500px]">
              <MonthlySpendingTrendChart monthlyTrend={monthlyTrend} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DashboardPage;