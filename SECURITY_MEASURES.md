# Medidas de Seguridad - JobBot Dashboard

> Seguridad de nivel empresarial implementada paso a paso.

---

## 🔐 Resumen de Medidas

| Capa | Implementación | Estado |
|------|----------------|--------|
| **Headers de Seguridad** | CSP, HSTS, X-Frame, etc. | ✅ `next.config.ts` |
| **Validación de Archivos** | Magic numbers, content sniffing | ✅ `fileValidation.ts` |
| **Rate Limiting** | Anti brute-force en auth | ✅ `rateLimit.ts` |
| **Almacenamiento de Tokens** | HttpOnly cookies (no localStorage) | ✅ `authCookies.ts` |
| **Row Level Security** | RLS en Supabase | ✅ `row-level-security.sql` |
| **Secrets Scanning** | Trivy + TruffleHog en CI/CD | ✅ GitHub Actions |

---

## 📋 Detalle por Capa

### 1. Headers de Seguridad (`next.config.ts`)

```typescript
// Headers configurados:
X-Frame-Options: DENY                    // Previene clickjacking
X-Content-Type-Options: nosniff          // Previene MIME sniffing
Content-Security-Policy: ...            // Previene XSS
Strict-Transport-Security: max-age=...  // Fuerza HTTPS
X-XSS-Protection: 1; mode=block         // Filtro XSS legacy
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

**CSP específica:**
```
default-src 'self'
script-src 'self' 'unsafe-eval' 'unsafe-inline'
style-src 'self' 'unsafe-inline'
img-src 'self' data: https:
connect-src 'self' http://localhost:8000 https://api.jobbot.com
frame-ancestors 'none'
```

### 2. Validación de Archivos CV (`src/lib/fileValidation.ts`)

**Verificaciones implementadas:**

1. ✅ **Tamaño máximo**: 10MB
2. ✅ **Extensiones permitidas**: `.pdf`, `.doc`, `.docx`, `.txt`
3. ✅ **MIME type validation**: Contra lista blanca
4. ✅ **Magic numbers**: Verificación de firma real del archivo
   - PDF: `%PDF` (0x25, 0x50, 0x44, 0x46)
   - DOCX: `PK` (zip header)
   - DOC: `ÐÏ\x11à` (MS Office)
5. ✅ **Detección de ejecutables**: MZ, ELF, Java class
6. ✅ **Sanitización de nombres**: Previene path traversal
7. ✅ **Nombres seguros**: UUID-based para almacenamiento

**Uso:**
```typescript
import { validateCVFile } from '@/lib/fileValidation';

const result = await validateCVFile(file);
if (!result.valid) {
  alert(result.error); // "Archivo demasiado grande" o "Tipo no permitido"
}
```

### 3. Rate Limiting (`src/lib/rateLimit.ts`)

**Configuración:**
- Máximo 5 intentos de login cada 15 minutos
- Bloqueo de 30 minutos después de exceder
- Limpieza automática de entradas expiradas

**Implementación:**
```typescript
// En API route de login
import { withRateLimit } from '@/lib/rateLimit';

export async function POST(request: Request) {
  return withRateLimit(request, async () => {
    // Lógica de login
  });
}
```

**Respuesta al exceder:**
```json
{
  "error": "Demasiados intentos",
  "message": "Cuenta temporalmente bloqueada. Intenta en 1800 segundos.",
  "retryAfter": 1800
}
```

### 4. Tokens en HttpOnly Cookies (`src/lib/authCookies.ts`)

**Problema anterior:** Token en localStorage vulnerable a XSS  
**Solución:** Cookies httpOnly (no accesibles por JavaScript)

**Atributos de cookies:**
```
HttpOnly: true       // No accesible por JS
Secure: true         // Solo HTTPS en producción
SameSite: strict     // Previene CSRF
Path: /              // Toda la app
Max-Age: 604800      // 7 días
```

**Flujo de autenticación:**
1. Login exitoso → Servidor crea cookies httpOnly
2. Cliente NO tiene acceso al token
3. Cada request incluye cookie automáticamente
4. Logout → Servidor limpia cookies

**Uso en cliente:**
```typescript
// Solo estado booleano, NUNCA el token
setAuthState(true);    // Login exitoso
isAuthenticated();     // Verificar sesión
```

**Uso en servidor:**
```typescript
const token = getTokenFromCookie(request);
```

### 5. Row Level Security (`fixtures/row-level-security.sql`)

**Tablas protegidas:**
- `users` - Solo ver/editar perfil propio
- `cvs` - Solo acceder a CVs propios
- `applications` - Solo postulaciones propias
- `cv_analyses` - Análisis vinculados a CVs propios
- `user_settings` - Configuración personal
- `credits` - Créditos propios (lectura), admin (modificación)
- `subscriptions` - Suscripción propia
- `sessions` - Sesiones propias

**Ejemplo de política:**
```sql
CREATE POLICY "Users can only access own CVs"
  ON cvs FOR ALL
  USING (auth.uid() = user_id);
