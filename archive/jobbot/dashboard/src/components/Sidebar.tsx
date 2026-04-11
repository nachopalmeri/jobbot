'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Search, 
  FileText, 
  CreditCard, 
  Settings, 
  Zap,
  LogOut,
  Menu,
  X,
  User
} from 'lucide-react';
import { cn } from '@/components/ui/button';
import { useState, useEffect } from 'react';

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Inicio' },
  { href: '/dashboard/buscar', icon: Search, label: 'Buscar' },
  { href: '/dashboard/postulaciones', icon: FileText, label: 'Postulaciones' },
  { href: '/dashboard/perfil', icon: User, label: 'Perfil' },
  { href: '/dashboard/suscripcion', icon: CreditCard, label: 'Suscripción' },
  { href: '/dashboard/configuracion', icon: Settings, label: 'Configuración' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  const SidebarContent = () => (
    <>
      <div className="p-6">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <Zap className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            JobBot
          </span>
        </Link>
      </div>
      
      <nav className="px-3 flex-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => isMobile && setIsMobileOpen(false)}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm font-medium',
                'transition-all duration-200',
                isActive 
                  ? 'bg-primary/10 text-primary' 
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className={cn('h-4 w-4', isActive && 'text-primary')} />
              <span>{item.label}</span>
              {isActive && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="bg-gradient-to-r from-amber-400 to-orange-500 rounded-xl p-4 text-white mb-4">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            <span className="font-semibold text-sm">Plan Free</span>
          </div>
          <p className="text-xs mt-1 opacity-90">Actualiza a Premium</p>
          <Link
            href="/dashboard/suscripcion"
            className="mt-3 block text-xs font-medium bg-white/20 rounded-md px-2 py-1.5 text-center hover:bg-white/30 transition-colors"
          >
            Ver planes
          </Link>
        </div>
        
        <button 
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 w-full text-sm font-medium',
            'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            'rounded-lg transition-colors duration-200'
          )}
        >
          <LogOut className="h-4 w-4" />
          <span>Cerrar sesión</span>
        </button>
      </div>
    </>
  );

  return (
    <>
      {isMobile && (
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="fixed top-3 left-4 z-50 lg:hidden p-2 rounded-md bg-background border shadow-sm"
          aria-label="Toggle menu"
        >
          {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      )}

      <aside className={cn(
        'fixed lg:static inset-y-0 left-0 z-40',
        'w-64 bg-background border-r border-border flex flex-col h-screen',
        'transition-transform duration-300 ease-out',
        isMobile ? (isMobileOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'
      )}>
        <SidebarContent />
      </aside>

      {isMobile && isMobileOpen && (
        <div 
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
    </>
  );
}
