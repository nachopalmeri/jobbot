'use client';

import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { cn } from './button';

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, toggleTheme, mounted } = useTheme();

  if (!mounted) {
    return (
      <div className={cn('w-9 h-9 rounded-md bg-muted animate-pulse', className)} />
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'inline-flex items-center justify-center rounded-md text-sm font-medium',
        'h-9 w-9 p-0',
        'bg-background border border-input hover:bg-accent hover:text-accent-foreground',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'transition-all duration-200 active:scale-95',
        className
      )}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </button>
  );
}
