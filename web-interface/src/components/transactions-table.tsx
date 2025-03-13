"use client";

import React, { useState } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { SearchIcon, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Transaction, TransactionTableRow } from '@/types';
import { formatCurrency, formatDate, getAmountColorClass, generateId } from '@/utils';

function prepareTransactions(transactions: Transaction[]): TransactionTableRow[] {
  return transactions.map(transaction => ({
    ...transaction,
    id: generateId(),
  }));
}

export function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'Дата_операции', desc: true }
  ]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  
  const data = React.useMemo(() => 
    prepareTransactions(transactions), [transactions]
  );
  
  // Получаем уникальные категории для фильтра
  const uniqueCategories = React.useMemo(() => {
    const categories = new Set<string>();
    transactions.forEach(t => categories.add(t.Категория));
    return Array.from(categories).sort();
  }, [transactions]);
  
  const columns: ColumnDef<TransactionTableRow>[] = [
    {
      accessorKey: 'Дата_операции',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Дата
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      cell: ({ row }) => {
        const date = row.getValue('Дата_операции') as string;
        return <div>{formatDate(date, { day: 'numeric', month: 'short', year: 'numeric' })}</div>;
      },
    },
    {
      accessorKey: 'Описание',
      header: 'Описание',
      cell: ({ row }) => {
        const description = row.getValue('Описание') as string;
        return <div className="font-medium">{description}</div>;
      },
    },
    {
      accessorKey: 'Категория',
      header: 'Категория',
      cell: ({ row }) => {
        const category = row.getValue('Категория') as string;
        return <div className="text-sm">{category}</div>;
      },
      filterFn: (row, id, value) => {
        return value.length === 0 || value.includes(row.getValue(id));
      },
    },
    {
      accessorKey: 'Сумма',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="justify-end"
          >
            Сумма
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      cell: ({ row }) => {
        const amount = row.getValue('Сумма') as number;
        const colorClass = getAmountColorClass(amount);
        return (
          <div className={`text-right font-semibold ${colorClass}`}>
            {formatCurrency(amount)}
          </div>
        );
      },
    },
    {
      accessorKey: 'Тип',
      header: 'Тип',
      cell: ({ row }) => {
        const type = row.getValue('Тип') as string;
        return <div className="text-sm">{type}</div>;
      },
      filterFn: (row, id, value) => {
        return value.length === 0 || value.includes(row.getValue(id));
      },
    },
  ];
  
  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility: {
        Тип: false, // Скрываем столбец типа, т.к. это уже видно из суммы
      },
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  });
  
  // Устанавливаем фильтры для категории и типа
  React.useEffect(() => {
    if (categoryFilter) {
      table.getColumn('Категория')?.setFilterValue([categoryFilter]);
    } else {
      table.getColumn('Категория')?.setFilterValue([]);
    }
    
    if (typeFilter) {
      table.getColumn('Тип')?.setFilterValue([typeFilter]);
    } else {
      table.getColumn('Тип')?.setFilterValue([]);
    }
  }, [table, categoryFilter, typeFilter]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row items-center justify-between">
        <div className="flex items-center w-full sm:w-auto">
          <SearchIcon className="absolute ml-3 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Поиск по описанию..."
            value={(table.getColumn('Описание')?.getFilterValue() as string) ?? ''}
            onChange={(event) => table.getColumn('Описание')?.setFilterValue(event.target.value)}
            className="pl-9 w-full sm:w-[300px]"
          />
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <Select 
            value={categoryFilter} 
            onValueChange={setCategoryFilter}
          >
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="Категория" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Все категории</SelectItem>
              {uniqueCategories.map(category => (
                <SelectItem key={category} value={category}>
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select 
            value={typeFilter} 
            onValueChange={setTypeFilter}
          >
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="Тип" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Все операции</SelectItem>
              <SelectItem value="Доход">Доходы</SelectItem>
              <SelectItem value="Расход">Расходы</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="rounded-md border">
        <div className="relative w-full overflow-auto">
          <table className="w-full caption-bottom text-sm">
            <thead className="[&_tr]:border-b">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="border-b transition-colors">
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="h-12 px-4 text-left align-middle font-medium">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b transition-colors hover:bg-muted/50"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="p-4 align-middle">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={columns.length} className="h-24 text-center">
                    Нет данных о транзакциях
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Показано {table.getFilteredRowModel().rows.length} из {data.length} транзакций
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="text-sm">
            Страница {table.getState().pagination.pageIndex + 1} из{' '}
            {table.getPageCount()}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
} 