# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from db.connection import engine, Base
from apis import router as api_router

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Flood Prediction API",
    description="API para predicción de riesgo de inundaciones en CDMX",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # URLs de React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejo global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": True, "mensaje": "Error interno del servidor"}
    )

# Incluir rutas de la API
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "message": "Flood Prediction API",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Solo para desarrollo
        log_level="info"
    )