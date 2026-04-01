"""
interview_data.py - Pool de preguntas y estructuras para simulador de entrevistas

Incluye:
- Preguntas RRHH usando método STAR (15 preguntas variadas)
- Configuraciones por tipo de entrevista
- Datos de empresas populares en Argentina
"""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class InterviewType(Enum):
    """Tipos de entrevista disponibles."""
    TECHNICAL = "technical"
    RRHH = "rrhh"


class FeedbackMode(Enum):
    """Modos de feedback disponibles."""
    IMMEDIATE = "immediate"  # Después de cada respuesta
    FINAL = "final"  # Al terminar toda la entrevista


@dataclass
class RRHHQuestion:
    """Estructura de una pregunta RRHH con metodología STAR."""
    id: str
    category: str
    question: str
    star_focus: str
    what_to_avoid: str
    golden_tip: str
    difficulty: str  # "easy", "medium", "hard"


# Pool de 15 preguntas RRHH variadas
RRHH_QUESTIONS_POOL: List[RRHHQuestion] = [
    RRHHQuestion(
        id="tell_me_about_yourself",
        category="intro",
        question="Contame sobre vos. ¿Quién sos profesionalmente y por qué estás en IT?",
        star_focus="Presentación concisa (30-60 segundos), conexión clara con el rol que buscás",
        what_to_avoid="NO contar tu vida personal completa, ni decir 'no sé qué decir', ni ser muy vago",
        golden_tip="Estructura: Presente (quién sos ahora) + Pasado (cómo llegaste acá) + Futuro (por qué este rol te entusiasma). Mantenelo en 60 segundos.",
        difficulty="easy"
    ),
    
    RRHHQuestion(
        id="strengths_weaknesses",
        category="self_awareness",
        question="¿Cuáles son tus 2 principales fortalezas y 1 debilidad real?",
        star_focus="Autoconocimiento honesto, debilidad con plan de mejora concreto",
        what_to_avoid="NO uses debilidades falsas tipo 'soy perfeccionista', NO des fortalezas genéricas sin ejemplos",
        golden_tip="Fortaleza: dá un ejemplo específico + resultado medible. Debilidad: una real + 3 acciones concretas que estás haciendo YA para mejorar.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="challenge_overcome",
        category="problem_solving",
        question="Describí un desafío técnico o de equipo difícil que hayas superado recientemente.",
        star_focus="Estructura STAR estricta: Situación concreta, Task claro, Actions específicas de VOS, Resultado medible",
        what_to_avoid="NO uses 'nosotros' sin aclarar tu rol específico, NO des resultados vagos ('mejoró todo'), NO te extiendas más de 2 minutos",
        golden_tip="Usá el método STAR al pie de la letra. Terminá SIEMPRE con una métrica: 'reduje el tiempo de carga en 40%', 'aumenté la eficiencia del equipo en 25%'.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="why_this_company",
        category="motivation",
        question="¿Por qué querés trabajar específicamente en nuestra empresa y no en otra?",
        star_focus="Conocimiento real de la empresa + conexión personal + alineación con tus objetivos",
        what_to_avoid="NO digas 'porque es una gran empresa' (genérico), NO menciones solo el sueldo, NO mientas sobre lo que sabés",
        golden_tip="Investigá antes: mencioná 2-3 cosas específicas (cultura, producto, valores) y conectalas con tu experiencia. Ej: 'Vi que priorizan X, y eso me entusiasma porque...'",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="what_you_know_about_us",
        category="research",
        question="¿Qué sabés sobre nuestra empresa, nuestro producto y nuestros desafíos actuales?",
        star_focus="Demostrar que investigaste: producto, competencia, mercado, cultura, noticias recientes",
        what_to_avoid="NO digas 'no tuve tiempo de investigar', NO des datos incorrectos, NO seas superficial",
        golden_tip="Prepará 3 puntos clave: (1) qué hacen y para quién, (2) un desafío actual que leíste, (3) por qué te resuena su cultura/valores.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="conflict_resolution",
        category="teamwork",
        question="Contame sobre un conflicto que tuviste con un compañero o jefe. ¿Cómo lo resolviste?",
        star_focus="Manejo emocional maduro, enfoque en solución, no culpar al otro",
        what_to_avoid="NO culpes al otro ni digas 'era un idiota', NO digas 'nunca tuve conflictos' (irreal), NO seas pasivo-agresivo",
        golden_tip="Enfocate en: (1) qué pasó objetivamente, (2) qué hiciste VOS para mejorar la situación, (3) qué aprendiste, (4) cómo está la relación ahora.",
        difficulty="hard"
    ),
    
    RRHHQuestion(
        id="failure_lesson",
        category="resilience",
        question="¿Podés describir un proyecto o decisión que falló bajo tu responsabilidad? ¿Qué aprendiste?",
        star_focus="Honestidad, autocrítica constructiva, cambios concretos que hiciste después",
        what_to_avoid="NO uses ejemplos menores ('me olvidé de traer café'), NO culpes a otros/circunstancias externas, NO digas 'no tuve fallos'",
        golden_tip="Elegí un fallo real pero no catastrófico. Enfocate 20% en el problema y 80% en: qué hiciste diferente después, qué sistema implementaste para que no se repita.",
        difficulty="hard"
    ),
    
    RRHHQuestion(
        id="pressure_deadline",
        category="stress_management",
        question="¿Cómo manejás la presión y los deadlines ajustados? ¿Un ejemplo?",
        star_focus="Sistema concreto de manejo de stress + priorización + ejemplo real",
        what_to_avoid="NO digas 'no me estreso' (irreal), NO digas 'trabajo más horas' como única solución",
        golden_tip="Describí tu sistema: cómo priorizás (matriz urgente/importante), cómo comunicás avances, cómo pedís ayuda si es necesario. Dá un ejemplo con resultado positivo.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="leadership_without_title",
        category="leadership",
        question="¿Una vez que lideraste o influenciaste positivamente a un equipo sin tener el título de líder?",
        star_focus="Influencia informal, liderazgo por ejemplo, resultado colectivo",
        what_to_avoid="NO centres todo en vos ('yo hice todo'), NO uses un ejemplo donde tu jefe te pidió liderar (eso es título)",
        golden_tip="Buscá un momento donde el equipo estaba atascado/confundido y VOS propusiste algo/guiaste al equipo a la solución sin que te lo pidieran. Medí el impacto en el equipo.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="disagree_with_decision",
        category="communication",
        question="¿Estuviste en desacuerdo con una decisión de tu jefe o equipo? ¿Qué hiciste?",
        star_focus="Cómo planteás desacuerdo profesionalmente, negociación, respeto",
        what_to_avoid="NO digas 'siempre hago lo que me dicen' (pasivo), ni 'discutí hasta imponerme' (agresivo), ni 'ignoré la decisión' (irresponsable)",
        golden_tip="Modelo: (1) Escuché la decisión, (2) Me preparé con datos, (3) Plantee mis preocupaciones con respeto explicando el riesgo, (4) Acepté la decisión final del jefe pero propuse plan B, (5) Resultado.",
        difficulty="hard"
    ),
    
    RRHHQuestion(
        id="learning_new_tech",
        category="adaptability",
        question="¿Cómo aprendés nuevas tecnologías? ¿Un ejemplo reciente de algo que aprendiste por tu cuenta?",
        star_focus="Metodología de aprendizaje autónomo + ejemplo concreto + aplicación práctica",
        what_to_avoid="NO digas 'hago cursos' sin ejemplo específico, NO menciones algo que aprendiste hace 5 años",
        golden_tip="Describí tu método paso a paso: (1) cómo elegís qué aprender, (2) recursos que usás, (3) cómo practicás, (4) cómo aplicás en un proyecto real. Ejemplo reciente (último año).",
        difficulty="easy"
    ),
    
    RRHHQuestion(
        id="work_with_difficult_person",
        category="interpersonal",
        question="¿Trabajaste con alguien difícil (tóxico, negativo, desmotivado)? ¿Cómo lo manejaste?",
        star_focus="Empatía, adaptación, enfoque en objetivos, no juicios",
        what_to_avoid="NO etiquetes a la persona ('era un tóxico'), NO cuentes chismes/confidencias, NO digas 'evité trabajar con él'",
        golden_tip="Enfocate en: (1) Qué hacía la persona específicamente, (2) Cómo te afectaba, (3) Qué estrategia usaste para trabajar igual (comunicación clara, foco en tareas, empatía), (4) Resultado profesional.",
        difficulty="hard"
    ),
    
    RRHHQuestion(
        id="five_years",
        category="career_goals",
        question="¿Dónde te ves en 5 años profesionalmente?",
        star_focus="Ambición realista + alineación con el rol actual + plan concreto",
        what_to_avoid="NO digas 'en tu puesto' (amenaza), ni 'no lo pensé' (falta de dirección), ni 'en otra empresa' (deslealtad)",
        golden_tip="Estructura: (1) Corto plazo (1-2 años): maestría técnica en X área específica, (2) Mediano (3-5 años): liderar proyectos/mentoría/rol senior en Y, (3) Cómo este trabajo te ayuda a llegar ahí.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="questions_for_us",
        category="engagement",
        question="¿Qué preguntas tenés para nosotros? (Mostrá 2-3 buenas preguntas que harías)",
        star_focus="Curiosidad genuina + investigación previa + interés en éxito mutuo",
        what_to_avoid="NO preguntes cosas que están en la web, NI sobre vacaciones/sueldo en primera entrevista, NI 'no tengo preguntas'",
        golden_tip="Buenas preguntas: (1) '¿Cuál sería el desafío más importante en los primeros 3 meses?', (2) '¿Cómo se mide el éxito en este rol?', (3) '¿Qué les gusta más de trabajar acá?'. Prepará 3-4.",
        difficulty="medium"
    ),
    
    RRHHQuestion(
        id="salary_expectations",
        category="negotiation",
        question="¿Cuáles son tus expectativas salariales? (Ejercicio: cómo responderías)",
        star_focus="Respuesta profesional que mantiene negociación abierta",
        what_to_avoid="NO des un número exacto inmediatamente, ni 'lo que ustedes paguen', ni un número ridículamente alto sin justificación",
        golden_tip="Estrategia: (1) 'Mi rango es X-Y basado en mi experiencia y mercado', (2) 'Pero valoro el paquete completo: aprendizaje, cultura, beneficios', (3) '¿Cuál es el rango asignado para este rol?'. Siempre rangos, nunca números exactos.",
        difficulty="medium"
    )
]


