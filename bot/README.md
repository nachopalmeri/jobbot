# 🤖 JobBot Telegram

Bot de Telegram para monitorear ofertas laborales de Python/Backend/Junior en Buenos Aires con integración de **IA (Groq/Llama 3)** para analizar CVs.

---

## 📋 Tabla de Contenidos

- [Overview](#-overview)
- [Estructura](#-estructura)
- [Comandos](#-comandos)
- [Configuración](#-configuración)
- [Scraping](#-scraping)
- [Inteligencia Artificial](#-inteligencia-artificial)
- [Sistema de Backup](#-sistema-de-backup)
- [Testing](#-testing)
- [Scheduler](#-scheduler)
- [Roadmap](#-roadmap)

---

## 🌟 Overview

JobBot Telegram es un bot inteligente que automatiza la búsqueda de empleo:

- 🤖 **6 fuentes de empleo**: LinkedIn, Remotive, Arbeitnow, Himalayas, Jobicy, RSS
- 🧠 **IA integrada**: Análisis de CVs con Llama 3.3 70B
- 📊 **Match scoring**: Puntuación de compatibilidad job/CV
- 🔔 **Alertas inteligentes**: Monitoreo automático con horarios configurables
- 🔒 **GDPR compliant**: Eliminación completa de datos
- 💾 **Backup automático**: Sistema de backup con notificaciones

### Flujo Principal

```
1. Usuario configura preferencias (/preferencias)
2. Usuario sube CV (/cargar_cv)
3. IA analiza CV y extrae keywords
4. Scheduler busca jobs cada X minutos
5. IA compara cada job con el CV (match score)
6. Bot envía alertas con puntuación 🟢🟡🟠🔴
7. Usuario aplica a los mejores matches
```

---

## 📁 Estructura

```
job_bot/
├── 📄 bot.py                      # Entry point del bot
├── 📄 config.py                   # Variables de entorno
├── 📄 database.py                 # Capa de base de datos
├── 📄 job_scraper.py              # Scrapers (6 fuentes)
├── 📄 scheduler.py                # Monitoreo automático
├── 📄 cv_analyzer.py              # IA (Groq) para CVs
├── 📄 backup.py                   # Sistema de backup
├── 📄 company_service.py          # Datos de empresas
├── 📄 financial_service.py        # Datos financieros
├── 📄 github_analyzer.py          # Análisis de GitHub
├── 📄 glassdoor_service.py        # Reviews de empresas
├── 📄 interview_data.py           # Datos de entrevistas
├── 📄 requirements.txt            # Dependencias
├── 📄 .env.example                # Template de config
├── 📁 tests/                      # Tests unitarios
│   ├── test_database.py
│   ├── test_scrapers.py
│   ├── test_cv_analyzer.py
│   └── test_scheduler.py
├── 📁 cvs/                        # Storage de CVs
└── 📁 landing/                    # Landing page estática
```

### Módulos Principales

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `bot.py` | ~600 | Lógica del bot, comandos, handlers |
| `job_scraper.py` | ~500 | Scrapers de 6 fuentes |
| `cv_analyzer.py` | ~300 | Integración con Groq API |
| `scheduler.py` | ~400 | Monitoreo automático |
| `database.py` | ~350 | CRUD SQLite |

---

## ⌨️ Comandos

### Comandos de Usuario

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `/start` | Inicialización y bienvenida | `/start` |
| `/preferencias` | Wizard de configuración | `/preferencias` |
| `/horarios` | Configurar frecuencia y horario | `/horarios` |
| `/cargar_cv` | Subir CV (PDF/TXT) | `/cargar_cv` |
| `/analizar_cv` | IA analiza tu CV | `/analizar_cv` |
| `/analizar_oferta [URL]` | Match score vs oferta | `/analizar_oferta https://...` |
| `/empresa [dominio]` | Ficha de empresa | `/empresa google.com` |
| `/detalle_job [id] [country]` | Detalle extendido | `/detalle_job 123 AR` |
| `/buscar` | Búsqueda manual inmediata | `/buscar` |
| `/activar_alertas` | Activar monitoreo | `/activar_alertas` |
| `/desactivar_alertas` | Pausar monitoreo | `/desactivar_alertas` |
| `/estado` | Ver perfil completo | `/estado` |
| `/borrar_datos` | Eliminar todos los datos | `/borrar_datos` |
| `/web` | Landing page | `/web` |
| `/help` | Ayuda y comandos | `/help` |

### Ejemplo de Conversación

```
User: /start
Bot: 🤖 ¡Bienvenido a JobBot!
     Tu asistente inteligente de búsqueda laboral.
     
     Usá /preferencias para configurar tu perfil

User: /preferencias
Bot: 🎯 Wizard de Configuración - Paso 1/5
     ¿Qué perfil buscás?
     1. Python Developer
     2. Backend Developer
     3. Full Stack
     
User: 1
Bot: ✅ Perfil: Python Developer
     
     Paso 2/5: ¿Qué nivel?
     1. Junior (0-2 años)
     2. Mid (2-5 años)
     3. Senior (5+ años)

# ... continúa el wizard ...

User: /cargar_cv
Bot: 📄 Por favor, subí tu CV en formato PDF o TXT

[User sube cv.pdf]

Bot: ✅ CV recibido y guardado.
     ¿Querés que la IA lo analice ahora? (/analizar_cv)

User: /analizar_cv
Bot: 🧠 Analizando tu CV con IA...
     
     📊 Resultado del Análisis:
     
     Score: 78/100 🟢
     
     Keywords detectadas:
     ✅ Python, Django, PostgreSQL, Docker
     
     Keywords sugeridas:
     💡 AWS, Kubernetes, CI/CD
     
     Recomendaciones:
     • Agregar proyectos open source
     • Certificaciones cloud
```

---

## ⚙️ Configuración

### Variables de Entorno

```env
# Telegram
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# AI
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# Database
DATABASE_TYPE=sqlite
DATABASE_PATH=job_bot.db

# App
APP_ENV=development
LOG_LEVEL=INFO
LANDING_URL=https://jobbot.ar

# Scheduler
SCHEDULER_POLL_MINUTES=10

# Search APIs (opcional)
SERPAPI_KEY=
RAPIDAPI_KEY=
TWITTER_BEARER_TOKEN=

# Smart Summary UX
JOB_BATCH_TTL_MINUTES=30
MAX_JOBS_FREE=5
MAX_JOBS_STARTER=8
MAX_JOBS_PRO=15
MAX_JOBS_PREMIUM=20
```

### Setup

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
# Editar .env con tus tokens

# 3. Inicializar base de datos
python -c "from database import Database; db = Database(); db.init_db()"

# 4. Ejecutar bot
python bot.py
```

---

## 🔍 Scraping

### Fuentes de Empleo (6)

| Fuente | Tipo | Frecuencia | Calidad |
|--------|------|------------|---------|
| **LinkedIn AR** | RSS (Google News) | 10 min | ⭐⭐⭐⭐⭐ |
| **Remotive** | API | 10 min | ⭐⭐⭐⭐ |
| **Arbeitnow** | API | 10 min | ⭐⭐⭐ |
| **Himalayas** | API | 10 min | ⭐⭐⭐⭐ |
| **Jobicy** | API | 10 min | ⭐⭐⭐⭐ |
| **Custom RSS** | RSS | 10 min | Variable |

### Filtros Aplicados

```python
# job_scraper.py
FILTERS = {
    'keywords': ['python', 'backend', 'junior', 'jr'],
    'exclude': ['senior', 'sr', 'lead', 'principal', 'architect'],
    'location': ['buenos aires', 'remoto', 'remote'],
    'experience': 'junior',  # 0-2 años
    'modalidad': ['remoto', 'hibrido']  # Configurable por usuario
}
```

### Arquitectura de Scrapers

```python
class JobScraper:
    """
    Scrapers individuales por fuente con:
    - Rate limiting integrado
    - Caching de respuestas
    - Retry con backoff
    - Parsing normalizado
    """
    
    def scrape_linkedin(self) -> List[Job]:
        """LinkedIn vía Google News RSS local"""
        pass
    
    def scrape_remotive(self) -> List[Job]:
        """Remotive API - trabajos remotos"""
        pass
    
    def scrape_arbeitnow(self) -> List[Job]:
        """Arbeitnow API - tech jobs"""
        pass
    
    def scrape_himalayas(self) -> List[Job]:
        """Himalayas API - startup remote"""
        pass
    
    def scrape_jobicy(self) -> List[Job]:
        """Jobicy API - startup tech"""
        pass
    
    def scrape_custom_rss(self, url: str) -> List[Job]:
        """Feeds RSS personalizados"""
        pass
```

### Modelo de Job

```python
@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # 'linkedin', 'remotive', etc.
    posted_at: datetime
    salary: Optional[str]
    remote: bool
    experience_level: str  # 'junior', 'mid', 'senior'
    keywords: List[str]
    match_score: Optional[float]  # 0-100
```

---

## 🧠 Inteligencia Artificial

### Integración Groq API

```python
# cv_analyzer.py
import groq

class CVAnalyzer:
    """
    Análisis de CVs usando Llama 3.3 70B
    """
    
    def __init__(self):
        self.client = groq.Client(api_key=os.getenv('GROQ_API_KEY'))
        self.model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    def analyze_cv(self, cv_text: str) -> dict:
        """
        Analiza un CV y retorna:
        - Score general (0-100)
        - Keywords detectadas
        - Keywords faltantes
        - Sugerencias de mejora
        """
        prompt = f"""
        Analiza el siguiente CV y proporciona un score de 0-100,
        keywords detectadas, keywords sugeridas y recomendaciones.
        
        CV:
        {cv_text}
        
        Responde en formato JSON:
        {{
            "score": 85,
            "keywords_found": [...],
            "keywords_missing": [...],
            "suggestions": [...]
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        return json.loads(response.choices[0].message.content)
    
    def compare_job_cv(self, job: Job, cv_text: str) -> dict:
        """
        Compara un job contra el CV y retorna match score.
        """
        prompt = f"""
        Compara esta oferta laboral con el CV del candidato.
        
        OFERTA:
        Título: {job.title}
        Descripción: {job.description}
        Requisitos: {job.requirements}
        
        CV:
        {cv_text}
        
        Proporciona:
        1. Match score (0-100)
        2. Keywords coincidentes
        3. Skills faltantes
        4. Recomendación de aplicar (SI/NO/TAL VEZ)
        """
        
        response = self.client.chat.completions.create(...)
        return self._parse_match_response(response)
```

### Match Scoring

| Score | Emoji | Significado | Acción |
|-------|-------|-------------|--------|
| 80-100 | 🟢 | Excelente match | Aplicar inmediatamente |
| 60-79 | 🟡 | Buen match | Considerar aplicar |
| 40-59 | 🟠 | Match parcial | Evaluar cuidadosamente |
| 0-39 | 🔴 | Bajo match | Posiblemente ignorar |

### Ejemplo de Análisis

```
🧠 Análisis de Match

📊 Score: 87/100 🟢

✅ Skills coincidentes:
   • Python (3 años)
   • Django (2 años)
   • PostgreSQL (2 años)
   • Docker (1 año)

⚠️ Skills faltantes:
   • AWS (nice to have)
   • Kubernetes (plus)

💡 Recomendación: APLICAR
   Tu perfil coincide muy bien con esta oferta.
   Destaca tu experiencia con Django y Docker.

🔗 Aplicar: [Botón de aplicación]
```

---

## 💾 Sistema de Backup

### Características

- 📦 **Backup completo**: Database + CVs + configs
- ⏰ **Automático**: Diario/semanal configurables
- ☁️ **Múltiples destinos**: Local, S3, Email
- 🔔 **Notificaciones**: Éxito/error por Telegram
- 🔄 **Rotación**: Retención de N backups

### Uso

```bash
# Backup manual
python backup.py

# Backup con email
python backup.py --email admin@jobbot.ar

# Backup programado (cron)
0 2 * * * cd /path/to/job_bot && python backup.py
```

### Configuración

```python
# backup.py
BACKUP_CONFIG = {
    'retention_days': 30,
    'compress': True,  # zip
    'include_cvs': True,
    'destinations': {
        'local': './backups/',
        's3': {
            'bucket': 'jobbot-backups',
            'region': 'us-east-1'
        },
        'email': {
            'enabled': True,
            'recipients': ['admin@jobbot.ar']
        }
    }
}
```

### Estructura del Backup

```
backup_2024-01-20_14-30-00/
├── database/
│   └── job_bot.db              # Base de datos SQLite
├── cvs/
│   ├── user_1_cv.pdf
│   ├── user_2_cv.pdf
│   └── ...
├── configs/
│   ├── .env                    # (sin secrets reales)
│   └── settings.json
├── metadata.json               # Info del backup
└── README.txt                  # Instrucciones restore
```

---

## 🧪 Testing

### Tests Disponibles

| Suite | Líneas | Cobertura |
|-------|--------|-----------|
| `test_database.py` | 150 | CRUD, migrations |
| `test_scrapers.py` | 200 | Parsing, filtros |
| `test_cv_analyzer.py` | 100 | IA responses |
| `test_scheduler.py` | 120 | Cron jobs |
| **Total** | **570** | **~85%** |

### Ejecutar Tests

```bash
# Todos los tests
cd job_bot
python -m pytest tests/ -v

# Tests específicos
python -m pytest tests/test_scrapers.py -v
python -m pytest tests/test_cv_analyzer.py::test_analyze_cv -v

# Con coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Ejemplo de Test

```python
# tests/test_cv_analyzer.py
import pytest
from cv_analyzer import CVAnalyzer

def test_analyze_cv():
    analyzer = CVAnalyzer()
    cv_text = """
    Juan Pérez - Python Developer
    3 años de experiencia en Django, PostgreSQL, Docker.
    """
    
    result = analyzer.analyze_cv(cv_text)
    
    assert 'score' in result
    assert 0 <= result['score'] <= 100
    assert 'Python' in result['keywords_found']
```

---

## ⏰ Scheduler

### Configuración de Alertas

```python
# scheduler.py
class JobScheduler:
    """
    Monitoreo automático con:
    - Horarios personalizables por usuario
    - Rate limiting
    - Filtros por preferencias
    - Deduplication de jobs
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.poll_minutes = int(os.getenv('SCHEDULER_POLL_MINUTES', 10))
    
    def start_monitoring(self, user_id: int):
        """Inicia monitoreo para un usuario"""
        user = self.db.get_user(user_id)
        
        # Job cada X minutos
        self.scheduler.add_job(
            self.check_jobs,
            'interval',
            minutes=self.poll_minutes,
            args=[user_id],
            id=f'monitor_{user_id}'
        )
    
    def check_jobs(self, user_id: int):
        """Busca jobs y envía alertas"""
        user = self.db.get_user(user_id)
        preferences = user['preferences']
        cv_text = self.db.get_cv(user_id)
        
        # Scrape jobs
        jobs = self.scraper.scrape_all(
            keywords=preferences['keywords'],
            location=preferences['location'],
            remote=preferences['remote']
        )
        
        # Filtrar jobs ya vistos
        new_jobs = [j for j in jobs if not self.db.is_job_seen(user_id, j.id)]
        
        # IA: Calcular match score
        for job in new_jobs:
            match = self.analyzer.compare_job_cv(job, cv_text)
            job.match_score = match['score']
        
        # Enviar solo los mejores matches (score > 60)
        good_matches = [j for j in new_jobs if j.match_score > 60]
        
        for job in sorted(good_matches, key=lambda x: x.match_score, reverse=True):
            self.send_job_alert(user_id, job)
```

### Wizard de Horarios

```
User: /horarios
Bot: ⏰ Configuración de Horarios
     
     ¿Con qué frecuencia querés que busque?
     1. Cada 10 minutos (Premium)
     2. Cada 30 minutos (Pro)
     3. Cada 1 hora (Starter)
     4. Cada 2 horas (Free)

User: 1
Bot: ✅ Frecuencia: 10 minutos

     ¿En qué horario querés recibir alertas?
     Ejemplo: 09:00 - 20:00

User: 09:00 - 18:00
Bot: ✅ Horario configurado: 09:00 - 18:00
     
     Recordá que podés pausar con /desactivar_alertas
```

---

## 🗺️ Roadmap

### Completado ✅

- [x] Bot de Telegram funcional
- [x] 6 fuentes de scraping
- [x] IA integrada (Groq)
- [x] Match scoring
- [x] Sistema de backup
- [x] Tests unitarios
- [x] GDPR compliance
- [x] Wizard de preferencias

### En Desarrollo 🚧

- [ ] Dashboard web (MVP ready)
- [ ] Pagos y suscripciones
- [ ] Pipeline de postulaciones

### Planificado 📅

- [ ] Calendario de entrevistas
- [ ] Integración LinkedIn OAuth
- [ ] Mobile app
- [ ] Analytics avanzado

---

## 📚 Recursos

- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [Groq API](https://console.groq.com/docs)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

---

<p align="center">
  <strong>JobBot Telegram</strong>
  <br>
  🤖 Hecho para Nacho (PISCU) — Gestión de TI
</p>
