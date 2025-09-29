# recreate_tables.py
import os
from dotenv import load_dotenv
from db.connection import engine, Base, init_db
from db.models import AtlasInundaciones, Clima
from sqlalchemy import text
import warnings

load_dotenv()

def backup_and_recreate_tables():
    """Hacer backup de datos y recrear tablas con SQLAlchemy"""
    print("INICIANDO RECREACION DE TABLAS...")
    print("=" * 50)
    
    try:
        # 1. Hacer backup de datos existentes
        print("1. Haciendo backup de datos existentes...")
        with engine.connect() as conn:
            # Backup de atlas_inundaciones
            resultado = conn.execute(text("SELECT * FROM atlas_inundaciones"))
            backup_atlas = resultado.fetchall()
            print(f"   - Backup atlas_inundaciones: {len(backup_atlas)} registros")
            
            # Backup de clima
            resultado = conn.execute(text("SELECT * FROM clima"))
            backup_clima = resultado.fetchall()
            print(f"   - Backup clima: {len(backup_clima)} registros")
        
        # 2. Eliminar tablas existentes
        print("2. Eliminando tablas existentes...")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS clima"))
            conn.execute(text("DROP TABLE IF EXISTS atlas_inundaciones"))
            conn.commit()
            print("   - Tablas eliminadas")
        
        # 3. Crear tablas usando SQLAlchemy
        print("3. Creando tablas con SQLAlchemy...")
        init_db()  # Esto crea las tablas usando los modelos
        print("   - Tablas creadas con SQLAlchemy")
        
        # 4. Restaurar datos
        print("4. Restaurando datos...")
        with engine.begin() as conn:  # begin() para transacción automática
            # Restaurar atlas_inundaciones
            if backup_atlas:
                for row in backup_atlas:
                    # Asumir el orden de columnas basado en tu CREATE TABLE
                    conn.execute(text("""
                        INSERT INTO atlas_inundaciones 
                        (cvegeo, alcaldia, riesgo, coordenadas, poligono, area_m2, perimetro_m, descripcion, fuente)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """), (
                        row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]
                    ))
                print(f"   - Restaurados {len(backup_atlas)} registros en atlas_inundaciones")
            
            # Restaurar clima
            if backup_clima:
                for row in backup_clima:
                    conn.execute(text("""
                        INSERT INTO clima 
                        (fecha, alcaldia, lluvia_mm, prob_lluvia, temperatura, humedad, presion, fuente)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """), (
                        row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]
                    ))
                print(f"   - Restaurados {len(backup_clima)} registros en clima")
        
        # 5. Verificar la nueva estructura
        print("5. Verificando nueva estructura...")
        with engine.connect() as conn:
            # Verificar atlas_inundaciones
            resultado = conn.execute(text("DESCRIBE atlas_inundaciones"))
            print("   - Estructura de atlas_inundaciones:")
            for col in resultado.fetchall():
                print(f"     * {col[0]} ({col[1]})")
            
            # Verificar clima
            resultado = conn.execute(text("DESCRIBE clima"))
            print("   - Estructura de clima:")
            for col in resultado.fetchall():
                print(f"     * {col[0]} ({col[1]})")
            
            # Contar registros
            resultado = conn.execute(text("SELECT COUNT(*) FROM atlas_inundaciones"))
            count_atlas = resultado.scalar()
            resultado = conn.execute(text("SELECT COUNT(*) FROM clima"))
            count_clima = resultado.scalar()
            print(f"   - Registros: atlas_inundaciones={count_atlas}, clima={count_clima}")
        
        print("\n✅ RECREACION COMPLETADA EXITOSAMENTE")
        
    except Exception as e:
        print(f"❌ ERROR durante la recreacion: {e}")
        import traceback
        traceback.print_exc()

def test_sqlalchemy_models():
    """Probar que los modelos SQLAlchemy funcionen correctamente"""
    print("\n🧪 PROBANDO MODELOS SQLALCHEMY...")
    print("=" * 50)
    
    try:
        from db.connection import get_db
        db = next(get_db())
        
        # Probar consulta con modelo AtlasInundaciones
        print("1. Probando modelo AtlasInundaciones...")
        resultados = db.query(AtlasInundaciones).limit(2).all()
        print(f"   ✅ Consulta exitosa: {len(resultados)} resultados")
        for r in resultados:
            print(f"     - {r.alcaldia}: {r.riesgo}")
            # Probar as_dict()
            datos = r.as_dict()
            print(f"       as_dict(): {list(datos.keys())}")
        
        # Probar consulta con modelo Clima
        print("2. Probando modelo Clima...")
        if resultados:
            alcaldia_prueba = resultados[0].alcaldia
            climas = db.query(Clima).filter(Clima.alcaldia == alcaldia_prueba).limit(2).all()
            print(f"   ✅ Consulta clima para {alcaldia_prueba}: {len(climas)} resultados")
            for c in climas:
                datos_clima = c.as_dict()
                print(f"     - {c.fecha}: {c.lluvia_mm}mm")
        
        db.close()
        print("✅ TODAS LAS PRUEBAS EXITOSAS")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    backup_and_recreate_tables()
    test_sqlalchemy_models()