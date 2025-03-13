import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface WildberriesProduct {
  id: string;
  name: string;
  brand: string;
  price: number;
  sale_price: number;
  discount: number;
  image_url: string;
  product_url: string;
}

export interface GarmentItem {
  id: string;
  name: string;
  description: string;
  price: number;
  oldPrice?: number;
  imageUrl: string;
  category: string;
  url?: string;
  gender?: string;
  wb_products?: WildberriesProduct[];
}

interface ProductCardProps {
  item: GarmentItem;
}

export const ProductCard: React.FC<ProductCardProps> = ({ item }) => {
  return (
    <div className="space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">{item.name}</h3>
        <p className="text-gray-600">{item.description}</p>
      </div>

      {item.wb_products && item.wb_products.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {item.wb_products.map((product, index) => (
            <Card key={`${item.id}-${index}`} className="overflow-hidden">
              <div className="relative">
                <img 
                  src={product.image_url} 
                  alt={product.name} 
                  className="w-full h-64 object-cover"
                />
                <Badge className="absolute top-2 right-2 bg-gray-800 text-white">
                  {item.category}
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
          ))}
        </div>
      ) : (
        <Card className="p-4">
          <p className="text-center text-gray-500">
            Не найдено товаров для {item.name}
          </p>
        </Card>
      )}
    </div>
  );
}; 