# agent/config.py
from typing import Dict, Any

# Configuración del agente
GEMINI_CONFIG = {
    "model": "gemini-pro",
    "temperature": 0.1,
    "max_tokens": 800
}

# Mapeo de niveles de riesgo a probabilidades
RIESGO_A_PROBABILIDAD = {
    "Bajo": 0.2,
    "Moderado": 0.45, 
    "Alto": 0.65,
    "Muy Alto": 0.85
}

# Configuración de mapas
MAP_CONFIG = {
    "tipo": "geojson",
    "directorio_salida": "./maps/",
    "zoom_default": 12,
    "centro_cdmx": [19.4326, -99.1332]
}

def crear_prompt_analisis(alcaldia: str, contexto: Dict[str, Any]) -> str:
    """Crea el prompt para Gemini basado en los datos disponibles"""
    
    # Datos con valores por defecto para evitar KeyError
    riesgo_base = contexto.get('datos_atlas', {}).get('riesgo', 'No disponible')
    lluvia_24h = contexto.get('lluvia_total_24h', 0)
    lluvia_48h = contexto.get('lluvia_total_48h', 0)
    area_m2 = contexto.get('datos_atlas', {}).get('area_m2', 'No disponible')
    descripcion = contexto.get('datos_atlas', {}).get('descripcion', 'No disponible')
    
    return f"""
Eres un experto en riesgo de inundaciones en CDMX. Analiza: {alcaldia}

DATOS DISPONIBLES:
- Riesgo base del atlas: {riesgo_base}
- Lluvia pronosticada 24h: {lluvia_24h:.1f} mm
- Lluvia pronosticada 48h: {lluvia_48h:.1f} mm
- Área de zona de riesgo: {area_m2} m²
- Descripción: {descripcion}

PROPORCIONA un análisis JSON con:
1. factores_riesgo: lista de 3-5 factores principales
2. explicacion_corta: texto breve (1-2 oraciones)
3. recomendaciones: lista de 2-3 recomendaciones prácticas

Responde SOLO en formato JSON, sin texto adicional.
Ejemplo de formato:
{{
    "factores_riesgo": ["lluvia_intensa", "drenaje_limitado"],
    "explicacion_corta": "Explicación breve del riesgo",
    "recomendaciones": ["Recomendación 1", "Recomendación 2"]
}}
"""