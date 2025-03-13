import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface Product {
  id: string;
  name: string;
  brand: string;
  price: number;
  sale_price: number;
  discount: number;
  image_url: string;
  product_url: string;
}

interface ClothingItem {
  type: string;
  color: string;
  description: string;
  gender: string;
  wb_products: Product[];
}

interface ImageAnalysisResultsProps {
  elements: ClothingItem[];
  analysis: string;
  image_path: string;
}

export const ImageAnalysisResults: React.FC<ImageAnalysisResultsProps> = ({
  elements,
  analysis,
  image_path,
}) => {
  return (
    <div className="space-y-8">
      <div className="bg-gray-50 p-6 rounded-lg">
        <h2 className="text-xl font-bold mb-4">Распознанная одежда:</h2>
        <ul className="list-disc pl-6 space-y-2">
          {elements.map((item, index) => (
            <li key={index}>
              <span className="font-semibold">{item.type}</span>: {item.color} {item.description}
            </li>
          ))}
        </ul>
      </div>

      <h2 className="text-2xl font-bold">Рекомендуемые товары</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {elements.map((item, itemIndex) => (
          item.wb_products && item.wb_products.length > 0 ? (
            item.wb_products.map((product, productIndex) => (
              <Card key={`${itemIndex}-${productIndex}`} className="overflow-hidden">
                <div className="relative">
                  <img 
                    src={product.image_url} 
                    alt={product.name} 
                    className="w-full h-64 object-cover"
                  />
                  <Badge className="absolute top-2 right-2 bg-gray-800 text-white">
                    {item.type}
                  </Badge>
                </div>
                <CardHeader className="p-4">
                  <CardTitle className="text-lg">{product.name}</CardTitle>
                  <div className="text-sm text-gray-500">{product.brand}</div>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                  <div className="flex justify-between items-center mb-4">
                    <div className="font-bold text-xl">
                      {product.sale_price} ₽
                    </div>
                    {product.discount > 0 && (
                      <div className="flex items-center">
                        <span className="text-gray-500 line-through text-sm mr-2">
                          {product.price} ₽
                        </span>
                        <Badge className="bg-red-500">-{product.discount}%</Badge>
                      </div>
                    )}
                  </div>
                  <Button 
                    className="w-full"
                    onClick={() => window.open(product.product_url, '_blank')}
                  >
                    Купить
                  </Button>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card key={`no-products-${itemIndex}`} className="col-span-3">
              <CardContent className="p-6">
                <p className="text-center text-gray-500">
                  Не найдено товаров для {item.type} {item.color}
                </p>
              </CardContent>
            </Card>
          )
        ))}
      </div>
    </div>
  );
}; 