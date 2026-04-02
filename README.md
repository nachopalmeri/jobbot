# Workspace Root

Este es el directorio raíz del workspace de OpenCode. 

## Configuración Global

### Dependencias Disponibles Globalmente
- **@chenglou/pretext**: Librería de medición y layout de texto multilinea

### Uso Rápido

En cualquier nuevo proyecto, pretext ya está disponible:

```javascript
import { prepare, layout } from '@chenglou/pretext';

const prepared = prepare('Tu texto aquí', '16px Inter');
const { height, lineCount } = layout(prepared, 300, 20);
```

### Scripts de Utilidad

Ubicados en `.workspace/`:

**Windows:**
```batch
.workspace\init-project.bat nombre-del-proyecto
```

**Unix/Linux/Mac:**
```bash
.workspace/init-project.sh nombre-del-proyecto
```

Estos scripts crean un nuevo proyecto con pretext ya incluido en las dependencias.

### Estructura

```
jobobt/
├── package.json          # Dependencias globales del workspace
├── WORKSPACE.md          # Documentación de configuración
├── .workspace/           # Scripts y utilidades del workspace
│   ├── init-project.bat  # Script para Windows
│   └── init-project.sh   # Script para Unix/Linux/Mac
├── dashboard/            # Proyectos existentes
├── frontend/
├── job_bot/
└── y/
```

## Documentación Adicional

- [WORKSPACE.md](./WORKSPACE.md) - Guía completa de configuración
- [Repositorio pretext](https://github.com/chenglou/pretext) - Documentación oficial
# Deploy: Thu Apr  2 21:45:12 UTC 2026
