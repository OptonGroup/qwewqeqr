"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import StylistAssistant from '@/components/assistants/stylist-assistant';
import CosmetologistAssistant from '@/components/assistants/cosmetologist-assistant';
import NutritionistAssistant from '@/components/assistants/nutritionist-assistant';
import DesignerAssistant from '@/components/assistants/designer-assistant';
import { Palette, Shirt, Salad, Sparkles } from 'lucide-react';
import { ImageUploader } from '@/components/ImageUploader';
import { ImageAnalysisResults } from '@/components/ImageAnalysisResults';

export default function Home() {
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRoleSelect = (role: string) => {
    setSelectedRole(role);
  };

  const handleImageUpload = (file: File) => {
    setSelectedImage(file);
    setImageUrl(URL.createObjectURL(file));
  };

  const handleAnalyzeImage = async () => {
    if (!selectedImage) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedImage);

      const response = await fetch('http://localhost:8000/analyze-image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Ошибка при анализе изображения');
      }

      const results = await response.json();
      setAnalysisResults(results);
    } catch (error) {
      console.error('Ошибка:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Если роль не выбрана, показываем страницу выбора
  if (!selectedRole) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-5xl w-full">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold tracking-tight mb-2">Шопинг-ассистент</h1>
            <p className="text-xl text-muted-foreground">
              Ваш персональный помощник для умного шопинга
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Стилист */}
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="text-center">
                <div className="mx-auto p-3 rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mb-2">
                  <Shirt className="w-8 h-8 text-primary" />
                </div>
                <CardTitle>Стилист</CardTitle>
                <CardDescription>
                  Создаст идеальный гардероб по вашим предпочтениям
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center text-sm text-muted-foreground">
                <p>Подбор образов и капсульных гардеробов</p>
                <p>Поиск по фото из Pinterest</p>
                <p>Советы по комбинированию одежды</p>
              </CardContent>
              <CardFooter>
                <Button onClick={() => handleRoleSelect('stylist')} className="w-full">
                  Выбрать
                </Button>
              </CardFooter>
            </Card>

            {/* Косметолог */}
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="text-center">
                <div className="mx-auto p-3 rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mb-2">
                  <Sparkles className="w-8 h-8 text-primary" />
                </div>
                <CardTitle>Косметолог</CardTitle>
                <CardDescription>
                  Подберет идеальный уход под ваш тип кожи
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center text-sm text-muted-foreground">
                <p>Анализ типа кожи и потребностей</p>
                <p>Подбор средств ухода</p>
                <p>Рекомендации с учетом образа жизни</p>
              </CardContent>
              <CardFooter>
                <Button onClick={() => handleRoleSelect('cosmetologist')} className="w-full">
                  Выбрать
                </Button>
              </CardFooter>
            </Card>

            {/* Нутрициолог */}
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="text-center">
                <div className="mx-auto p-3 rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mb-2">
                  <Salad className="w-8 h-8 text-primary" />
                </div>
                <CardTitle>Нутрициолог</CardTitle>
                <CardDescription>
                  Составит оптимальную продуктовую корзину
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center text-sm text-muted-foreground">
                <p>Расчет КБЖУ и калорийности</p>
                <p>Подбор продуктов под бюджет</p>
                <p>Анализ банковских выписок для оптимизации трат</p>
              </CardContent>
              <CardFooter>
                <Button onClick={() => handleRoleSelect('nutritionist')} className="w-full">
                  Выбрать
                </Button>
              </CardFooter>
            </Card>

            {/* Дизайнер */}
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="text-center">
                <div className="mx-auto p-3 rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mb-2">
                  <Palette className="w-8 h-8 text-primary" />
                </div>
                <CardTitle>Дизайнер</CardTitle>
                <CardDescription>
                  Поможет обустроить ваш интерьер
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center text-sm text-muted-foreground">
                <p>Подбор мебели и декора</p>
                <p>Визуализация интерьерных решений</p>
                <p>Советы по стилю и цветовым сочетаниям</p>
              </CardContent>
              <CardFooter>
                <Button onClick={() => handleRoleSelect('designer')} className="w-full">
                  Выбрать
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </main>
    );
  }

  // Показываем соответствующего ассистента в зависимости от выбранной роли
  return (
    <main className="min-h-screen bg-background">
      <StylistAssistant />
    </main>
  );
} 