# 🎨 JobBot Dashboard

Dashboard moderno y profesional para la plataforma JobBot SaaS.

---

## 📋 Tabla de Contenidos

- [Overview](#-overview)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Páginas](#-páginas)
- [Componentes UI](#-componentes-ui)
- [State Management](#-state-management)
- [Autenticación](#-autenticación)
- [Cómo Agregar Nuevas Páginas](#-cómo-agregar-nuevas-páginas)
- [Testing](#-testing)
- [Despliegue](#-despliegue)

---

## 🌟 Overview

El Dashboard de JobBot es una aplicación web moderna construida con Next.js que proporciona:

- 🔐 **Autenticación completa**: Login, registro, JWT, refresh tokens
- 📊 **Dashboard analytics**: Métricas en tiempo real
- 💼 **Gestión de jobs**: Buscar, filtrar, postular
- 👤 **Perfil de usuario**: Datos personales, preferencias, CV
- 💳 **Sistema de suscripción**: Planes y pagos integrados
- 🎨 **Dark mode**: Toggle y persistencia
- 📱 **Responsive**: Mobile-first design
- ⚡ **Alto rendimiento**: App Router, server components

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnología | Versión | Propósito |
|-----------|------------|---------|-----------|
| Framework | Next.js | 16.2.1 | App Router, SSR/SSG |
| Language | TypeScript | 5.x | Type safety |
| Styling | Tailwind CSS | v4 | Utility-first CSS |
| UI Library | shadcn/ui | latest | Componentes accesibles |
| State Client | Zustand | 4.5+ | Global state |
| State Server | TanStack Query | 5.17+ | Server state, caching |
| Animations | Framer Motion | 11.x | Transiciones suaves |
| Icons | Lucide React | 0.312 | Iconografía |
| Testing | Vitest | 1.2+ | Unit testing |
| Testing | Testing Library | 14.x | Component testing |

---

## 📁 Estructura del Proyecto

```
dashboard/
├── 📁 src/
│   ├── 📁 app/                    # Next.js App Router
│   │   ├── 📁 (auth)/             # Grupo de rutas: autenticación
│   │   │   ├── 📄 layout.tsx      # Layout compartido auth
│   │   │   ├── 📁 login/
│   │   │   │   └── 📄 page.tsx    # Página de login
│   │   │   └── 📁 register/
│   │   │       └── 📄 page.tsx    # Página de registro
│   │   │
│   │   ├── 📁 (dashboard)/        # Grupo de rutas: dashboard
│   │   │   ├── 📄 layout.tsx      # Layout con sidebar
│   │   │   ├── 📄 page.tsx        # Home/Dashboard
│   │   │   ├── 📁 buscar/
│   │   │   │   └── 📄 page.tsx    # Buscar empleos
│   │   │   ├── 📁 postulaciones/
│   │   │   │   └── 📄 page.tsx    # Mis postulaciones
│   │   │   ├── 📁 perfil/
│   │   │   │   └── 📄 page.tsx    # Perfil de usuario
│   │   │   ├── 📁 suscripcion/
│   │   │   │   └── 📄 page.tsx    # Planes y pagos
│   │   │   └── 📁 configuracion/
│   │   │       └── 📄 page.tsx    # Configuración
│   │   │
│   │   ├── 📄 layout.tsx          # Root layout
│   │   ├── 📄 page.tsx            # Landing/Redirect
│   │   └── 📄 globals.css         # Estilos globales
│   │
│   ├── 📁 components/             # Componentes React
│   │   ├── 📁 ui/                 # Componentes UI (12)
│   │   │   ├── 📄 button.tsx      # Button con variants
│   │   │   ├── 📄 card.tsx        # Card container
│   │   │   ├── 📄 input.tsx       # Input con validación
│   │   │   ├── 📄 badge.tsx       # Badge/status
│   │   │   ├── 📄 dialog.tsx      # Modal/dialog
│   │   │   ├── 📄 toast.tsx       # Notifications
│   │   │   ├── 📄 skeleton.tsx    # Loading states
│   │   │   ├── 📄 empty-state.tsx # Estados vacíos
│   │   │   ├── 📄 theme-toggle.tsx # Dark mode switch
│   │   │   ├── 📄 header.tsx      # Header component
│   │   │   └── 📄 index.ts        # Exports
│   │   │
│   │   └── 📄 Sidebar.tsx         # Navegación lateral
│   │
│   ├── 📁 hooks/                  # Custom hooks
│   │   ├── 📄 useTheme.ts         # Theme management
│   │   └── 📄 useAuth.ts          # Auth logic
│   │
│   ├── 📁 stores/                 # Zustand stores
│   │   └── 📄 index.ts            # Global store
│   │
│   ├── 📁 types/                  # TypeScript types
│   │   └── 📄 index.ts            # Type definitions
│   │
│   └── 📁 lib/                    # Utilities
│       └── 📄 utils.ts            # Helper functions
│
├── 📁 __tests__/                  # Tests (2000 líneas)
│   ├── 📄 setup.ts                # Test setup
│   ├── 📄 components.test.tsx     # Component tests
│   ├── 📄 hooks.test.ts           # Hook tests
│   └── 📄 integration.test.tsx      # Integration tests
│
├── 📁 public/                     # Static assets
├── 📄 .impeccable.md             # Contexto de diseño
├── 📄 COMPONENTS.md              # Doc de componentes
├── 📄 package.json               # Dependencias
├── 📄 next.config.ts             # Next.js config
├── 📄 tailwind.config.ts         # Tailwind config
├── 📄 tsconfig.json              # TypeScript config
└── 📄 vitest.config.ts           # Vitest config
```

---

## 📄 Páginas

### 1. 🔐 Autenticación

| Página | Ruta | Descripción |
|--------|------|-------------|
| Login | `/login` | Inicio de sesión con email/password |
| Register | `/register` | Registro con validación |

**Features:**
- Validación de formularios
- Mensajes de error amigables
- Redirección post-login
- Link a términos y condiciones

### 2. 🏠 Dashboard Home

| Página | Ruta | Descripción |
|--------|------|-------------|
| Home | `/dashboard` | Estadísticas y overview |

**Features:**
- Stats cards con métricas
- Jobs recientes
- Quick actions
- Gráficos de actividad

### 3. 🔍 Buscar Empleos

| Página | Ruta | Descripción |
|--------|------|-------------|
| Buscar | `/dashboard/buscar` | Búsqueda de empleos |

**Features:**
- Filtros avanzados (keywords, ubicación, modalidad)
- Búsqueda en tiempo real
- Paginación
- Cards de jobs con match score

### 4. 📝 Postulaciones

| Página | Ruta | Descripción |
|--------|------|-------------|
| Postulaciones | `/dashboard/postulaciones` | Gestión de postulaciones |

**Features:**
- Lista de postulaciones
- Estado de cada postulación
- Fechas de seguimiento
- Eliminar postulación

### 5. 👤 Perfil

| Página | Ruta | Descripción |
|--------|------|-------------|
| Perfil | `/dashboard/perfil` | Perfil del usuario |

**Features:**
- Editar datos personales
- Subir/actualizar CV
- Preferencias de búsqueda
- Cambiar contraseña

### 6. 💳 Suscripción

| Página | Ruta | Descripción |
|--------|------|-------------|
| Suscripción | `/dashboard/suscripcion` | Planes y pagos |

**Features:**
- Comparación de planes (Free, Starter, Pro, Premium)
- Checkout integrado (Stripe/MercadoPago)
- Historial de pagos
- Cancelar/upgrade

### 7. ⚙️ Configuración

| Página | Ruta | Descripción |
|--------|------|-------------|
| Configuración | `/dashboard/configuracion` | Configuración de cuenta |

**Features:**
- Preferencias de notificaciones
- Integraciones (LinkedIn, GitHub)
- Facturación
- Eliminar cuenta

---

## 🧩 Componentes UI

### Componentes Core (12)

| Componente | Props | Descripción |
|------------|-------|-------------|
| `Button` | `variant`, `size`, `loading` | Botón con múltiples estilos |
| `Card` | `className`, `children` | Contenedor con sombra |
| `Input` | `label`, `error`, `helperText` | Input con validación |
| `Badge` | `variant` | Badge de status |
| `Dialog` | `open`, `onClose`, `title` | Modal accesible |
| `Toast` | `type`, `message` | Notificaciones |
| `Skeleton` | `width`, `height` | Loading placeholder |
| `EmptyState` | `icon`, `title`, `action` | Estado vacío |
| `ThemeToggle` | - | Switch claro/oscuro |
| `Header` | `user`, `notifications` | Header con menú |
| `Sidebar` | `items`, `active` | Navegación lateral |
| `Select` | `options`, `value`, `onChange` | Dropdown estilizado |

### Ejemplo de Uso

```tsx
// Card con contenido
<Card className="p-6">
  <h2 className="text-xl font-bold">Título</h2>
  <p>Contenido de la card...</p>
  <Button variant="primary">Acción</Button>
</Card>

// Formulario
<form>
  <Input
    label="Email"
    type="email"
    error={errors.email}
    helperText="Tu correo de trabajo"
  />
  <Button type="submit" loading={isSubmitting}>
    Guardar
  </Button>
</form>
```

---

## 🗄️ State Management

### Zustand Store

```typescript
// stores/index.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  // User
  user: User | null
  setUser: (user: User | null) => void
  
  // Theme
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  
  // Jobs
  jobs: Job[]
  setJobs: (jobs: Job[]) => void
  addJob: (job: Job) => void
  
  // UI
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      
      theme: 'system',
      setTheme: (theme) => set({ theme }),
      
      jobs: [],
      setJobs: (jobs) => set({ jobs }),
      addJob: (job) => set((state) => ({ 
        jobs: [...state.jobs, job] 
      })),
      
      sidebarOpen: false,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: 'jobbot-storage',
      partialize: (state) => ({ theme: state.theme }),
    }
  )
)
```

### TanStack Query (Server State)

```typescript
// hooks/useJobs.ts
import { useQuery, useMutation } from '@tanstack/react-query'

export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const res = await fetch('/api/jobs', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return res.json()
    }
  })
}

export function useSearchJobs() {
  return useMutation({
    mutationFn: async (params: SearchParams) => {
      const res = await fetch('/api/jobs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(params)
      })
      return res.json()
    }
  })
}
```

---

## 🔐 Autenticación

### Flujo JWT

```typescript
// hooks/useAuth.ts
export function useAuth() {
  const { user, setUser } = useStore()
  
  const login = async (email: string, password: string) => {
    const res = await fetch('/api/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    
    const data = await res.json()
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    setUser(data.user)
  }
  
  const logout = async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }
  
  const refresh = async () => {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        refresh_token: localStorage.getItem('refresh_token')
      })
    })
    
    const data = await res.json()
    localStorage.setItem('access_token', data.access_token)
  }
  
  return { user, login, logout, refresh }
}
```

### Protected Route

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')
  
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*']
}
```

---

## ➕ Cómo Agregar Nuevas Páginas

### 1. Crear Estructura de Archivos

```bash
# Nueva página en el dashboard
mkdir -p src/app/(dashboard)/nueva-pagina
touch src/app/(dashboard)/nueva-pagina/page.tsx
```

### 2. Implementar la Página

```tsx
// src/app/(dashboard)/nueva-pagina/page.tsx
'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function NuevaPagina() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Nueva Página</h1>
      
      <Card className="p-6">
        <p>Contenido de la página...</p>
        <Button>Acción</Button>
      </Card>
    </div>
  )
}
```

### 3. Agregar al Sidebar

```tsx
// En Sidebar.tsx
const menuItems = [
  { icon: Home, label: 'Dashboard', href: '/dashboard' },
  { icon: Search, label: 'Buscar', href: '/dashboard/buscar' },
  // ... otros items
  { icon: NewIcon, label: 'Nueva Página', href: '/dashboard/nueva-pagina' },
]
```

### 4. Crear Tests

```tsx
// __tests__/nueva-pagina.test.tsx
import { render, screen } from '@testing-library/react'
import NuevaPagina from '@/app/(dashboard)/nueva-pagina/page'

describe('NuevaPagina', () => {
  it('renders correctly', () => {
    render(<NuevaPagina />)
    expect(screen.getByText('Nueva Página')).toBeInTheDocument()
  })
})
```

---

## 🧪 Testing

### Configuración

**Vitest + Testing Library**

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', '__tests__/']
    }
  }
})
```

### Ejecutar Tests

```bash
# Modo watch (desarrollo)
npm test

# Una vez
npm run test:run

# Con UI interactiva
npm run test:ui

# Coverage
npm run test:coverage
```

### Tests Disponibles (2000 líneas)

| Suite | Tests | Descripción |
|-------|-------|-------------|
| `components.test.tsx` | 45 | Tests de componentes UI |
| `hooks.test.ts` | 20 | Tests de hooks |
| `integration.test.tsx` | 15 | Tests de integración |
| `auth.test.tsx` | 12 | Tests de autenticación |

### Ejemplo de Test

```tsx
// __tests__/button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })
  
  it('handles click', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click me</Button>)
    fireEvent.click(screen.getByText('Click me'))
    expect(onClick).toHaveBeenCalled()
  })
  
  it('shows loading state', () => {
    render(<Button loading>Loading</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

---

## 🚀 Despliegue

### Build de Producción

```bash
# Variables de entorno
cp .env.local.example .env.local
# Editar .env.local

# Build
npm run build

# Iniciar
npm start
```

### Variables de Entorno

```env
# API
NEXT_PUBLIC_API_URL=https://api.jobbot.ar

# Auth
NEXT_PUBLIC_JWT_EXPIRY=3600

# Feature flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_PAYMENTS=true
```

### Docker

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.jobbot.ar
```

---

## 📚 Recursos

- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Zustand](https://docs.pmnd.rs/zustand)
- [TanStack Query](https://tanstack.com/query/latest)
- [Framer Motion](https://www.framer.com/motion/)

---

<p align="center">
  <strong>JobBot Dashboard</strong>
  <br>
  Next.js 16 • TypeScript • Tailwind v4
</p>
