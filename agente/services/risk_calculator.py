# logic/risk_calculator.py
from typing import Dict, Any, List

def calculate_flood_risk(
    atlas_data: Dict[str, Any],
    weather_forecast: List[Dict[str, Any]],
    periodo: int = 24
) -> str:
    """
    Calcula el riesgo de inundación combinando el riesgo base y el pronóstico de lluvia
    para un periodo de 24 o 48 horas.
    """
    # 1. Calcular lluvia total pronosticada
    total_rain_mm = sum(f.get('lluvia_mm', 0.0) for f in weather_forecast)

    # 2. Asignar puntaje de riesgo base del atlas
    risk_map = {"Bajo": 1, "Medio": 2, "Alto": 3, "Muy Alto": 4}
    base_risk_score = risk_map.get(atlas_data.get('riesgo'), 0)

    # 3. Asignar puntaje por la lluvia, ajustando umbrales según el periodo
    rain_score = 0
    # Umbrales para 24 horas
    moderate_threshold = 5
    high_threshold = 15
    
    # Si el periodo es de 48 horas, duplicamos los umbrales
    if periodo == 48:
        moderate_threshold *= 2 # 10 mm
        high_threshold *= 2   # 30 mm

    if moderate_threshold <= total_rain_mm < high_threshold:
        rain_score = 1  # Lluvia Moderada
    elif total_rain_mm >= high_threshold:
        rain_score = 2  # Lluvia Fuerte

    # 4. Fórmula de cálculo final (sin cambios)
    final_score = base_risk_score + rain_score

    # 5. Convertir el puntaje final a una categoría
    if final_score <= 2:
        return "Bajo"
    elif final_score <= 4:
        return "Moderado"
    elif final_score <= 5:
        return "Alto"
    else:
        return "Muy Alto"