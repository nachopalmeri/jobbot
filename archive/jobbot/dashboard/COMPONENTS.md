# JobBot Dashboard - Component Documentation

## Overview

JobBot Dashboard es una aplicación Next.js con diseño moderno, limpio y profesional. Utiliza Tailwind CSS v4 para estilos, shadcn/ui como base para componentes, y Framer Motion para animaciones sutiles.

## Componentes UI

### Button
Botón reutilizable con múltiples variantes y estados.

```tsx
import { Button } from '@/components/ui/button';

<Button variant="default" size="lg" isLoading={false}>
  Click me
</Button>
```

**Props:**
- `variant`: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
- `size`: 'default' | 'sm' | 'lg' | 'icon'
- `isLoading`: boolean
- `disabled`: boolean

### Card
Contenedor de contenido con estilos consistentes.

```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Título</CardTitle>
  </CardHeader>
  <CardContent>Contenido</CardContent>
</Card>
```

### Input
Campo de entrada con validación y estados de error.

```tsx
import { Input } from '@/components/ui/input';

<Input 
  type="email" 
  placeholder="email@example.com" 
  error={errors.email}
/>
```

### Badge
Etiquetas de estado con diferentes variantes.

```tsx
import { Badge } from '@/components/ui/badge';

<Badge variant="success">Activo</Badge>
```

**Variants:** default, secondary, destructive, outline, success, warning

### Select
Selector de opciones con estilos consistentes.

```tsx
import { Select } from '@/components/ui/select';

<Select value={value} onChange={handleChange}>
  <option value="1">Opción 1</option>
</Select>
```

### Dialog
Modal para confirmaciones y formularios.

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Título</DialogTitle>
    </DialogHeader>
    {/* Contenido */}
  </DialogContent>
</Dialog>
```

### ThemeToggle
Botón para alternar entre modo claro y oscuro.

```tsx
import { ThemeToggle } from '@/components/ui/theme-toggle';

<ThemeToggle />
```

### Header
Header del dashboard con notificaciones, tema y menú de usuario.

```tsx
import { Header } from '@/components/ui/header';

<Header />
```

## Hooks

### useTheme
Gestiona el tema claro/oscuro con persistencia en localStorage.

```tsx
import { useTheme } from '@/hooks/useTheme';

const { theme, toggleTheme, setTheme } = useTheme();
```

### useAuth
Maneja la autenticación y el token.

```tsx
import { useAuth } from '@/hooks/useAuth';

const { token, isAuthenticated, login, logout } = useAuth();
```

## Stores (Zustand)

### useAuthStore
Estado global de autenticación.

```tsx
import { useAuthStore } from '@/stores';

const { user, isAuthenticated, logout } = useAuthStore();
```

### useJobStore
Gestión de jobs y filtros.

```tsx
import { useJobStore } from '@/stores';

const { jobs, filters, setFilters, addJob } = useJobStore();
```

### useUIStore
Estado de UI (sidebar, tema).

```tsx
import { useUIStore } from '@/stores';

const { sidebarOpen, toggleSidebar } = useUIStore();
```

## Páginas

### /login
Página de inicio de sesión con validación de campos.

**Features:**
- Validación de email y contraseña
- Mostrar/ocultar contraseña
- Manejo de errores
- Loading states

### /register
Página de registro con formulario completo.

**Features:**
- Validación de todos los campos
- Confirmación de registro exitoso
- Explicación del ID de Telegram

### /dashboard
Dashboard principal con estadísticas y jobs recientes.

**Features:**
- Stats cards con tendencias
- Lista de jobs recientes
- Quick actions
- Animaciones de entrada

### /dashboard/postulaciones
Tabla de jobs con filtros y búsqueda.

**Features:**
- Búsqueda en tiempo real
- Filtro por estado
- Paginación
- Modal para agregar job
- Editar/eliminar jobs

### /dashboard/perfil
Perfil del usuario con preferencias.

**Features:**
- Edición de datos personales
- Keywords de búsqueda (toggle chips)
- Upload de CV
- Preferencias de notificaciones

### /dashboard/buscar
Búsqueda de nuevos empleos.

**Features:**
- Búsqueda con filtros
- Filtros rápidos
- Guardar jobs
- Aplicar directamente

### /dashboard/suscripcion
Página de planes y pagos.

**Features:**
- Comparación de planes
- Métodos de pago
- FAQs

### /dashboard/configuracion
Configuración de la cuenta.

**Features:**
- Integraciones (Telegram, etc.)
- Historial de facturación
- Eliminación de cuenta

## Diseño

### Colores
El sistema usa variables CSS con soporte para light/dark mode:

```css
--background: hsl(var(--background))
--foreground: hsl(var(--foreground))
--primary: hsl(var(--primary))
--secondary: hsl(var(--secondary))
--destructive: hsl(var(--destructive))
--success: hsl(var(--success))
--warning: hsl(var(--warning))
```

### Tipografía
- Font: Geist (sans), Geist Mono (mono)
- Tamaños consistentes con scale
- Line heights apropiados para legibilidad

### Espaciado
- 4px base (space-1)
- Scale: 1, 2, 3, 4, 5, 6, 8, 10, 12, 16...
- Consistente en toda la app

### Responsive
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Sidebar colapsable en mobile
- Layout adaptable

## Animaciones

Usando Framer Motion con easing natural:

```tsx
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};
```

### Timing
- Entrada: 200-500ms
- Hover: 150-200ms
- Stagger: 50-100ms entre elementos

### Easing
- `--ease-out-quart`: cubic-bezier(0.25, 1, 0.5, 1)
- `--ease-out-quint`: cubic-bezier(0.22, 1, 0.36, 1)
- `--ease-out-expo`: cubic-bezier(0.16, 1, 0.3, 1)

## Testing

### Ejecutar tests
```bash
npm test           # Modo watch
npm run test:ui    # UI interactiva
npm run test:coverage  # Coverage report
```

### Tests incluidos
- Utils (cn function)
- Job types y filtering
- Componentes UI (agregar según necesidad)

## Accesibilidad

- WCAG AA compliance
- Focus indicators visibles
- Labels en todos los inputs
- Alt text en imágenes
- Reduced motion support

## Performance

- Next.js Image optimization
- Lazy loading de componentes
- CSS transitions en GPU (transform, opacity)
- will-change aplicado selectivamente

## Convenciones

### Nombres de archivos
- PascalCase para componentes: `Button.tsx`, `Sidebar.tsx`
- camelCase para hooks: `useTheme.ts`, `useAuth.ts`
- kebab-case para páginas: `page.tsx`, `layout.tsx`

### Import/Export
- Preferir default exports para páginas
- Named exports para componentes reutilizables
- Agrupar en index.ts para facilidad de import

### Tipos
- Definir interfaces en `/src/types`
- Usar TypeScript strict mode
- No usar `any`

## Licencia

JobBot Dashboard © 2024 - Todos los derechos reservados.
