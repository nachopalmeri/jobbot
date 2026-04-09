'use client';

import { Bell, User, ChevronDown, LogOut, Settings } from 'lucide-react';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import { ThemeToggle } from './theme-toggle';
import { cn } from './button';

export function Header() {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  return (
    <header className="sticky top-0 z-30 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold lg:hidden">JobBot</h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            className={cn(
              'inline-flex items-center justify-center rounded-md',
              'h-9 w-9 p-0',
              'bg-background border border-input hover:bg-accent hover:text-accent-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              'transition-all duration-200 active:scale-95 relative'
            )}
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground flex items-center justify-center">
              2
            </span>
          </button>

          <ThemeToggle />

          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className={cn(
                'flex items-center gap-2 rounded-md px-2 py-1.5',
                'hover:bg-accent transition-colors duration-200'
              )}
            >
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-4 w-4 text-primary" />
              </div>
              <span className="hidden sm:block text-sm font-medium">Usuario</span>
              <ChevronDown className={cn('h-4 w-4 transition-transform duration-200', isUserMenuOpen && 'rotate-180')} />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-md border bg-background shadow-lg animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="p-2">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium">Mi Cuenta</p>
                    <p className="text-xs text-muted-foreground">usuario@email.com</p>
                  </div>
                  <div className="my-1 h-px bg-border" />
                  <Link
                    href="/dashboard/perfil"
                    className={cn(
                      'flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm',
                      'hover:bg-accent hover:text-accent-foreground',
                      'transition-colors duration-150'
                    )}
                    onClick={() => setIsUserMenuOpen(false)}
                  >
                    <User className="h-4 w-4" />
                    Perfil
                  </Link>
                  <Link
                    href="/dashboard/configuracion"
                    className={cn(
                      'flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm',
                      'hover:bg-accent hover:text-accent-foreground',
                      'transition-colors duration-150'
                    )}
                    onClick={() => setIsUserMenuOpen(false)}
                  >
                    <Settings className="h-4 w-4" />
                    Configuración
                  </Link>
                  <div className="my-1 h-px bg-border" />
                  <button
                    onClick={handleLogout}
                    className={cn(
                      'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm',
                      'text-destructive hover:bg-destructive/10',
                      'transition-colors duration-150'
                    )}
                  >
                    <LogOut className="h-4 w-4" />
                    Cerrar sesión
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
