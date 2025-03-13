export interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  category: string;
  type: 'income' | 'expense';
}

export interface CategorySpending {
  category: string;
  amount: number;
}

export interface MonthlyTrend {
  month: string;
  categories: CategorySpending[];
}

export interface BankStatementMetadata {
  accountNumber: string;
  period: {
    from: string;
    to: string;
  };
  owner: string;
  bank: string;
}

export interface SpendingReport {
  totalExpenses: number;
  totalIncome: number;
  balance: number;
  categorySpending: CategorySpending[];
  monthlyTrend: MonthlyTrend[];
  topExpenseCategories: CategorySpending[];
  recommendations: BudgetRecommendation[];
}

export interface BudgetRecommendation {
  category: string;
  currentSpending: number;
  recommendedSpending: number;
  savingPotential: number;
  recommendation: string;
}

export interface FinancialSummary {
  totalIncome: number;
  totalExpenses: number;
  balance: number;
  savingRate: number;
  monthlyAverage: {
    income: number;
    expenses: number;
    savings: number;
  };
} 