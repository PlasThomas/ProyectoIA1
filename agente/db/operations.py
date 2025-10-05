from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .models import AtlasInundaciones, Clima
import json
from datetime import datetime

# ---------------------------
# Atlas (polígonos / zonas)
# ---------------------------

def get_atlas_by_id(db: Session, record_id: int) -> Optional[AtlasInundaciones]:
    """Obtener un registro del atlas por id."""
    return db.get(AtlasInundaciones, record_id)


def list_atlas(db: Session, limit: int = 100, offset: int = 0) -> List[AtlasInundaciones]:
    """Listar registros del atlas (paginado)."""
    stmt = select(AtlasInundaciones).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


def get_atlas_by_cvegeo(db: Session, cvegeo: str) -> List[AtlasInundaciones]:
    """Buscar por clave geográfica exacta."""
    stmt = select(AtlasInundaciones).where(AtlasInundaciones.cvegeo == cvegeo)
    return db.execute(stmt).scalars().all()


def get_atlas_by_alcaldia(db: Session, alcaldia: str, exact: bool = False) -> List[AtlasInundaciones]:
    """
    Buscar por alcaldía. Si exact=True hace coincidencia exacta (case-insensitive),
    si exact=False usa LIKE (%alcaldia%).
    """
    if exact:
        stmt = select(AtlasInundaciones).where(func.lower(AtlasInundaciones.alcaldia) == alcaldia.lower())
    else:
        stmt = select(AtlasInundaciones).where(AtlasInundaciones.alcaldia.like(f"%{alcaldia}%"))
    return db.execute(stmt).scalars().all()


def create_atlas(db: Session, *, cvegeo: Optional[str] = None, alcaldia: Optional[str] = None,
                 riesgo: Optional[str] = None, coordenadas: Optional[str] = None,
                 poligono: Optional[Dict] = None, area_m2: Optional[float] = None,
                 perimetro_m: Optional[float] = None, descripcion: Optional[str] = None,
                 fuente: Optional[str] = None) -> AtlasInundaciones:
    """Insertar un nuevo registro en atlas_inundaciones."""
    obj = AtlasInundaciones(
        cvegeo=cvegeo,
        alcaldia=alcaldia,
        riesgo=riesgo,
        coordenadas=coordenadas,
        poligono=poligono,
        area_m2=area_m2,
        perimetro_m=perimetro_m,
        descripcion=descripcion,
        fuente=fuente,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_atlas(db: Session, record_id: int, **fields) -> Optional[AtlasInundaciones]:
    """Actualizar campos del atlas (pasar kwargs con las columnas que desees actualizar)."""
    obj = db.get(AtlasInundaciones, record_id)
    if not obj:
        return None
    for k, v in fields.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def atlas_to_geojson_featurecollection(db: Session) -> Dict[str, Any]:
    """
    Devuelve FeatureCollection GeoJSON con poligonos y propiedades mínimas.
    Ideal para alimentar Folium/GeoJSON en front.
    """
    rows = db.execute(select(AtlasInundaciones)).scalars().all()
    features = []
    for r in rows:
        geom = r.poligono
        # si poligono está guardado como string JSON, convertirlo
        if isinstance(geom, str):
            try:
                geom = json.loads(geom)
            except Exception:
                geom = None
        feature = {
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": r.id,
                "cvegeo": r.cvegeo,
                "alcaldia": r.alcaldia,
                "riesgo": r.riesgo,
                "area_m2": float(r.area_m2) if r.area_m2 is not None else None,
                "perimetro_m": float(r.perimetro_m) if r.perimetro_m is not None else None,
                "descripcion": r.descripcion,
                "fuente": r.fuente,
            }
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


# ---------------------------
# Clima (historico / pronosticos)
# ---------------------------

def insert_clima_record(db: Session, *, fecha: datetime, alcaldia: str,
                        lluvia_mm: Optional[float] = None, prob_lluvia: Optional[float] = None,
                        temperatura: Optional[float] = None, humedad: Optional[float] = None,
                        presion: Optional[float] = None, fuente: Optional[str] = None) -> Clima:
    """
    Insertar un registro en la tabla clima.
    """
    obj = Clima(
        fecha=fecha,
        alcaldia=alcaldia,
        lluvia_mm=lluvia_mm,
        prob_lluvia=prob_lluvia,
        temperatura=temperatura,
        humedad=humedad,
        presion=presion,
        fuente=fuente,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def bulk_insert_clima(db: Session, records: List[Dict[str, Any]]) -> int:
    """
    Insertar lista de registros (cada registro es un dict con llaves compatibles).
    Retorna número de registros insertados.
    """
    objs = [Clima(**r) for r in records]
    db.add_all(objs)
    db.commit()
    return len(objs)


def get_recent_clima_by_alcaldia(db: Session, alcaldia: str, limit: int = 24) -> List[Clima]:
    """Obtener últimos `limit` registros de clima para una alcaldía."""
    stmt = select(Clima).where(Clima.alcaldia == alcaldia).order_by(Clima.fecha.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def get_clima_by_date_range(db: Session, alcaldia: str, start: datetime, end: datetime) -> List[Clima]:
    """Obtener registros de clima entre dos fechas (inclusive)."""
    stmt = select(Clima).where(
        Clima.alcaldia == alcaldia,
        Clima.fecha >= start,
        Clima.fecha <= end
    ).order_by(Clima.fecha)
    return db.execute(stmt).scalars().all()


def get_monthly_rainfall_sum(db: Session, alcaldia: str, year: int, month: int) -> float:
    """
    Suma de lluvia (lluvia_mm) para una alcaldía en mes/año dados.
    (Usa func.extract; para MySQL funciona mediante YEAR/MONTH)
    """
    stmt = select(func.sum(Clima.lluvia_mm)).where(
        Clima.alcaldia == alcaldia,
        func.extract('year', Clima.fecha) == year,
        func.extract('month', Clima.fecha) == month
    )
    res = db.execute(stmt).scalar_one_or_none()
    return float(res) if res is not None else 0.0

def get_all_alcaldias(db: Session) -> List[str]:
    """Obtiene todas las alcaldías únicas de la base de datos"""
    try:
        from .models import AtlasInundaciones  # Import local para evitar circular imports
        result = db.query(AtlasInundaciones.alcaldia).distinct().all()
        return [row[0] for row in result if row[0]]  # Filtra valores None
    except Exception as e:
        print(f"Error obteniendo alcaldías: {e}")
        return []