def get_random_rrhh_questions(count: int = 5) -> List[RRHHQuestion]:
    """
    Retorna 'count' preguntas aleatorias del pool.
    Asegura variedad de categorías.
    """
    import random
    
    if count >= len(RRHH_QUESTIONS_POOL):
        return RRHH_QUESTIONS_POOL.copy()
    
    # Seleccionar aleatoriamente pero manteniendo variedad de dificultad
    easy = [q for q in RRHH_QUESTIONS_POOL if q.difficulty == "easy"]
    medium = [q for q in RRHH_QUESTIONS_POOL if q.difficulty == "medium"]
    hard = [q for q in RRHH_QUESTIONS_POOL if q.difficulty == "hard"]
    
    # Distribución: 2 easy, 2 medium, 1 hard (para 5 preguntas)
    selected = []
    selected.extend(random.sample(easy, min(2, len(easy))))
    selected.extend(random.sample(medium, min(2, len(medium))))
    selected.extend(random.sample(hard, min(1, len(hard))))
    
    # Si faltan, completar con aleatorias
    remaining = [q for q in RRHH_QUESTIONS_POOL if q not in selected]
    while len(selected) < count and remaining:
        selected.append(random.choice(remaining))
        remaining.remove(selected[-1])
    
    # Barajar orden
    random.shuffle(selected)
    
    return selected[:count]


