# test_agent.py
import os
import sys
from dotenv import load_dotenv

# Añadir el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def probar_agente():
    """Script completo para probar el agente de inundaciones"""
    
    # Cargar variables de entorno
    load_dotenv()
    print(" Configurando entorno...")
    
    # Verificar API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print(" GOOGLE_API_KEY no encontrada en .env")
        print("   Por favor, añade: GOOGLE_API_KEY=tu_api_key_aqui")
        print("   Usando modo simulado para Gemini...")
    else:
        print(" GOOGLE_API_KEY encontrada")
    
    # Verificar conexión a base de datos
    try:
        from db.connection import get_db
        db_session = next(get_db())
        print(" Conexión a base de datos exitosa")
    except Exception as e:
        print(f" Error conectando a base de datos: {e}")
        return
    
    # Crear agente
    try:
        from agent import FloodPredictionAgent
        agente = FloodPredictionAgent(db_session)
        print(" Agente creado correctamente")
    except Exception as e:
        print(f" Error creando agente: {e}")
        return
    
    # Lista de alcaldías para probar
    alcaldias_prueba = [
        "Iztapalapa", 
        "Coyoacán", 
        "Benito Juárez",
        "Gustavo A. Madero"
    ]
    
    print(f"\n🎯 Probando con {len(alcaldias_prueba)} alcaldías...")
    print("=" * 60)
    
    resultados_totales = {
        "exitos": 0,
        "errores": 0,
        "con_gemini": 0,
        "simulados": 0
    }
    
    for alcaldia in alcaldias_prueba:
        print(f"\n  ALCALDÍA: {alcaldia}")
        print("-" * 40)
        
        try:
            # Obtener predicción
            resultado = agente.predict_for_alcaldia(alcaldia)
            
            if resultado.get("error"):
                print(f" ERROR: {resultado['mensaje']}")
                resultados_totales["errores"] += 1
                continue
            
            # Mostrar resultados exitosos
            resultados_totales["exitos"] += 1
            
            # Información de análisis
            modo_analisis = resultado['datos_utilizados']['modo_analisis']
            if modo_analisis == "gemini":
                resultados_totales["con_gemini"] += 1
            else:
                resultados_totales["simulados"] += 1
            
            print(f" Predicción exitosa ({modo_analisis})")
            
            # Predicciones 24h
            pred_24h = resultado['predicciones']['24_horas']
            print(f" 24 HORAS:")
            print(f"   • Riesgo: {pred_24h['nivel_riesgo']}")
            print(f"   • Probabilidad: {pred_24h['probabilidad_inundacion']:.0%}")
            print(f"   • Lluvia: {pred_24h['lluvia_total_mm']:.1f} mm")
            print(f"   • Registros: {pred_24h.get('registros_utilizados', 'N/A')}")
            
            # Predicciones 48h
            pred_48h = resultado['predicciones']['48_horas']
            print(f" 48 HORAS:")
            print(f"   • Riesgo: {pred_48h['nivel_riesgo']}")
            print(f"   • Probabilidad: {pred_48h['probabilidad_inundacion']:.0%}")
            print(f"   • Lluvia: {pred_48h['lluvia_total_mm']:.1f} mm")
            print(f"   • Registros: {pred_48h.get('registros_utilizados', 'N/A')}")
            
            # Análisis contextual
            analisis = resultado['analisis_contextual']
            print(f" ANÁLISIS:")
            print(f"   • Factores: {', '.join(analisis['factores_riesgo'])}")
            print(f"   • Explicación: {analisis['explicacion_corta']}")
            print(f"   • Recomendaciones: {', '.join(analisis['recomendaciones'])}")
            
            # Información del mapa
            mapa = resultado['mapa']
            print(f"🗺️  MAPA: {mapa['ruta_local']} ({mapa['estado']})")
            
        except Exception as e:
            print(f" Error inesperado con {alcaldia}: {e}")
            resultados_totales["errores"] += 1
    
    # Resumen final
    print(f"\n{'='*60}")
    print(" RESUMEN DE PRUEBAS")
    print(f"{'='*60}")
    print(f" Éxitos: {resultados_totales['exitos']}/{len(alcaldias_prueba)}")
    print(f" Errores: {resultados_totales['errores']}/{len(alcaldias_prueba)}")
    print(f" Con Gemini: {resultados_totales['con_gemini']}")
    print(f" Simulados: {resultados_totales['simulados']}")
    
    # Cerrar sesión de base de datos
    try:
        db_session.close()
        print("Sesión de BD cerrada")
    except:
        pass

def probar_una_alcaldia(alcaldia: str):
    """Probar una alcaldía específica en detalle"""
    load_dotenv()
    
    try:
        from db.connection import get_db
        from agent import FloodPredictionAgent
        
        db_session = next(get_db())
        agente = FloodPredictionAgent(db_session)
        
        print(f"\n Probando en detalle: {alcaldia}")
        print("=" * 50)
        
        resultado = agente.predict_for_alcaldia(alcaldia)
        
        # Mostrar resultado completo en JSON
        import json
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        db_session.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("INICIANDO PRUEBA DEL AGENTE DE INUNDACIONES")
    print("=" * 60)
    
    # Opciones de prueba
    import argparse
    parser = argparse.ArgumentParser(description='Probar agente de inundaciones')
    parser.add_argument('--alcaldia', type=str, help='Probar una alcaldía específica')
    
    args = parser.parse_args()
    
    if args.alcaldia:
        probar_una_alcaldia(args.alcaldia)
    else:
        probar_agente()