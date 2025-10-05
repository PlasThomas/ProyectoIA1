# agent/__init__.py
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import google.generativeai as genai

# Importaciones de tus otros módulos
from .config import GEMINI_CONFIG, crear_prompt_analisis
from services.risk_calculator import calculate_flood_risk
from services.wheater_api import GeocodingService, WeatherService, transform_forecast_to_db_records
from db.operations import get_atlas_by_alcaldia, get_recent_clima_by_alcaldia

load_dotenv()

class FloodPredictionAgent:
    """
    Agente híbrido que predice el riesgo de inundación.
    Intenta obtener datos de la API en tiempo real y usa la base de datos como respaldo.
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
    
    async def predict_for_alcaldia(self, alcaldia: str):
        """Orquesta el proceso de predicción completo usando el modelo híbrido."""
        try:
            print(f"\nAnalizando {alcaldia} (modelo híbrido)...")
            
            contexto = await self._obtener_contexto_hibrido(alcaldia)

            if not contexto.get('datos_atlas'):
                return self._respuesta_error(f"No se encontraron datos en el atlas para: {alcaldia}")
            if not contexto.get('pronostico_24h'):
                 return self._respuesta_error(f"Fallo crítico: No se pudo obtener el clima ni por API ni por BD para: {alcaldia}")
            
            analisis_gemini = await self._analizar_con_gemini(alcaldia, contexto)
            probabilidades = self._calcular_probabilidades(contexto)
            
            respuesta_final = self._estructurar_respuesta(alcaldia, probabilidades, analisis_gemini)
            respuesta_final["datos_utilizados"]["fuente_clima"] = contexto["fuente_clima"]
            return respuesta_final
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._respuesta_error(f"Error fatal en la predicción: {str(e)}")
    
    async def _obtener_contexto_hibrido(self, alcaldia: str):
        """
        Intenta obtener el pronóstico del clima de la API (Plan A)
        y si falla, usa la base de datos como respaldo (Plan B).
        """
        atlas_data_list = get_atlas_by_alcaldia(self.db, alcaldia, exact=True)
        atlas_data = atlas_data_list[0].as_dict() if atlas_data_list else {}
        
        try:
            # --- PLAN A: API EN TIEMPO REAL ---
            print("  -> Intentando obtener clima desde la API en tiempo real...")
            coords = await self.geocoder.geocode_cdmx_location(alcaldia)
            if not coords: raise ValueError("Geocodificación fallida")

            forecast_api_data = await self.weather_service.get_forecast(coords['lat'], coords['lon'])
            if not forecast_api_data: raise ValueError("La respuesta de la API de pronóstico está vacía")
            
            pronostico_records = transform_forecast_to_db_records(forecast_api_data, alcaldia)
            fuente_clima = "API en Tiempo Real"
            print("  ✔️ Éxito: Clima obtenido de la API.")

        except Exception as e:
            # --- PLAN B: RESPALDO CON BASE DE DATOS ---
            print(f"  ⚠️ ADVERTENCIA: La llamada a la API falló ({e}). Usando base de datos como respaldo.")
            pronostico_db_objetos = get_recent_clima_by_alcaldia(self.db, alcaldia, limit=8)
            pronostico_records = [p.as_dict() for p in pronostico_db_objetos]
            fuente_clima = "Base de Datos (Respaldo)"
            if not pronostico_records:
                print("  ❌ ERROR: No se encontraron datos de clima en la base de datos.")
        
        lluvia_24h = sum(p.get('lluvia_mm', 0.0) for p in pronostico_records)

        return {
            "datos_atlas": atlas_data,
            "pronostico_24h": pronostico_records,
            "lluvia_total_24h": lluvia_24h,
            "fuente_clima": fuente_clima
        }

    async def _analizar_con_gemini(self, alcaldia: str, contexto: dict):
        """Llama a la API de Gemini de forma asíncrona para el análisis contextual."""
        if not self.gemini_available:
            return self._analisis_por_defecto("Análisis simulado por falta de API Key de Gemini.")
        try:
            prompt = crear_prompt_analisis(alcaldia, contexto)
            response = await self.llm.generate_content_async(prompt)
            return json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
        except Exception as e:
            return self._analisis_por_defecto(f"Análisis no disponible por error en Gemini: {e}")
        
    def _calcular_probabilidades(self, contexto: dict):
        """Calcula el riesgo usando la lógica externa de risk_calculator."""
        riesgo = calculate_flood_risk(contexto['datos_atlas'], contexto['pronostico_24h'])
        return {
            "24_horas": {
                "nivel_riesgo": riesgo,
                "lluvia_total_mm": contexto['lluvia_total_24h']
            }
        }

    def _estructurar_respuesta(self, alcaldia: str, probabilidades: dict, analisis_gemini: dict):
        """Construye el diccionario final de la respuesta."""
        return {
            "alcaldia": alcaldia,
            "predicciones": probabilidades,
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