def get_company_specific_questions(company_name: str) -> List[str]:
    """
    Retorna preguntas específicas comunes para empresas populares de Argentina.
    Si no conoce la empresa, retorna lista vacía.
    """
    company_questions = {
        "mercado libre": [
            "¿Qué sabés sobre los valores de Mercado Libre (priorizar al cliente, innovación constante)?",
            "¿Cómo te adaptarías a un ambiente donde se priorizan resultados sobre procesos?",
        ],
        "mercadolibre": [
            "¿Qué sabés sobre los valores de Mercado Libre (priorizar al cliente, innovación constante)?",
            "¿Cómo te adaptarías a un ambiente donde se priorizan resultados sobre procesos?",
        ],
        "globant": [
            "¿Qué te atrae del modelo de 'pod' y equipos auto-organizados de Globant?",
            "¿Cómo manejarías trabajar para un cliente internacional con cultura muy diferente?",
        ],
        "accenture": [
            "¿Estás cómodo con la rotación de proyectos y tecnologías cada 6-12 meses?",
            "¿Cómo te ves en un ambiente corporativo grande con procesos definidos?",
        ],
        "despegar": [
            "¿Qué sabés sobre los desafíos técnicos de una plataforma de viajes (alta demanda, pagos)?",
            "¿Cómo asegurarías la calidad de código en un ambiente de entregas frecuentes?",
        ],
        "uala": [
            "¿Qué sabés sobre las regulaciones fintech y por qué te interesa este rubro?",
            "¿Cómo priorizarías seguridad vs velocidad de desarrollo en una fintech?",
        ],
        "pedidos ya": [
            "¿Qué sabés sobre los desafíos logísticos de delivery en tiempo real?",
            "¿Cómo manejarías la presión de un ambiente de alto crecimiento y deadlines ajustados?",
        ],
        "fravega": [
            "¿Qué sabés sobre la transformación digital del retail tradicional?",
            "¿Cómo ayudarías a una empresa tradicional a competir con Amazon/MercadoLibre?",
        ],
        "banco": [
            "¿Qué sabés sobre la transformación digital de los bancos tradicionales?",
            "¿Cómo balanceás innovación con la seguridad requerida en sistemas bancarios?",
        ],
        "santander": [
            "¿Qué sabés sobre la transformación digital de los bancos tradicionales?",
            "¿Cómo balanceás innovación con la seguridad requerida en sistemas bancarios?",
        ],
        "galicia": [
            "¿Qué sabés sobre la transformación digital de los bancos tradicionales?",
            "¿Cómo balanceás innovación con la seguridad requerida en sistemas bancarios?",
        ],
        "naranja": [
            "¿Qué te interesa del mundo fintech vs banca tradicional?",
            "¿Cómo priorizarías la experiencia de usuario en productos financieros complejos?",
        ],
        "mulesoft": [
            "¿Qué sabés sobre integración de sistemas y APIs en entornos enterprise?",
            "¿Cómo explicarías el valor de una herramienta de integración a un cliente técnico?",
        ],
        "auth0": [
            "¿Qué sabés sobre autenticación, OAuth y seguridad de identidad?",
            "¿Cómo diseñarías un sistema de autenticación que sea seguro pero fácil de usar?",
        ],
    }
    
    company_lower = company_name.lower().strip()
    return company_questions.get(company_lower, [])


