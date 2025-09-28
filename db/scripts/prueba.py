import requests

API_KEY = "3f51a8775f0dc3ff50ebb05306b266e4"

# Coordenadas correctas de CDMX
lat = 19.4326
lon = -99.1332

# Endpoint de OpenWeather
url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("Conexión exitosa")
    print("Ciudad:", data["city"]["name"])
    print("Primer registro de pronóstico:")
    print(data["list"][0])  # imprime solo el primer bloque
else:
    print(" Error en la conexión:", response.status_code, response.text)
