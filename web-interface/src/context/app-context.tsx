"use client";

import React, { createContext, useState, useContext, ReactNode } from 'react';

interface AppContextType {
  selectedRole: string | null;
  setSelectedRole: (role: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedRole, setSelectedRole] = useState<string | null>(null);

  return (
    <AppContext.Provider value={{ selectedRole, setSelectedRole }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
} 