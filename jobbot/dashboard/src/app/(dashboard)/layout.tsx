'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { Header } from '@/components/ui/header';
import { ToastProvider } from '@/components/ui/toast';
import { cn } from '@/components/ui/button';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
    } else {
      setIsAuthenticated(true);
    }
  }, []);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin h-10 w-10 border-4 border-primary border-t-transparent rounded-full" />
          <p className="text-sm text-muted-foreground">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <ToastProvider>
      <div className="min-h-screen bg-background">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <main className={cn(
              'flex-1 overflow-y-auto',
              'p-4 lg:p-6'
            )}>
              {children}
            </main>
          </div>
        </div>
      </div>
    </ToastProvider>
  );
}
