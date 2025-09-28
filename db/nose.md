a ver esta mamada queda asi: 

-- en la carpeta scripts estan los codigos en python y el script sql para crear la BD, solo tiene 2 tablas weones, que recopilar datos pa estas mamadas estuvo bien culero, primero creen la BD que tiene lo siguiente:
la tabla atlas_inundaciones que tiene:
id → Identificador único de cada registro (clave primaria).

cvegeo → Clave geográfica del área (referencia oficial del INEGI / CDMX).

alcaldia → Nombre de la alcaldía donde se encuentra el polígono de riesgo.

riesgo → Nivel de riesgo de inundación (ejemplo: Alto, Medio, Bajo).

coordenadas → Coordenadas principales en formato texto (para consulta rápida).

poligono (JSON) → Representación del polígono en formato GeoJSON (para mapas/animaciones).

area_m2 → Superficie del polígono en metros cuadrados.

perimetro_m → Longitud del perímetro en metros.

descripcion → Texto descriptivo adicional (ejemplo: "Zona con alta probabilidad por cercanía al río X").

fuente → Fuente de los datos (ejemplo: Atlas de Riesgo de Inundaciones - CDMX).

LA OTRA TABLA ES LA DE CLIMA QUE TIENE: 
id → Identificador único del registro (clave primaria).

fecha → Fecha y hora del pronóstico (ejemplo: 2025-09-28 12:00:00).

alcaldia → Nombre de la alcaldía a la que corresponde el pronóstico.

lluvia_mm → Cantidad de lluvia acumulada en milímetros para ese intervalo de 3h.

prob_lluvia → Probabilidad de lluvia en porcentaje (%).

temperatura → Temperatura del aire en grados Celsius.

humedad → Humedad relativa en %.

presion → Presión atmosférica en hPa (hectopascales).

fuente → Fuente de los datos (en este caso: OpenWeatherMap).

------------------------------------------------------------------------------

-- la carpeta data contiene el csv que obtuve la pagina de gobierno, en ella vienen los datos para almacenar del riesgo de inundacion, ya hice el filtro en los scripts de python de que tomar, no hay falla en eso.

------------------------------------------------------------------------------
literal son solo 2 scripts de python, el de cargar_csv va a llenar la tabla de atlas, la de cargar clima toma los datos de probabilidad de clima de la api, en los 2 tiene comentarios donde medio explique que hace cada mamada por si quieren saber que pedo, nomas ajustan las rutas para el de cargar_csv, a donde esta el data, no hay pierder.

Tambien ya puse la lista de las chingaderas que hay que instalar en python, estan en el requirements.txt

P.D, el que dice prueba.py es pa calar la conexion con la api, luego se medio apendeja la api, ahi me avisan si no jala.
