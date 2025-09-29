# logic/risk_calculator.py
from typing import Dict, Any, List

def calculate_flood_risk(atlas_data: Dict[str, Any], weather_forecast: List[Dict[str, Any]]) -> str:
    """
    Calcula el riesgo de inundación combinando el riesgo base y el pronóstico de lluvia.
    """
    # 1. Calcular lluvia total pronosticada para las próximas 24h
    total_rain_mm = sum(f.get('lluvia_mm', 0.0) for f in weather_forecast)

    # 2. Asignar puntaje de riesgo base del atlas
    risk_map = {"Bajo": 1, "Medio": 2, "Alto": 3, "Muy Alto": 4}
    base_risk_score = risk_map.get(atlas_data.get('riesgo'), 0)

    # 3. Asignar puntaje por la lluvia
    rain_score = 0
    if 5 <= total_rain_mm < 15:
        rain_score = 1  # Moderado
    elif total_rain_mm >= 15:
        rain_score = 2  # Fuerte

    # 4. Fórmula de cálculo final (puedes ajustarla)
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