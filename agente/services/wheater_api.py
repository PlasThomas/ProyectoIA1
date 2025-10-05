import os
import httpx
import asyncio
from datetime import datetime
from typing import Dict, Optional, List, Any

# Hacemos una importación relativa para acceder a los módulos de la base de datos
# Asume que este archivo está en app/services/ y los otros en app/db/
from db.connection import get_db
from db.operations import bulk_insert_clima
from dotenv import load_dotenv

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
class GeocodingService:
    """Servicio para geocodificación de ubicaciones en CDMX usando Nominatim."""
    
    def __init__(self):
        """Corrección: El método constructor es __init__."""
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
    
    async def geocode_cdmx_location(self, alcaldia: str) -> Optional[Dict]:
        """Geocodifica una alcaldía específica de CDMX para obtener latitud y longitud."""
        print(f"Geocodificando: {alcaldia}...")

        headers = {
            'User-Agent': 'FloodPredictionAgent/1.0 (yannigalvan02@aragon.unam.mx)'
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.nominatim_url,
                    params={
                        "q": f"{alcaldia}, Ciudad de México, México",
                        "format": "json",
                        "limit": 1,
                        "addressdetails": 1
                    },
                    headers=headers  # <-- Se añade el encabezado aquí
                )
                response.raise_for_status()
                
                if response.json():
                    data = response.json()[0]
                    return {"lat": float(data["lat"]), "lon": float(data["lon"])}
                
                return None
        except Exception as e:
            print(f"Error en geocodificación para {alcaldia}: {e}")
            return None

class WeatherService:
    """Servicio para obtener datos de pronóstico de OpenWeatherMap."""
    
    def __init__(self):
        """Corrección: El método constructor es __init__."""
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.openweather_api_key:
            raise ValueError("La variable de entorno OPENWEATHER_API_KEY no está definida.")
        self.weather_api_base = "https://api.openweathermap.org/data/2.5"
    
    async def get_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """Obtiene el pronóstico de 5 días / 3 horas."""
        print(f"Obteniendo pronóstico para Lat={lat}, Lon={lon}...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.weather_api_base}/forecast",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.openweather_api_key,
                        "units": "metric",
                        "lang": "es"
                    }
                )
                response.raise_for_status()
                print("Pronóstico obtenido con éxito.")
                return response.json()
        except Exception as e:
            print(f"Error obteniendo pronóstico: {e}")
            return None

# --- Lógica de Orquestación y Guardado en Base de Datos ---

def transform_forecast_to_db_records(forecast_data: Dict, alcaldia: str) -> List[Dict[str, Any]]:
    """Transforma la respuesta de la API en una lista de registros para la tabla Clima."""
    records_to_insert = []
    # Procesamos solo las próximas 8 lecturas (24 horas)
    for forecast in forecast_data.get('list', [])[:8]:
        records_to_insert.append({
            "fecha": datetime.fromtimestamp(forecast['dt']),
            "alcaldia": alcaldia,
            # El valor '3h' es el volumen de los últimos 3h. No se necesita dividir.
            "lluvia_mm": forecast.get('rain', {}).get('3h', 0.0),
            # 'pop' es la probabilidad de precipitación (0 a 1), se multiplica por 100.
            "prob_lluvia": forecast.get('pop', 0.0) * 100,
            "temperatura": forecast['main']['temp'],
            "humedad": forecast['main']['humidity'],
            "presion": forecast['main']['pressure'],
            "fuente": "OpenWeatherMap"
        })
    return records_to_insert

async def fetch_and_store_forecast_for_alcaldia(geocoder: GeocodingService, weather: WeatherService, alcaldia: str):
    """Orquesta el proceso completo para una alcaldía: geocodificar, obtener pronóstico y guardar."""
    coords = await geocoder.geocode_cdmx_location(alcaldia)
    if not coords:
        return

    forecast_data = await weather.get_forecast(coords['lat'], coords['lon'])
    if not forecast_data:
        return

    records = transform_forecast_to_db_records(forecast_data, alcaldia)
    
    if not records:
        print(f"No se generaron registros para {alcaldia}.")
        return

    # Usamos el generador get_db para obtener una sesión de la base de datos
    db_session = next(get_db())
    try:
        count = bulk_insert_clima(db_session, records)
        print(f"Se insertaron {count} registros de pronóstico para {alcaldia} en la base de datos.")
    finally:
        db_session.close()

# --- Punto de Entrada para Ejecutar como Script ---

async def main():
    """Función principal para ejecutar el proceso para todas las alcaldías de interés."""
    # Lista de alcaldías que quieres monitorear
    alcaldias_cdmx = [
        "Álvaro Obregón", "Azcapotzalco", "Benito Juárez", "Coyoacán", 
        "Cuajimalpa de Morelos", "Cuauhtémoc", "Gustavo A. Madero", "Iztacalco",
        "Iztapalapa", "La Magdalena Contreras", "Miguel Hidalgo", "Milpa Alta",
        "Tláhuac", "Tlalpan", "Venustiano Carranza", "Xochimilco"
    ]
    
    geocoder = GeocodingService()
    weather = WeatherService()
    
    # Creamos una tarea para cada alcaldía para ejecutarlas en paralelo
    tasks = [fetch_and_store_forecast_for_alcaldia(geocoder, weather, nombre) for nombre in alcaldias_cdmx]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("Iniciando la actualización de datos de pronóstico del clima...")
    # Carga las variables de entorno desde el archivo .env
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
    print("Proceso de actualización finalizado.")