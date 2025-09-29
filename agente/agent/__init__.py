# agent/__init__.py
from typing import Dict, Any
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .config import (
    GEMINI_CONFIG,
    RIESGO_A_PROBABILIDAD, 
    MAP_CONFIG,
    crear_prompt_analisis
)

load_dotenv()

class FloodPredictionAgent:
    """Agente especializado en prediccion de inundaciones para CDMX"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.gemini_available = False
        self.llm = None
        self._setup_gemini()
        
    def _setup_gemini(self):
        """Configurar Gemini sin usar langchain"""
        try:
            import google.generativeai as genai
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("ADVERTENCIA: GOOGLE_API_KEY no encontrada en variables de entorno")
                return
            
            genai.configure(api_key=google_api_key)
            self.llm = genai.GenerativeModel(GEMINI_CONFIG["model"])
            self.gemini_available = True
            print("Gemini configurado correctamente")
            
        except ImportError:
            print("ADVERTENCIA: google-generativeai no esta instalado. Usando modo simulado.")
        except Exception as e:
            print(f"ADVERTENCIA: Error configurando Gemini: {e}")
    
    def predict_for_alcaldia(self, alcaldia: str) -> Dict[str, Any]:
        """
        Predice riesgo de inundacion para una alcaldia
        
        Args:
            alcaldia: Nombre de la alcaldia (ej. "Iztapalapa", "Coyoacan")
            
        Returns:
            Dict con predicciones, analisis y informacion del mapa
        """
        try:
            print(f"Analizando {alcaldia}...")
            
            # 1. Obtener datos contextuales
            contexto = self._obtener_contexto_alcaldia(alcaldia)
            if not contexto.get('datos_atlas'):
                return self._respuesta_error(f"No se encontraron datos en el atlas para: {alcaldia}")
            
            # 2. Generar analisis con Gemini o simulado
            analisis_gemini = self._analizar_con_gemini(alcaldia, contexto)
            
            # 3. Calcular probabilidades (usando tu funcion existente)
            probabilidades = self._calcular_probabilidades(contexto)
            
            # 4. Generar informacion del mapa
            mapa_info = self._generar_mapa(alcaldia, contexto, probabilidades)
            
            return self._estructurar_respuesta(alcaldia, probabilidades, mapa_info, analisis_gemini)
            
        except Exception as e:
            print(f"ERROR analizando {alcaldia}: {str(e)}")
            return self._respuesta_error(f"Error en prediccion: {str(e)}")
    
    def _obtener_contexto_alcaldia(self, alcaldia: str) -> Dict[str, Any]:
        """Obtener todos los datos relevantes para la alcaldia"""
        try:
            from db.operations import get_atlas_by_alcaldia, get_recent_clima_by_alcaldia
            
            # Datos historicos de inundaciones
            datos_atlas = get_atlas_by_alcaldia(self.db, alcaldia, exact=True)
            if not datos_atlas:
                # Intentar busqueda parcial si no hay exacta
                datos_atlas = get_atlas_by_alcaldia(self.db, alcaldia, exact=False)
            
            atlas_data = datos_atlas[0].as_dict() if datos_atlas else {}
            
            # Pronosticos de clima
            pronostico_24h = get_recent_clima_by_alcaldia(self.db, alcaldia, limit=8)
            pronostico_48h = get_recent_clima_by_alcaldia(self.db, alcaldia, limit=16)
            
            # Calcular lluvia total
            lluvia_24h = sum(p.lluvia_mm or 0 for p in pronostico_24h) if pronostico_24h else 0
            lluvia_48h = sum(p.lluvia_mm or 0 for p in pronostico_48h) if pronostico_48h else 0
            
            return {
                "datos_atlas": atlas_data,
                "pronostico_24h": [p.as_dict() for p in pronostico_24h] if pronostico_24h else [],
                "pronostico_48h": [p.as_dict() for p in pronostico_48h] if pronostico_48h else [],
                "lluvia_total_24h": lluvia_24h,
                "lluvia_total_48h": lluvia_48h,
                "registros_encontrados_24h": len(pronostico_24h),
                "registros_encontrados_48h": len(pronostico_48h)
            }
            
        except Exception as e:
            print(f"ERROR obteniendo contexto para {alcaldia}: {e}")
            return {"datos_atlas": {}}
    
    def _analizar_con_gemini(self, alcaldia: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Usar Gemini para analisis contextual"""
        
        if not self.gemini_available:
            return self._analisis_por_defecto()
        
        try:
            print(f"Consultando Gemini para {alcaldia}...")
            prompt = crear_prompt_analisis(alcaldia, contexto)
            response = self.llm.generate_content(prompt)
            
            # Intentar parsear JSON de la respuesta
            contenido = response.text.strip()
            
            # Limpiar la respuesta (remover markdown code blocks)
            if contenido.startswith("```json"):
                contenido = contenido[7:]
            if contenido.endswith("```"):
                contenido = contenido[:-3]
            contenido = contenido.strip()
            
            analisis = json.loads(contenido)
            print("Analisis de Gemini obtenido correctamente")
            return analisis
            
        except json.JSONDecodeError as e:
            print(f"ADVERTENCIA: Gemini no devolvio JSON valido: {e}")
            print(f"Respuesta recibida: {contenido}")
            return self._analisis_por_defecto()
        except Exception as e:
            print(f"ADVERTENCIA: Error con Gemini: {e}")
            return self._analisis_por_defecto()
    
    def _analisis_por_defecto(self) -> Dict[str, Any]:
        """Analisis por defecto si Gemini falla"""
        return {
            "factores_riesgo": ["intensidad_lluvia", "capacidad_drenaje", "topografia_zona"],
            "explicacion_corta": "Analisis basado en datos meteorologicos e historicos de la zona",
            "recomendaciones": [
                "Monitorear pronosticos oficiales del clima",
                "Evitar zonas bajas y cauces de rios durante lluvias intensas"
            ]
        }
    
    def _calcular_probabilidades(self, contexto: Dict) -> Dict[str, Any]:
        """Calcular probabilidades usando risk_calculator existente"""
        
        try:
            from services.risk_calculator import calculate_flood_risk
            
            # Usar tu funcion existente
            riesgo_24h = calculate_flood_risk(contexto['datos_atlas'], contexto['pronostico_24h'])
            riesgo_48h = calculate_flood_risk(contexto['datos_atlas'], contexto['pronostico_48h'])
            
            return {
                "24_horas": {
                    "nivel_riesgo": riesgo_24h,
                    "probabilidad_inundacion": RIESGO_A_PROBABILIDAD.get(riesgo_24h, 0.3),
                    "lluvia_total_mm": contexto['lluvia_total_24h'],
                    "registros_utilizados": contexto['registros_encontrados_24h']
                },
                "48_horas": {
                    "nivel_riesgo": riesgo_48h, 
                    "probabilidad_inundacion": RIESGO_A_PROBABILIDAD.get(riesgo_48h, 0.3),
                    "lluvia_total_mm": contexto['lluvia_total_48h'],
                    "registros_utilizados": contexto['registros_encontrados_48h']
                }
            }
            
        except Exception as e:
            print(f"ERROR en calculo de probabilidades: {e}")
            # Valores por defecto en caso de error
            return {
                "24_horas": {
                    "nivel_riesgo": "Error",
                    "probabilidad_inundacion": 0.0,
                    "lluvia_total_mm": 0,
                    "registros_utilizados": 0
                },
                "48_horas": {
                    "nivel_riesgo": "Error", 
                    "probabilidad_inundacion": 0.0,
                    "lluvia_total_mm": 0,
                    "registros_utilizados": 0
                }
            }
    
    def _generar_mapa(self, alcaldia: str, contexto: Dict, probabilidades: Dict) -> Dict[str, Any]:
        """Generar informacion para el mapa"""
        
        try:
            # Crear directorio de mapas si no existe
            os.makedirs(MAP_CONFIG["directorio_salida"], exist_ok=True)
            
            nombre_archivo = f"{alcaldia.lower().replace(' ', '_')}_risk.geojson"
            ruta_completa = os.path.join(MAP_CONFIG["directorio_salida"], nombre_archivo)
            
            return {
                "tipo": MAP_CONFIG["tipo"],
                "ruta_local": ruta_completa,
                "centro": MAP_CONFIG["centro_cdmx"],
                "nivel_zoom": MAP_CONFIG["zoom_default"],
                "estado": "por_generar",
                "alcaldia": alcaldia,
                "nivel_riesgo_actual": probabilidades["24_horas"]["nivel_riesgo"]
            }
            
        except Exception as e:
            print(f"ADVERTENCIA: Error generando info de mapa: {e}")
            return {
                "tipo": "geojson",
                "ruta_local": "",
                "estado": "error",
                "error": str(e)
            }
    
    def _estructurar_respuesta(self, alcaldia: str, probabilidades: Dict, 
                             mapa_info: Dict, analisis_gemini: Dict) -> Dict[str, Any]:
        """Estructurar la respuesta final en JSON"""
        
        return {
            "alcaldia": alcaldia,
            "timestamp_prediccion": datetime.now().isoformat(),
            "predicciones": probabilidades,
            "analisis_contextual": analisis_gemini,
            "mapa": mapa_info,
            "datos_utilizados": {
                "fuente_clima": "OpenWeatherMap",
                "fuente_riesgo_base": "Atlas Inundaciones CDMX",
                "modo_analisis": "gemini" if self.gemini_available else "simulado",
                "ultima_actualizacion": datetime.now().isoformat()
            },
            "estado": "completado"
        }
    
    def _respuesta_error(self, mensaje: str) -> Dict[str, Any]:
        """Estructura para respuestas de error"""
        return {
            "error": True,
            "mensaje": mensaje,
            "alcaldia": None,
            "predicciones": None,
            "mapa": None,
            "estado": "error",
            "timestamp": datetime.now().isoformat()
        }