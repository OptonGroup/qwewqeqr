const fs = require('fs');
const path = require('path');

// Генерируем BASE64 прозрачного изображения 1x1 пиксель
const transparentPixel = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';

// Функция для создания директории, если она не существует
function ensureDirectoryExists(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    console.log(`Создана директория: ${dirPath}`);
  }
}

// Функция для создания изображения
function createImage(filePath) {
  const buffer = Buffer.from(transparentPixel, 'base64');
  fs.writeFileSync(filePath, buffer);
  console.log(`Создано изображение: ${filePath}`);
}

// Основная функция
function createFallbackImages() {
  // Определяем, запущены ли мы в Docker
  const isDocker = process.env.NODE_ENV === 'production' || process.env.DOCKER === 'true';
  
  // В Docker базовая директория находится в текущей директории
  const baseDir = isDocker 
    ? path.join(process.cwd(), 'public', 'images', 'fallback')
    : path.join(__dirname, 'web-interface', 'public', 'images', 'fallback');
  
  console.log(`Создание fallback-изображений в директории: ${baseDir}`);
  
  // Создаем базовую директорию
  ensureDirectoryExists(baseDir);
  
  // Создаем заглушку no-image.jpg
  createImage(path.join(baseDir, 'no-image.jpg'));
  
  // Гендеры и типы образов
  const genders = ['male', 'female', 'any'];
  const outfitTypes = ['basic', 'casual', 'formal', 'evening', 'sport', 'beach', 'winter'];
  
  // Создаем директории и изображения для каждого гендера и типа
  for (const gender of genders) {
    for (const type of outfitTypes) {
      const typeDir = path.join(baseDir, gender, type);
      ensureDirectoryExists(typeDir);
      
      // Создаем 3 изображения для каждого типа
      for (let i = 1; i <= 3; i++) {
        createImage(path.join(typeDir, `${type}-${i}.jpg`));
      }
    }
  }
  
  console.log('Все fallback-изображения созданы успешно!');
}

// Запускаем функцию
createFallbackImages(); 