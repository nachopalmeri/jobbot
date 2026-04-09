"""
glassdoor_service.py - Servicio de datos de empresas para preparación de entrevistas

Integra:
- Datos financieros de financial_service.py
- Datos específicos de interview_data.py (cultura, preguntas frecuentes)
- Web scraping básico de Glassdoor (futuro)

Para preparar candidatos con info real de la empresa antes de la entrevista.
"""

import logging
from typing import Dict, Optional, List
from pathlib import Path

# Importar datos de empresas
from interview_data import COMPANY_DATA, get_company_specific_questions

# Intentar importar financial_service para datos de ticker
financial_service_available = False
financial_data = None
try:
    from financial_service import FinancialService, DOMAIN_TO_TICKER
    financial_service_available = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class GlassdoorService:
    """
    Servicio para obtener datos de empresas para preparación de entrevistas.
    
    Combina datos locales + servicio financiero + scraping (futuro).
    """
    
    def __init__(self):
        self.financial_service = None
        if financial_service_available:
            try:
                self.financial_service = FinancialService()
            except:
                pass
    
    async def get_company_interview_data(self, company_name: str) -> Optional[Dict]:
        """
        Obtiene datos completos de una empresa para preparar entrevista.
        
        Args:
            company_name: Nombre de la empresa (ej: "Mercado Libre", "Globant")
            
        Returns:
            Dict con datos de la empresa o None si no encuentra nada
        """
        if not company_name:
            return None
            
        company_lower = company_name.lower().strip()
        
        # 1. Buscar en datos locales primero (interview_data.py)
        local_data = self._get_local_company_data(company_lower, company_name)
        if local_data:
            return local_data
        
        # 2. Intentar obtener datos financieros si existe servicio
        financial_data = await self._get_financial_data(company_name)
        if financial_data:
            return financial_data
        
        # 3. Si no hay nada, retornar datos genéricos útiles
        return self._get_generic_company_data(company_name)
    
    def _get_local_company_data(self, company_lower: str, original_name: str) -> Optional[Dict]:
        """Busca datos en interview_data.py"""
        
        # Buscar coincidencia exacta o parcial en COMPANY_DATA
        for key, data in COMPANY_DATA.items():
            if key in company_lower or company_lower in key:
                questions = get_company_specific_questions(original_name)
                
                return {
                    "name": original_name.title(),
                    "source": "jobbot_database",
                    "found": True,
                    "rating": data.get("rating", 3.5),
                    "interview_difficulty": data.get("difficulty", "Media"),
                    "interview_duration": data.get("duration", "2-4 semanas"),
                    "culture": data.get("culture", []),
                    "common_questions": questions if questions else data.get("common_questions", []),
                    "tips": data.get("tips", "Investigá la empresa antes de la entrevista"),
                    "recommendation_rate": "70-80%",
                    "hiring_departments": ["IT", "Producto", "Data"],
                }
        
        # Buscar con variantes comunes
        variants = {
            "mercadolibre": "mercado libre",
            "mercado": "mercado libre",
            "meli": "mercado libre",
            "ml": "mercado libre",
            "mp": "mercado pago",
            "uala": "uala",
            "pedidosya": "pedidos ya",
            "despegar": "despegar",
            "fravega": "fravega",
            "globant": "globant",
            "accenture": "accenture",
            "auth0": "auth0",
            "mulesoft": "mulesoft",
            "santander": "banco",
            "galicia": "banco",
            "bbva": "banco",
            "icbc": "banco",
            "macro": "banco",
            "naranja": "naranja",
            "banco": "banco",
        }
        
        for variant, canonical in variants.items():
            if variant in company_lower:
                # Buscar datos del canonical
                canonical_data = COMPANY_DATA.get(canonical)
                if canonical_data:
                    questions = get_company_specific_questions(original_name)
                    
                    return {
                        "name": original_name.title(),
                        "source": "jobbot_database",
                        "found": True,
                        "rating": canonical_data.get("rating", 3.5),
                        "interview_difficulty": canonical_data.get("difficulty", "Media"),
                        "interview_duration": canonical_data.get("duration", "2-4 semanas"),
                        "culture": canonical_data.get("culture", []),
                        "common_questions": questions if questions else canonical_data.get("common_questions", []),
                        "tips": canonical_data.get("tips", "Investigá la empresa antes de la entrevista"),
                        "recommendation_rate": "70-80%",
                        "hiring_departments": ["IT", "Producto", "Data"],
                        "note": f"Usando datos de {canonical.title()} como referencia"
                    }
        
        return None
    
    async def _get_financial_data(self, company_name: str) -> Optional[Dict]:
        """Intenta obtener datos del financial_service.py"""
        
        if not self.financial_service:
            return None
        
        # Buscar dominio/ticker para esta empresa
        # Intentar con dominios comunes
        domains_to_try = [
            f"{company_name.lower().replace(' ', '')}.com",
            f"{company_name.lower().replace(' ', '')}.com.ar",
            f"{company_name.lower().replace(' ', '')}.co",
        ]
        
        # Agregar casos especiales conocidos
        special_domains = {
            "mercado libre": "mercadolibre.com",
            "mercadolibre": "mercadolibre.com",
            "meli": "mercadolibre.com",
            "globant": "globant.com",
            "uala": "uala.com.ar",
            "pedidos ya": "pedidosya.com",
            "pedidosya": "pedidosya.com",
            "despegar": "despegar.com",
            "fravega": "fravega.com",
            "accenture": "accenture.com",
            "auth0": "auth0.com",
            "mulesoft": "mulesoft.com",
        }
        
        company_lower = company_name.lower().strip()
        if company_lower in special_domains:
            domains_to_try.insert(0, special_domains[company_lower])
        
        # Intentar obtener datos de empresa
        for domain in domains_to_try:
            try:
                company_info = await self.financial_service.get_company_info(domain)
                if company_info:
                    return {
                        "name": company_info.get("name", company_name),
                        "source": "financial_data",
                        "found": True,
                        "industry": company_info.get("industry", "Tecnología"),
                        "sector": company_info.get("sector", "Software"),
                        "employees": company_info.get("employees", "No disponible"),
                        "description": company_info.get("description", ""),
                        "website": company_info.get("website", ""),
                        "rating": 3.8,  # Genérico si no tenemos Glassdoor
                        "interview_difficulty": "Media",
                        "interview_duration": "2-4 semanas",
                        "culture": ["Innovación", "Crecimiento", "Tecnología"],
                        "common_questions": get_company_specific_questions(company_name),
                        "tips": f"Investigá sobre {company_name} en su web y LinkedIn",
                        "recommendation_rate": "70%",
                        "hiring_departments": ["IT", "Ingeniería"],
                        "financial_data": {
                            "market_cap": company_info.get("market_cap"),
                            "revenue": company_info.get("revenue"),
                            "ticker": company_info.get("ticker"),
                        } if company_info.get("ticker") else None
                    }
            except:
                continue
        
        return None
    
    def _get_generic_company_data(self, company_name: str) -> Dict:
        """Retorna datos genéricos útiles cuando no hay datos específicos"""
        
        return {
            "name": company_name.title(),
            "source": "generic",
            "found": False,
            "rating": None,
            "interview_difficulty": "Media (estimado)",
            "interview_duration": "2-3 semanas (típico en Argentina)",
            "culture": [],
            "common_questions": [
                "¿Por qué querés trabajar acá?",
                "¿Qué sabés sobre nuestra empresa?",
                "¿Cómo te ves aportando a nuestro equipo?",
            ],
            "tips": f"No tenemos datos específicos de {company_name}, pero te recomiendo: (1) Revisar su web y LinkedIn, (2) Buscar 'entrevista {company_name} Argentina' en Google, (3) Preguntar en comunidades de IT si alguien entrevistó ahí",
            "recommendation_rate": "No disponible",
            "hiring_departments": ["IT (probablemente)"],
            "suggestion": f"¿Es {company_name} una empresa mediana/grande de Argentina? Podrías sugerirnos agregarla a nuestra base de datos.",
        }
    
    def format_company_info_for_user(self, company_data: Dict) -> str:
        """
        Formatea los datos de la empresa para mostrar al usuario.
        Retorna texto listo para enviar por Telegram.
        """
        if not company_data:
            return "❌ No pude obtener información sobre esa empresa."
        
        name = company_data.get("name", "La empresa")
        
        lines = [f"🔍 <b>Info sobre {name}</b>\n"]
        
        # Rating y dificultad
        rating = company_data.get("rating")
        if rating:
            stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
            lines.append(f"📊 Rating empleados: {rating}/5 {stars}")
        
        difficulty = company_data.get("interview_difficulty")
        if difficulty:
            emoji = "🟢" if "Fácil" in difficulty else "🟡" if "Media" in difficulty else "🔴"
            lines.append(f"{emoji} Dificultad entrevistas: {difficulty}")
        
        duration = company_data.get("interview_duration")
        if duration:
            lines.append(f"⏱ Duración típica del proceso: {duration}")
        
        # Cultura
        culture = company_data.get("culture", [])
        if culture:
            lines.append(f"\n💡 <b>Cultura destacada:</b>")
            for item in culture[:4]:
                lines.append(f"   • {item}")
        
        # Preguntas frecuentes
        questions = company_data.get("common_questions", [])
        if questions:
            lines.append(f"\n❓ <b>Preguntas frecuentes reportadas:</b>")
            for i, q in enumerate(questions[:3], 1):
                lines.append(f"   {i}. {q}")
        
        # Tips
        tips = company_data.get("tips")
        if tips:
            lines.append(f"\n💎 <b>Tips para la entrevista:</b>")
            lines.append(f"   {tips}")
        
        # Nota especial
        note = company_data.get("note")
        if note:
            lines.append(f"\n<i>ℹ️ {note}</i>")
        
        # Sugerencia si no encontramos datos
        suggestion = company_data.get("suggestion")
        if suggestion:
            lines.append(f"\n<i>💬 {suggestion}</i>")
        
        return "\n".join(lines)


# Instancia global para usar
glassdoor_service = GlassdoorService()
