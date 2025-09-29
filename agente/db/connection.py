import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_URL = os.getenv("DB_URL")

# engine y Session (síncrono)
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

# Base declarativa para modelos
Base = declarative_base()

def init_db():
    """
    Crear tablas (llamar una vez al inicializar el proyecto o desde un script).
    Importa los modelos para que se registren en la metadata.
    """
    # Importar modelos aquí para registrar metadata (evita import circular)
    import db.models
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Generador para usar como dependencia en FastAPI o para uso manual.
    Uso:
        db = next(get_db())
        ... usar db ...
    ó en FastAPI:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()