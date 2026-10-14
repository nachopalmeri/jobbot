"""Source directory for the unified job-search workflow.

Only sources marked as API, search-index or user-supplied feeds are candidates
for automated collection. Manual discovery routes are intentionally not scraped.
Task marketplaces are separated from employment listings.
"""

from copy import deepcopy
from typing import Dict, List, Optional


SEARCH_SOURCE_CATALOG: List[Dict[str, str]] = [
    {"id": "startups_argentina", "name": "Startups Argentina", "url": "https://www.startupsargentina.com/jobs", "group": "argentina_startups", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Prioridad 1; validar aviso y fecha en la fuente primaria."},
    {"id": "getonbrd", "name": "Get on Board", "url": "https://www.getonbrd.com/", "group": "argentina_part_time", "kind": "employment", "access": "automated_api", "scope": "Argentina/LATAM", "note": "API pública integrada; consultas locales acotadas."},
    {"id": "uade", "name": "Empleos UADE", "url": "https://www.empleos.uade.edu.ar/Postulaciones", "group": "argentina_part_time", "kind": "employment", "access": "authenticated_manual", "scope": "Argentina", "note": "Revisión en sesión del usuario; no automatizar login/postulación."},
    {"id": "firstjob", "name": "FirstJob", "url": "https://firstjob.me/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina/LATAM", "note": "Pasantías, prácticas y primeros empleos; confirmar país/fecha."},
    {"id": "empleosit", "name": "Empleos IT", "url": "https://empleosit.com.ar/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Validar publicación original y vigencia."},
    {"id": "indeed", "name": "Indeed Argentina", "url": "https://ar.indeed.com/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Discovery manual; no evadir controles anti-bot."},
    {"id": "computrabajo", "name": "Computrabajo Argentina", "url": "https://ar.computrabajo.com/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Discovery manual; verificar ficha y consistencia de jornada."},
    {"id": "linkedin", "name": "LinkedIn Jobs y publicaciones", "url": "https://www.linkedin.com/jobs/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina/global", "note": "Revisar empleos y publicaciones públicas; no automatizar sesión autenticada."},
    {"id": "bumeran", "name": "Bumeran Argentina", "url": "https://www.bumeran.com.ar/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Validar fecha original y aviso directo; algunas fichas requieren JavaScript."},
    {"id": "becasit", "name": "BecasIT", "url": "https://becasit.com.ar/", "group": "argentina_part_time", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Pasantías y formación IT; confirmar publicación vigente."},
    {"id": "wellfound", "name": "Wellfound", "url": "https://wellfound.com/", "group": "international_startups_part_time", "kind": "employment", "access": "manual", "scope": "Global; confirmar contratación desde Argentina", "note": "Sin scraper automatizado en este proyecto."},
    {"id": "cosign", "name": "Cosign", "url": "https://cosign.co/jobs", "group": "international_startups_part_time", "kind": "employment", "access": "manual", "scope": "Global; confirmar país, modalidad y contratación desde Argentina", "note": "Red profesional curada; explorar roles en empresas recomendadas por la comunidad. Sin API/feed público verificado."},
    {"id": "yc_jobs", "name": "Y Combinator Jobs", "url": "https://www.ycombinator.com/jobs", "group": "international_startups_part_time", "kind": "employment", "access": "manual", "scope": "Global; confirmar elegibilidad", "note": "Verificar vacante y empresa contratante."},
    {"id": "work_at_a_startup", "name": "Work at a Startup", "url": "https://www.workatastartup.com/", "group": "international_startups_part_time", "kind": "employment", "access": "manual", "scope": "Global; confirmar elegibilidad", "note": "Discovery manual; no generalizar elegibilidad por etiqueta remoto."},
    {"id": "startupjobs", "name": "Startup Jobs Argentina", "url": "https://startup.jobs/locations/argentina", "group": "argentina_startups", "kind": "employment", "access": "manual", "scope": "Argentina", "note": "Agregador; confirmar aviso en la empresa."},
    {"id": "vibe_coding_jobs", "name": "Vibe Coding Jobs", "url": "https://remotevibecodingjobs.com/whos-hiring", "group": "other_high_match", "kind": "employment", "access": "manual", "scope": "Global; confirmar país", "note": "Discovery únicamente; filtrar seniority y validar ATS."},
    {"id": "vibehackers", "name": "Vibehackers Jobs", "url": "https://vibehackers.io/jobs", "group": "other_high_match", "kind": "employment", "access": "manual", "scope": "Global; confirmar país", "note": "Discovery únicamente; verificar vigencia en fuente primaria."},
    {"id": "remotive", "name": "Remotive", "url": "https://remotive.com/remote-jobs", "group": "remote_employment", "kind": "employment", "access": "automated_api", "scope": "Remoto; validar país", "note": "API remota integrada; ubicación genérica no confirma Argentina."},
    {"id": "arbeitnow", "name": "Arbeitnow", "url": "https://arbeitnow.com/", "group": "remote_employment", "kind": "employment", "access": "automated_api", "scope": "Global/remoto", "note": "API integrada; aplicar elegibilidad geográfica."},
    {"id": "jobicy", "name": "Jobicy", "url": "https://jobicy.com/", "group": "remote_employment", "kind": "employment", "access": "automated_api", "scope": "Remoto; validar país", "note": "API integrada; no asumir contratación global."},
    {"id": "himalayas", "name": "Himalayas", "url": "https://himalayas.app/jobs", "group": "remote_employment", "kind": "employment", "access": "automated_api", "scope": "Remoto; validar país", "note": "API integrada; verificar país permitido y enlace original."},
    {"id": "linkedin_google", "name": "LinkedIn por índice público", "url": "https://www.linkedin.com/jobs/", "group": "remote_employment", "kind": "employment", "access": "search_index", "scope": "Argentina/global", "note": "Cobertura parcial vía índice/RSS; no equivale al feed completo de LinkedIn."},
    {"id": "serpapi_google", "name": "Google Jobs (SerpAPI)", "url": "https://www.google.com/search?ibp=htl;jobs", "group": "remote_employment", "kind": "employment", "access": "optional_paid_api", "scope": "Según consulta", "note": "Sólo si está configurada la credencial; respetar cuota/costo."},
    {"id": "premium_backfill", "name": "Backfill de proveedores premium", "url": "", "group": "remote_employment", "kind": "employment", "access": "optional_paid_api", "scope": "Según proveedor y consulta", "note": "Active Jobs DB/JSearch bajo configuración; uso acotado, no habilitar costos sin autorización."},
    {"id": "twitter_x", "name": "Twitter/X Jobs", "url": "https://x.com/", "group": "argentina_part_time", "kind": "employment", "access": "optional_paid_api", "scope": "Según consulta", "note": "Sólo si hay token/plan configurado; publicaciones requieren validar en empleador."},
    {"id": "custom_rss", "name": "Feeds RSS del usuario", "url": "", "group": "all_employment", "kind": "employment", "access": "user_feed", "scope": "Según feed", "note": "Sólo URLs agregadas por el usuario."},
    {"id": "outlier", "name": "Outlier", "url": "https://outlier.ai/", "group": "ai_task_work", "kind": "task_work", "access": "manual", "scope": "Por proyecto/país", "note": "Tareas por encargo; carga, tarifas y continuidad variables."},
    {"id": "alignerr", "name": "Alignerr", "url": "https://www.alignerr.com/jobs", "group": "ai_task_work", "kind": "task_work", "access": "manual", "scope": "Por proyecto/país", "note": "Confirmar dialecto, elegibilidad y disponibilidad de proyectos."},
    {"id": "dataannotation", "name": "DataAnnotation", "url": "https://www.dataannotation.tech/", "group": "ai_task_work", "kind": "task_work", "access": "manual", "scope": "País no confirmado", "note": "No contar como elegible hasta confirmar Argentina y requisitos."},
    {"id": "prolific", "name": "Prolific", "url": "https://www.prolific.com/participants", "group": "ai_task_work", "kind": "task_work", "access": "manual", "scope": "País según lista oficial", "note": "Investigación remunerada, no empleo; prioridad baja si Argentina no está habilitada."},
    {"id": "yc_events", "name": "YC Startup Events", "url": "https://www.ycombinator.com/events", "group": "ecosystem", "kind": "ecosystem", "access": "manual", "scope": "Global", "note": "Networking, no vacantes."},
    {"id": "appgentina_events", "name": "Appgentina — Eventos de tecnología en Argentina", "url": "https://appgentina.com/", "group": "ecosystem", "kind": "ecosystem", "access": "manual", "scope": "Argentina", "note": "Networking y eventos; no contabilizar como vacantes."},
]


def get_search_source_catalog(group: Optional[str] = None) -> List[Dict[str, str]]:
    """Return a defensive copy of the unified source catalog, optionally filtered."""
    sources = SEARCH_SOURCE_CATALOG
    if group:
        sources = [source for source in sources if source["group"] == group]
    return deepcopy(sources)
