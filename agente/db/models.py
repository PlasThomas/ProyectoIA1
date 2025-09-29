from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, JSON
from .connection import Base
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

class AtlasInundaciones(Base):
    __tablename__ = "atlas_inundaciones"

    id = Column(Integer, primary_key=True, index=True)
    cvegeo = Column(String(20), nullable=True, index=True)
    alcaldia = Column(String(100), nullable=True, index=True)
    riesgo = Column(String(50), nullable=True, index=True)
    coordenadas = Column(String(100), nullable=True)
    poligono = Column(JSON, nullable=True)           # GeoJSON almacenado como JSON
    area_m2 = Column(Numeric(15, 2), nullable=True)
    perimetro_m = Column(Numeric(15, 2), nullable=True)
    descripcion = Column(Text, nullable=True)
    fuente = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<AtlasInundaciones(id={self.id}, alcaldia={self.alcaldia}, riesgo={self.riesgo})>"

    def as_dict(self) -> Dict[str, Any]:
        """Retorna representacion dict (convierte Decimals a floats)."""
        return {
            "id": self.id,
            "cvegeo": self.cvegeo,
            "alcaldia": self.alcaldia,
            "riesgo": self.riesgo,
            "coordenadas": self.coordenadas,
            "poligono": self.poligono,
            "area_m2": float(self.area_m2) if self.area_m2 is not None else None,
            "perimetro_m": float(self.perimetro_m) if self.perimetro_m is not None else None,
            "descripcion": self.descripcion,
            "fuente": self.fuente,
        }


class Clima(Base):
    __tablename__ = "clima"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False, index=True)   # datetime del pronóstico/registro
    alcaldia = Column(String(100), nullable=False, index=True)
    lluvia_mm = Column(Numeric(5, 2), nullable=True)
    prob_lluvia = Column(Numeric(5, 2), nullable=True)    # porcentaje 0..100
    temperatura = Column(Numeric(5, 2), nullable=True)
    humedad = Column(Numeric(5, 2), nullable=True)
    presion = Column(Numeric(7, 2), nullable=True)
    fuente = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<Clima(id={self.id}, fecha={self.fecha}, alcaldia={self.alcaldia})>"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "fecha": self.fecha.isoformat() if isinstance(self.fecha, datetime) else self.fecha,
            "alcaldia": self.alcaldia,
            "lluvia_mm": float(self.lluvia_mm) if self.lluvia_mm is not None else None,
            "prob_lluvia": float(self.prob_lluvia) if self.prob_lluvia is not None else None,
            "temperatura": float(self.temperatura) if self.temperatura is not None else None,
            "humedad": float(self.humedad) if self.humedad is not None else None,
            "presion": float(self.presion) if self.presion is not None else None,
            "fuente": self.fuente,
        }
