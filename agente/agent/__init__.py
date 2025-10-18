import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import google.generativeai as genai

from .config import GEMINI_CONFIG, crear_prompt_analisis
from services.risk_calculator import calculate_flood_risk
from services.wheater_api import GeocodingService, WeatherService, transform_forecast_to_db_records
from db.operations import get_atlas_by_alcaldia, get_recent_clima_by_alcaldia

load_dotenv()

class FloodPredictionAgent:
    """
    Agente híbrido que predice el riesgo de inundación para periodos de 24 y 48 horas.
    """
    def __init__(self, db_session: Session):
        self.db = db_session
        self.gemini_available = False
        self.llm = None
        self._setup_gemini()
        self.geocoder = GeocodingService()
        self.weather_service = WeatherService()
        
    def _setup_gemini(self):
        """Configura el modelo de Gemini si la API key está disponible."""
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("ADVERTENCIA: GOOGLE_API_KEY no encontrada. El análisis de IA se ejecutará en modo SIMULADO.")
                return
            genai.configure(api_key=google_api_key)
            self.llm = genai.GenerativeModel(GEMINI_CONFIG["model"])
            self.gemini_available = True
        except Exception as e:
            print(f"ADVERTENCIA: Error configurando Gemini: {e}")
    
    # MODIFICADO: Acepta el parámetro 'periodo'
    async def predict_for_alcaldia(self, alcaldia: str, periodo: int = 24):
        """Orquesta el proceso de predicción completo para un periodo específico."""
        try:
            print(f"\nAnalizando {alcaldia} (modelo híbrido para {periodo}h)...")
            
            # Pasa el periodo para obtener el contexto correcto
            contexto = await self._obtener_contexto_hibrido(alcaldia, periodo)

            if not contexto.get('datos_atlas'):
                return self._respuesta_error(f"No se encontraron datos en el atlas para: {alcaldia}")
            if not contexto.get('pronostico_completo'):
                 return self._respuesta_error(f"Fallo crítico: No se pudo obtener el clima ni por API ni por BD para: {alcaldia}")
            
            analisis_gemini = await self._analizar_con_gemini(alcaldia, contexto)
            
            # Pasa el periodo para calcular las probabilidades
            predicciones = self._calcular_predicciones(contexto)
            
            respuesta_final = self._estructurar_respuesta(alcaldia, predicciones, analisis_gemini)
            respuesta_final["datos_utilizados"]["fuente_clima"] = contexto["fuente_clima"]
            return respuesta_final
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._respuesta_error(f"Error fatal en la predicción: {str(e)}")
    
    # MODIFICADO: Acepta y utiliza el parámetro 'periodo'
    async def _obtener_contexto_hibrido(self, alcaldia: str, periodo: int):
        """
        Obtiene el pronóstico del clima para hasta 48 horas y los datos del atlas.
        Intenta usar la API como Plan A y la BD como Plan B.
        """
        atlas_data_list = get_atlas_by_alcaldia(self.db, alcaldia, exact=True)
        atlas_data = atlas_data_list[0].as_dict() if atlas_data_list else {}
        
        # Necesitamos hasta 16 registros para cubrir 48 horas (16 * 3h = 48h)
        registros_necesarios = 16 

        try:
            # --- PLAN A: API EN TIEMPO REAL ---
            print("  -> Intentando obtener clima desde la API en tiempo real...")
            coords = await self.geocoder.geocode_cdmx_location(alcaldia)
            if not coords: raise ValueError("Geocodificación fallida")

            forecast_api_data = await self.weather_service.get_forecast(coords['lat'], coords['lon'])
            if not forecast_api_data: raise ValueError("La respuesta de la API de pronóstico está vacía")
            
            pronostico_records = transform_forecast_to_db_records(forecast_api_data, alcaldia)
            fuente_clima = "API en Tiempo Real"
            print("Éxito: Clima obtenido de la API.")

        except Exception as e:
            # --- PLAN B: RESPALDO CON BASE DE DATOS ---
            print(f"ADVERTENCIA: La llamada a la API falló ({e}). Usando base de datos como respaldo.")
            pronostico_db_objetos = get_recent_clima_by_alcaldia(self.db, alcaldia, limit=registros_necesarios)
            pronostico_records = [p.as_dict() for p in pronostico_db_objetos]
            fuente_clima = "Base de Datos (Respaldo)"
            if not pronostico_records:
                print("ERROR: No se encontraron datos de clima en la base de datos.")
        
        # Preparamos los datos para ambos periodos
        pronostico_24h = pronostico_records[:8]
        pronostico_48h = pronostico_records[:16]

        lluvia_24h = sum(p.get('lluvia_mm', 0.0) for p in pronostico_24h)
        lluvia_48h = sum(p.get('lluvia_mm', 0.0) for p in pronostico_48h)

        return {
            "datos_atlas": atlas_data,
            "pronostico_completo": pronostico_records, # Todos los registros obtenidos
            "pronostico_24h": pronostico_24h,
            "pronostico_48h": pronostico_48h,
            "lluvia_total_24h": lluvia_24h,
            "lluvia_total_48h": lluvia_48h, # Añadimos el cálculo de 48h
            "fuente_clima": fuente_clima
        }

    async def _analizar_con_gemini(self, alcaldia: str, contexto: dict):
        """Llama a la API de Gemini (sin cambios)."""
        if not self.gemini_available:
            return self._analisis_por_defecto("Análisis simulado por falta de API Key de Gemini.")
        try:
            # El prompt ahora recibirá el contexto con datos de 24h y 48h
            prompt = crear_prompt_analisis(alcaldia, contexto)
            response = await self.llm.generate_content_async(prompt)
            return json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
        except Exception as e:
            return self._analisis_por_defecto(f"Análisis no disponible por error en Gemini: {e}")
            
    # MODIFICADO: Renombrado y ajustado para calcular ambos periodos
    def _calcular_predicciones(self, contexto: dict):
        """Calcula el riesgo para 24 y 48 horas usando la lógica externa."""
        # Cálculo para 24 horas
        riesgo_24h = calculate_flood_risk(
            contexto['datos_atlas'], 
            contexto['pronostico_24h'], 
            periodo=24
        )
        
        # Cálculo para 48 horas
        riesgo_48h = calculate_flood_risk(
            contexto['datos_atlas'], 
            contexto['pronostico_48h'],
            periodo=48
        )
        
        return {
            "24_horas": {
                "nivel_riesgo": riesgo_24h,
                "lluvia_total_mm": contexto['lluvia_total_24h']
            },
            "48_horas": {
                "nivel_riesgo": riesgo_48h,
                "lluvia_total_mm": contexto['lluvia_total_48h']
            }
        }

    # MODIFICADO: 'probabilidades' ahora es 'predicciones'
    def _estructurar_respuesta(self, alcaldia: str, predicciones: dict, analisis_gemini: dict):
        """Construye el diccionario final de la respuesta."""
        return {
            "alcaldia": alcaldia,
            "predicciones": predicciones,
            "analisis_contextual": analisis_gemini,
            "datos_utilizados": {
                "modo_analisis": "gemini" if self.gemini_available else "simulado"
            }
        }

    def _respuesta_error(self, mensaje: str):
        """Formatea una respuesta de error estándar."""
        return {"error": True, "mensaje": mensaje}

    def _analisis_por_defecto(self, explicacion: str):
        """Genera un análisis por defecto cuando Gemini no está disponible."""
        return {
            "factores_riesgo": ["No disponible"],
            "explicacion_corta": explicacion,
            "recomendaciones": ["Consultar fuentes oficiales."]
        }