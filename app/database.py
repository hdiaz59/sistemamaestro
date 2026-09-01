"""
Módulo de Base de Datos
Gestiona el almacenamiento histórico y transaccional con SQLAlchemy y SQLite.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL
from app.logger import logger

Base = declarative_base()

def obtener_ahora():
    return datetime.now()

class Vacante(Base):
    """Modelo de datos para una vacante del Sistema Maestro."""
    __tablename__ = "vacantes"

    id_vacante = Column(String(64), primary_key=True, index=True)
    cargo = Column(String(255), nullable=False)
    area = Column(String(255), nullable=False)
    secretaria = Column(String(255), nullable=False)
    departamento = Column(String(100), nullable=False, index=True)
    municipio = Column(String(100), nullable=False, index=True)
    zona = Column(String(100), nullable=True)
    tipo_priorizacion = Column(String(255), nullable=True)
    postulados = Column(Integer, default=0)
    fecha_cierre_texto = Column(String(100), nullable=True)
    fecha_cierre_iso = Column(String(50), nullable=True)
    url_portal = Column(String(500), nullable=True)
    estado = Column(String(50), default="NUEVA", index=True)  # NUEVA, ACTIVA, ACTUALIZADA, CERRADA
    activa = Column(Boolean, default=True, index=True)
    fecha_primera_deteccion = Column(DateTime, default=obtener_ahora)
    fecha_ultima_consulta = Column(DateTime, default=obtener_ahora)
    veces_detectada = Column(Integer, default=1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_vacante": self.id_vacante,
            "cargo": self.cargo,
            "area": self.area,
            "secretaria": self.secretaria,
            "departamento": self.departamento,
            "municipio": self.municipio,
            "zona": self.zona,
            "tipo_priorizacion": self.tipo_priorizacion,
            "postulados": self.postulados,
            "fecha_cierre_texto": self.fecha_cierre_texto,
            "fecha_cierre_iso": self.fecha_cierre_iso,
            "url_portal": self.url_portal,
            "estado": self.estado,
            "activa": self.activa,
            "fecha_primera_deteccion": self.fecha_primera_deteccion.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_primera_deteccion else None,
            "fecha_ultima_consulta": self.fecha_ultima_consulta.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_ultima_consulta else None,
            "veces_detectada": self.veces_detectada,
        }

class HistorialConsulta(Base):
    """Registro histórico de cada ejecución de consulta."""
    __tablename__ = "historial_consultas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_consulta = Column(DateTime, default=obtener_ahora)
    total_vacantes_detectadas = Column(Integer, default=0)
    total_nuevas = Column(Integer, default=0)
    total_actualizadas = Column(Integer, default=0)
    total_cerradas = Column(Integer, default=0)
    duracion_segundos = Column(Float, default=0.0)
    estado = Column(String(50), default="EXITOSO")
    detalles_json = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "fecha_consulta": self.fecha_consulta.strftime("%Y-%m-%d %H:%M:%S") if self.fecha_consulta else None,
            "total_vacantes_detectadas": self.total_vacantes_detectadas,
            "total_nuevas": self.total_nuevas,
            "total_actualizadas": self.total_actualizadas,
            "total_cerradas": self.total_cerradas,
            "duracion_segundos": self.duracion_segundos,
            "estado": self.estado,
            "detalles": json.loads(self.detalles_json) if self.detalles_json else None
        }

# Crear motor y fábrica de sesiones
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada correctamente.")

def obtener_vacantes_historicas_db() -> Dict[str, Vacante]:
    """Retorna un diccionario de todas las vacantes indexadas por id_vacante."""
    db = SessionLocal()
    try:
        registros = db.query(Vacante).all()
        return {r.id_vacante: r for r in registros}
    finally:
        db.close()

def guardar_resultado_consulta(
    vacantes_actuales: List[Dict[str, Any]],
    novedades: Dict[str, Any],
    duracion_segundos: float = 0.0,
    estado_ejecucion: str = "EXITOSO"
):
    """
    Persiste en la base de datos las vacantes actuales, actualiza estados y registra el log de consulta.
    """
    db = SessionLocal()
    ahora = datetime.now()
    try:
        # 1. Obtener registros existentes
        existentes = {v.id_vacante: v for v in db.query(Vacante).all()}
        ids_actuales = set()

        for v_data in vacantes_actuales:
            v_id = v_data["id_vacante"]
            ids_actuales.add(v_id)

            if v_id in existentes:
                v_obj = existentes[v_id]
                # Si cambió postulados u otro dato, se marca ACTUALIZADA, sino ACTIVA
                if v_obj.postulados != v_data.get("postulados", 0):
                    v_obj.postulados = v_data.get("postulados", 0)
                    v_obj.estado = "ACTUALIZADA"
                else:
                    v_obj.estado = "ACTIVA"
                v_obj.activa = True
                v_obj.fecha_ultima_consulta = ahora
                v_obj.veces_detectada += 1
            else:
                # Nueva vacante
                v_obj = Vacante(
                    id_vacante=v_id,
                    cargo=v_data.get("cargo", ""),
                    area=v_data.get("area", ""),
                    secretaria=v_data.get("secretaria", ""),
                    departamento=v_data.get("departamento", ""),
                    municipio=v_data.get("municipio", ""),
                    zona=v_data.get("zona", ""),
                    tipo_priorizacion=v_data.get("tipo_priorizacion", ""),
                    postulados=v_data.get("postulados", 0),
                    fecha_cierre_texto=v_data.get("fecha_cierre_texto", ""),
                    fecha_cierre_iso=v_data.get("fecha_cierre_iso"),
                    url_portal=v_data.get("url_portal", ""),
                    estado="NUEVA",
                    activa=True,
                    fecha_primera_deteccion=ahora,
                    fecha_ultima_consulta=ahora,
                    veces_detectada=1,
                )
                db.add(v_obj)

        # Marcar como CERRADA las vacantes que estaban activas y ya no aparecieron
        for v_id, v_obj in existentes.items():
            if v_id not in ids_actuales and v_obj.activa:
                v_obj.activa = False
                v_obj.estado = "CERRADA"
                v_obj.fecha_ultima_consulta = ahora

        # 2. Registrar en historial_consultas
        consulta_log = HistorialConsulta(
            fecha_consulta=ahora,
            total_vacantes_detectadas=len(vacantes_actuales),
            total_nuevas=len(novedades.get("nuevas", [])),
            total_actualizadas=len(novedades.get("actualizadas", [])),
            total_cerradas=len(novedades.get("cerradas", [])),
            duracion_segundos=duracion_segundos,
            estado=estado_ejecucion,
            detalles_json=json.dumps({
                "total_actuales": len(vacantes_actuales),
                "nuevas_ids": [n["id_vacante"] for n in novedades.get("nuevas", [])],
            })
        )
        db.add(consulta_log)

        db.commit()
        logger.info("Datos persistidos en SQLite satisfactoriamente.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar en base de datos: {e}")
        raise
    finally:
        db.close()

def obtener_todas_las_vacantes_db() -> List[Dict[str, Any]]:
    """Retorna todas las vacantes en la base de datos en formato diccionario."""
    db = SessionLocal()
    try:
        vacs = db.query(Vacante).all()
        return [v.to_dict() for v in vacs]
    finally:
        db.close()
