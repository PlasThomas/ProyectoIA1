# apis/routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import asyncio

from db.connection import get_db
from agent import FloodPredictionAgent

router = APIRouter(prefix="/api/v1", tags=["flood-prediction"])

# Cache simple para evitar crear múltiples instancias del agente
_agent_cache = {}

def get_flood_agent(db: Session = Depends(get_db)) -> FloodPredictionAgent:
    """Dependency injection para el agente de inundaciones"""
    if db not in _agent_cache:
        _agent_cache[db] = FloodPredictionAgent(db)
    return _agent_cache[db]

@router.get("/health")
async def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return {
        "status": "healthy",
        "service": "Flood Prediction API",
        "timestamp": "2024-01-01T00:00:00Z"  # Usar datetime en producción
    }

@router.get("/alcaldias")
async def get_alcaldias(db: Session = Depends(get_db)):
    """Obtiene la lista de alcaldías disponibles en la base de datos"""
    try:
        from db.operations import get_all_alcaldias
        alcaldias = get_all_alcaldias(db)
        return {
            "alcaldias": alcaldias,
            "total": len(alcaldias)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo alcaldías: {str(e)}")

@router.get("/predict/{alcaldia}")
async def predict_flood_risk(alcaldia: str, agent: FloodPredictionAgent = Depends(get_flood_agent)):
    """Obtiene la predicción de riesgo de inundación para una alcaldía específica"""
    try:
        if not alcaldia or not alcaldia.strip():
            raise HTTPException(status_code=400, detail="El nombre de la alcaldía no puede estar vacío")
        
        print(f"🔍 Solicitando predicción para: {alcaldia}")
        resultado = await agent.predict_for_alcaldia(alcaldia.strip())
        
        if resultado.get("error"):
            raise HTTPException(status_code=404, detail=resultado["mensaje"])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en predicción para {alcaldia}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/predict/batch")
async def predict_batch_flood_risk(
    alcaldias: List[str], 
    agent: FloodPredictionAgent = Depends(get_flood_agent)
):
    """Obtiene predicciones para múltiples alcaldías en lote"""
    try:
        if not alcaldias:
            raise HTTPException(status_code=400, detail="La lista de alcaldías no puede estar vacía")
        
        resultados = []
        for alcaldia in alcaldias:
            if alcaldia.strip():
                try:
                    resultado = await agent.predict_for_alcaldia(alcaldia.strip())
                    resultados.append(resultado)
                except Exception as e:
                    resultados.append({
                        "alcaldia": alcaldia,
                        "error": True,
                        "mensaje": f"Error procesando esta alcaldía: {str(e)}"
                    })
                # Pequeña pausa para no saturar las APIs externas
                await asyncio.sleep(0.1)
        
        return {
            "resultados": resultados,
            "total_procesadas": len(resultados),
            "exitosas": len([r for r in resultados if not r.get("error")])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando lote: {str(e)}")

@router.get("/alcaldia/{alcaldia}/context")
async def get_alcaldia_context(
    alcaldia: str, 
    agent: FloodPredictionAgent = Depends(get_flood_agent)
):
    """Obtiene solo el contexto de datos para una alcaldía (sin análisis de IA)"""
    try:
        contexto = await agent._obtener_contexto_hibrido(alcaldia.strip())
        
        if not contexto.get('datos_atlas'):
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para: {alcaldia}")
        
        return {
            "alcaldia": alcaldia,
            "datos_atlas": contexto.get('datos_atlas', {}),
            "datos_clima": {
                "pronostico_24h": contexto.get('pronostico_24h', []),
                "lluvia_total_24h": contexto.get('lluvia_total_24h', 0),
                "fuente": contexto.get('fuente_clima', 'Desconocida')
            },
            "timestamp": "2024-01-01T00:00:00Z"  # Usar datetime en producción
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo contexto: {str(e)}")