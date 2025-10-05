# test_agent.py
import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Añadir el directorio raíz al path para que los imports funcionen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# La importación ahora apunta al paquete 'agent' que contiene __init__.py
from agent import FloodPredictionAgent
from db.connection import get_db

async def probar_agente_para_alcaldia(alcaldia: str):
    """Prueba el agente para una sola alcaldía y muestra el resultado."""
    db_session = next(get_db())
    try:
        agente = FloodPredictionAgent(db_session)
        print(f"--- Solicitando predicción para: {alcaldia} ---")
        
        resultado = await agente.predict_for_alcaldia(alcaldia)
        
        print(f"--- Resultado para: {alcaldia} ---")
        if resultado.get("error"):
            print(f"❌ ERROR: {resultado['mensaje']}")
            return False

        # Mostrar resultados exitosos
        fuente = resultado['datos_utilizados']['fuente_clima']
        modo = resultado['datos_utilizados']['modo_analisis']
        
        print(f"✔️ Predicción exitosa (Fuente de clima: {fuente} | Modo IA: {modo})")
        
        pred_24h = resultado['predicciones']['24_horas']
        print(f"  💧 PREDICCIÓN 24 HORAS:")
        print(f"     - Nivel de Riesgo: {pred_24h['nivel_riesgo']}")
        print(f"     - Lluvia Total Estimada: {pred_24h['lluvia_total_mm']:.1f} mm")
        
        analisis = resultado['analisis_contextual']
        print(f"  🧠 ANÁLISIS CONTEXTUAL:")
        print(f"     - Explicación: {analisis['explicacion_corta']}")
        return True

    except Exception as e:
        print(f"❌ Error inesperado con {alcaldia}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db_session.close()

async def main():
    """Función principal para ejecutar las pruebas."""
    load_dotenv()
    print("INICIANDO PRUEBA DEL AGENTE DE INUNDACIONES (MODELO HÍBRIDO)")
    print("=" * 60)

    alcaldias_prueba = [
        "Iztapalapa", 
        "Coyoacán", 
        "Benito Juárez",
        "Gustavo A. Madero"
    ]
    
    tasks = [probar_agente_para_alcaldia(alcaldia) for alcaldia in alcaldias_prueba]
    resultados = await asyncio.gather(*tasks)

    exitos = sum(1 for r in resultados if r)
    errores = len(resultados) - exitos

    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print(f"  Éxitos: {exitos}/{len(alcaldias_prueba)}")
    print(f"  Errores: {errores}/{len(alcaldias_prueba)}")
    print("=" * 60)

if __name__ == "__main__":
    # Ejecuta la función principal asíncrona
    asyncio.run(main())