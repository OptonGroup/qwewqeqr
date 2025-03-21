import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../styles/globals.css';
import { AppProvider } from '@/context/app-context';

const inter = Inter({ subsets: ['latin', 'cyrillic'] });

export const metadata: Metadata = {
  title: 'Анализатор банковских выписок',
  description: 'Инструмент для анализа выписок Тинькофф банка',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="light">
      <body className={inter.className}>
        <AppProvider>
          {children}
        </AppProvider>
      </body>
    </html>
  );
} 