import requests
import pandas as pd 
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import time

from dotenv import load_dotenv
import os

# Carga las variables del archivo .env
load_dotenv('/home/diego/Documentos/clima/mi-repo/.env')

alcaldias = [ #la lista de coordenadas de las alcaldias
    ("Cuauhtémoc", 19.4333, -99.1333),
    ("Benito Juárez", 19.4008, -99.1641),
    ("Miguel Hidalgo", 19.4270, -99.1826),
    ("Coyoacán", 19.3500, -99.1625),
    ("Iztapalapa", 19.3569, -99.0721),
    ("Gustavo A. Madero", 19.4861, -99.1200),
    ("Azcapotzalco", 19.4833, -99.1703),
    ("Iztacalco", 19.3897, -99.0961),
    ("Álvaro Obregón", 19.3500, -99.2361),
    ("Cuajimalpa", 19.3556, -99.2747),
    ("La Magdalena Contreras", 19.2833, -99.2333),
    ("Tlalpan", 19.2826, -99.1406),
    ("Xochimilco", 19.2579, -99.1005),
    ("Milpa Alta", 19.0960, -99.0300),
    ("Venustiano Carranza", 19.4240, -99.1000),
    ("Tláhuac", 19.3200, -99.0020)
]

usuario  = "root"
password = "yui1810ni"
host = "localhost"
bd = "inundaciones_db"

#se crea la conexion a Mysql
engine = create_engine(os.getenv('DB_URL'))

rows_to_insert = [] #lista donde se guardan los registros del clima antes de insertarlos en la tabla
now = datetime.utcnow()
cutoff = now + timedelta(hours=24) #esto es para los pronosticos de las siguientes 24 horas, si quieren pueden modificarlo para obtener registros en intervalos de menos tiempo


#consulta a la API de openWeather por alcaldia

for alcaldia, lat, lon in alcaldias:
    #url de la api con los parametros de lat, lon y mi apikey
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={os.getenv('OPENWEATHER_API_KEY')}&units=metric&lang=es"
    
    #peticion HTTP
    r = requests.get(url)
    if r.status_code != 200:
        print(f" Error API en {alcaldia}: {r.status_code}")
        time.sleep(1) #esta mamada es pa no saturar la api por que ya me andaba cargando lo del plan gratuito, asi que esta mamada no la quiten
        continue

    data = r.json() 
    count = 0 #contador de registros por alcaldia 

    #iteracion en la lista de pronosticos

    for item in data.get('list', []):
        dt_txt = item.get('dt_txt') #fecha y hora del pronostico
        dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")

        # Solo tomar registros de las proximas 24h

        if dt <= cutoff:
            lluvia_mm = item.get('rain', {}).get('3h', 0.0) #la lluvia que se acumulo en 3h
            prob_lluvia = item.get('pop', 0) * 100 #la probabilidad de lluvia
            temp = item['main'].get('temp') #temperatura en centigrados
            humedad = item['main'].get('humidity') #humedad relativa
            presion = item['main'].get('pressure') #la presion atmosferica

            #agregamos los datos a la lista

            rows_to_insert.append({
                "fecha": dt,
                "alcaldia": alcaldia,
                "lluvia_mm": lluvia_mm,
                "prob_lluvia": prob_lluvia,
                "temperatura": temp,
                "humedad": humedad,
                "presion": presion,
                "fuente": "OpenWeatherMap"
            })

            count += 1
            if count >= 8:  # solo 24 horas (8 registros de 3h)
                break

    print(f" {alcaldia}: {count} registros preparados.")
    time.sleep(1)  # evitar saturar API

# Guardar en MySQL
df = pd.DataFrame(rows_to_insert)
if not df.empty:
    df.to_sql("clima", con=engine, if_exists="append", index=False)
    print("Datos guardados en la tabla clima.")
else:
    print("No se generaron datos para guardar.")