```

**Índices para performance:**
```sql
CREATE INDEX idx_cvs_user_id ON cvs(user_id);
CREATE INDEX idx_applications_user_id ON applications(user_id);
-- etc.
```

**Auditoría:**
```sql
-- Tabla audit_log con triggers
CREATE TRIGGER cvs_audit
  AFTER INSERT OR UPDATE OR DELETE ON cvs
  FOR EACH ROW EXECUTE FUNCTION audit_trigger();
```

### 6. Secrets Scanning (CI/CD)

**Herramientas integradas:**

1. **TruffleHog** - Detección de secrets en código
   ```yaml
   - uses: trufflesecurity/trufflehog@main
     with:
       path: ./
       base: ${{ github.event.repository.default_branch }}
       head: HEAD
       extra_args: --debug --only-verified
   ```

2. **Trivy** - Escaneo de vulnerabilidades en dependencias
   ```yaml
   - uses: aquasecurity/trivy-action@master
     with:
       scan-type: 'fs'
       scan-ref: './dashboard'
       format: 'sarif'
   ```

**Flujo CI/CD:**
```
1. Security Scan (secrets + vulnerabilities)
2. E2E Tests (solo si pasa seguridad)
3. Security Tests (categoría específica)
```

---

## 🧪 Tests E2E de Seguridad

Nuevos tests específicos para seguridad:

| Test | Descripción |
|------|-------------|
| `27-security-routes` | Rutas protegidas redirigen a login sin auth |
| `28-security-xss` | Sanitización de inputs maliciosos |
| `29-security-headers` | Verificación de headers de seguridad |
| `30-security-brute-force` | Bloqueo después de múltiples intentos |
| `31-security-session` | Manejo correcto de sesiones y cookies |

**Ejecución:**
```bash
cd e2e
./suite.sh security    # Solo tests de seguridad
./suite.sh all         # Todos los tests (35 total)
```

---

## 🚀 Checklist de Seguridad

Antes de deploy a producción:

- [ ] Headers de seguridad activos (verificar con `curl -I`)
- [ ] RLS habilitado en Supabase (ejecutar SQL)
- [ ] Cookies httpOnly funcionando (verificar en DevTools)
- [ ] Rate limiting activo (probar 5 logins fallidos)
- [ ] Validación de archivos (subir PDF malicioso)
- [ ] Secrets scanning pasando en CI/CD
- [ ] Tests E2E de seguridad pasando
- [ ] HTTPS forzado en producción
- [ ] CSP ajustada para dominios de producción

---

## 📚 Recursos

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [HttpOnly Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies)
- [Supabase RLS](https://supabase.com/docs/guides/auth/row-level-security)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)

---

## 🔒 Notas Importantes

1. **Token en localStorage**: El código legacy usa localStorage. Migrar completamente a cookies httpOnly.
2. **CSP en desarrollo**: Permite 'unsafe-inline' para scripts. Ajustar para producción con nonces.
3. **Rate limiting en memoria**: Para producción a alta escala, migrar a Redis.
4. **Auditoría**: Los logs de auditoría crecen rápido. Implementar retención (ej: 90 días).

---

**Última actualización:** Abril 2026  
**Responsable:** Dev Team  
**Próxima revisión:** Julio 2026
