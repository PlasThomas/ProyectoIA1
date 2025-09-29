# init_database.py
import os
import json
from dotenv import load_dotenv
from db.connection import init_db, engine
from db.models import AtlasInundaciones, Clima
from sqlalchemy import text

load_dotenv()

def verificar_y_inicializar_bd():
    """Verificar e inicializar la base de datos"""
    print("VERIFICANDO E INICIALIZANDO BASE DE DATOS...")
    print("=" * 50)
    
    try:
        # 1. Verificar conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexión a BD exitosa")
        
        # 2. Verificar si las tablas existen
        tabla_atlas = AtlasInundaciones.__tablename__
        tabla_clima = Clima.__tablename__
        
        with engine.connect() as conn:
            # Verificar tabla atlas_inundaciones
            resultado = conn.execute(text(f"SHOW TABLES LIKE '{tabla_atlas}'"))
            if resultado.fetchone():
                print(f"✅ Tabla '{tabla_atlas}' existe")
            else:
                print(f"❌ Tabla '{tabla_atlas}' NO existe")
                
            # Verificar tabla clima
            resultado = conn.execute(text(f"SHOW TABLES LIKE '{tabla_clima}'"))
            if resultado.fetchone():
                print(f"✅ Tabla '{tabla_clima}' existe")
            else:
                print(f"❌ Tabla '{tabla_clima}' NO existe")
        
        # 3. Verificar datos en las tablas
        with engine.connect() as conn:
            # Contar registros en atlas_inundaciones
            resultado = conn.execute(text(f"SELECT COUNT(*) FROM {tabla_atlas}"))
            count_atlas = resultado.scalar()
            print(f"📊 Registros en {tabla_atlas}: {count_atlas}")
            
            # Contar registros en clima
            resultado = conn.execute(text(f"SELECT COUNT(*) FROM {tabla_clima}"))
            count_clima = resultado.scalar()
            print(f"📊 Registros en {tabla_clima}: {count_clima}")
            
            # Mostrar algunas alcaldías disponibles
            resultado = conn.execute(text(f"SELECT DISTINCT alcaldi FROM {tabla_atlas} LIMIT 5"))
            alcaldias = [row[0] for row in resultado.fetchall()]
            print(f"🏙️  Alcaldías en atlas: {alcaldias}")
            
            # Mostrar algunas alcaldías en clima
            resultado = conn.execute(text(f"SELECT DISTINCT alcaldia FROM {tabla_clima} LIMIT 5"))
            alcaldias_clima = [row[0] for row in resultado.fetchall()]
            print(f"🌤️  Alcaldías en clima: {alcaldias_clima}")
        
        # 4. Verificar estructura de la tabla atlas_inundaciones
        print("\n🔍 Verificando estructura de tabla atlas_inundaciones...")
        with engine.connect() as conn:
            resultado = conn.execute(text(f"DESCRIBE {tabla_atlas}"))
            columnas = resultado.fetchall()
            print("📋 Columnas en atlas_inundaciones:")
            for col in columnas:
                print(f"   - {col[0]} ({col[1]})")
        
        # 5. Probar consulta directa para ver problema con poligono
        print("\n🔍 Probando consulta directa para detectar problema JSON...")
        with engine.connect() as conn:
            # Consultar algunos registros con poligono
            resultado = conn.execute(text(f"SELECT cvegeo, alcaldi, LENGTH(poligono) as len_poligono, LEFT(poligono, 100) as preview FROM {tabla_atlas} LIMIT 3"))
            registros = resultado.fetchall()
            for reg in registros:
                print(f"   📍 {reg[0]} - {reg[1]}")
                print(f"      Longitud poligono: {reg[2]} caracteres")
                print(f"      Preview: {reg[3]}...")
                
                # Intentar parsear JSON
                try:
                    poligono_completo = conn.execute(text(f"SELECT poligono FROM {tabla_atlas} WHERE cvegeo = :cvegeo"), 
                                                   {"cvegeo": reg[0]}).scalar()
                    json_data = json.loads(poligono_completo)
                    print(f"      ✅ JSON válido")
                except json.JSONDecodeError as e:
                    print(f"      ❌ JSON inválido: {e}")
                except Exception as e:
                    print(f"      ⚠️  Error: {e}")
        
        # 6. Intentar usar los modelos SQLAlchemy con manejo de errores
        print("\n🔍 Probando modelos SQLAlchemy...")
        from db.connection import get_db
        db = next(get_db())
        
        try:
            # Probar consulta simple SIN poligono primero
            print("Probando consulta sin poligono...")
            resultados = db.query(AtlasInundaciones.cvegeo, AtlasInundaciones.alcaldi, AtlasInundaciones.riesgo).limit(2).all()
            print(f"✅ Consulta básica exitosa: {len(resultados)} resultados")
            for r in resultados:
                print(f"   - {r.alcaldi}: {r.riesgo}")
                
        except Exception as e:
            print(f"❌ Error en consulta básica: {e}")
        
        try:
            # Probar consulta CON poligono pero manejando el error
            print("Probando consulta con poligono...")
            resultados = db.query(AtlasInundaciones).limit(2).all()
            print(f"✅ Consulta completa exitosa: {len(resultados)} resultados")
            for r in resultados:
                print(f"   - {r.alcaldi}: {r.riesgo}")
                # Intentar acceder al poligono con manejo de errores
                try:
                    if r.poligono:
                        if isinstance(r.poligono, str):
                            poligono_data = json.loads(r.poligono)
                            print(f"     ✅ Poligono JSON válido")
                        else:
                            print(f"     ℹ️  Poligono no es string: {type(r.poligono)}")
                except json.JSONDecodeError:
                    print(f"     ❌ Poligono JSON inválido")
                except Exception as e:
                    print(f"     ⚠️  Error con poligono: {e}")
                    
        except Exception as e:
            print(f"❌ Error en consulta completa: {e}")
            
        db.close()
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    verificar_y_inicializar_bd()