# Datos de empresas populares en Argentina para mostrar al usuario
COMPANY_DATA = {
    "mercado libre": {
        "rating": 4.2,
        "difficulty": "Media",
        "duration": "2-3 semanas",
        "culture": ["Aprendizaje constante", "Orientación a resultados", "Innovación"],
        "common_questions": [
            "¿Cómo priorizarías features con deadlines ajustados?",
            "Diferencia entre un buen y un gran desarrollador",
        ],
        "tips": "Enfocate en mostrar Ownership (sentido de dueño) y impacto medible"
    },
    "globant": {
        "rating": 3.8,
        "difficulty": "Media-Alta",
        "duration": "2-4 semanas",
        "culture": ["Trabajo en equipo", "Crecimiento", "Diversidad"],
        "common_questions": [
            "¿Cómo te adaptás a nuevas tecnologías rápidamente?",
            "Experiencia trabajando con clientes internacionales",
        ],
        "tips": "Mostrá adaptabilidad y experiencia multicliente"
    },
    "accenture": {
        "rating": 3.9,
        "difficulty": "Media",
        "duration": "3-4 semanas",
        "culture": ["Profesionalismo", "Procesos", "Escala global"],
        "common_questions": [
            "¿Cómo manejás la presión en proyectos grandes?",
            "Trabajo en equipos distribuidos globalmente",
        ],
        "tips": "Enfocate en procesos, metodologías ágiles y trabajo en equipo"
    },
    "uala": {
        "rating": 4.3,
        "difficulty": "Alta",
        "duration": "3-5 semanas",
        "culture": ["Innovación", "Movimiento rápido", "Impacto social"],
        "common_questions": [
            "¿Cómo balanceás velocidad con seguridad en fintech?",
            "¿Qué sabés de regulaciones financieras?",
        ],
        "tips": "Mostrá interés genuino en fintech y balance entre seguridad/innovación"
    },
    "uala": {
        "rating": 4.3,
        "difficulty": "Alta",
        "duration": "3-5 semanas",
        "culture": ["Innovación", "Movimiento rápido", "Impacto social"],
        "common_questions": [
            "¿Cómo balanceás velocidad con seguridad en fintech?",
            "¿Qué sabés de regulaciones financieras?",
        ],
        "tips": "Mostrá interés genuino en fintech y balance entre seguridad/innovación"
    },
}
