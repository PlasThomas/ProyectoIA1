import pandas as pd 
from sqlalchemy import create_engine #Para la conexion en la base de datos

from dotenv import load_dotenv
import os

# Carga las variables del archivo .env
load_dotenv('/home/thomas/Documentos/Escuela/Noveno_semestre/IA/ProyectoIA1/.env')

csv_path = "/home/thomas/Documentos/Escuela/Noveno_semestre/IA/ProyectoIA1/db/data/data_geo_limpia.csv" #aqui es importante que modifiquen la ruta a donde este el csv

#Creacion del motor de conexion con SQLAlchemy
#usamos Mysql con el driver PyMySql
engine = create_engine(os.getenv('DB_URL'))

#Extraemos los datos

df = pd.read_csv(csv_path) #Se cargan los datos desde el archivo CSV 

df["coordenadas"] = df["g_pnt_2"]      # g_pnt_2  coordenadas (puntos geoespaciales)
df["poligono"] = df["geo_shp"]         # geo_shp poligono (formas poligonales)
df["riesgo"] = df["intnsdd"]           # intnsdd  riesgo (intensidad/nivel de riesgo)
df["descripcion"] = df["descrpc"]      # descrpc  descripcion (descripción del área)
df["perimetro_m"] = df["perim_m"]      # perim_m perimetro_m (perímetro en metros)


#Crear el dataframe solo con las columnas que ocupamos por que trae otras mamadas

df_final = df[[
    "cvegeo",           # Clave geográfica única del área
    "alcaldi",          # Alcaldía a la que pertenece el área
    "riesgo",           # Nivel de riesgo de inundación
    "coordenadas",      # Coordenadas geográficas del punto
    "poligono",         # Polígono que define el área de riesgo
    "area_m2",          # Área en metros cuadrados
    "perimetro_m",      # Perímetro en metros
    "descripcion",      # Descripción detallada del área
    "fuente"            # Fuente de los datos
]]

# Renombrar 'alcaldi' a 'alcaldia' para que coincida exactamente con tu tabla
df_final = df_final.rename(columns={'alcaldi': 'alcaldia'})

 #Se cargan los datos da la BD
df_final.to_sql("atlas_inundaciones", con=engine, if_exists="append", index=False)

#esto confirma si se realizo la ejecucion del programa
print("Datos cargados en MySQL con éxito")