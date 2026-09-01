"""
Módulo de Exportación de Datos
Genera archivos Excel formateados y archivos JSON estructurados para alimentar la aplicación web en GitHub Pages.
"""
import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from app.config import EXPORTACIONES_DIR, HISTORICO_DIR, DOCS_DATA_DIR
from app.logger import logger

COLUMNAS_EXCEL = {
    "estado": "Estado",
    "departamento": "Departamento",
    "municipio": "Municipio",
    "secretaria": "Secretaría de Educación",
    "zona": "Zona",
    "cargo": "Cargo",
    "area": "Área de Conocimiento",
    "tipo_priorizacion": "Tipo de Priorización",
    "postulados": "Postulados Actuales",
    "fecha_cierre_texto": "Fecha de Cierre",
    "fecha_primera_deteccion": "Primera Detección",
    "url_portal": "Enlace Sistema Maestro",
    "id_vacante": "ID Vacante (Hash)",
}

def exportar_dataframe_a_excel(df: pd.DataFrame, ruta_archivo, nombre_hoja: str = "Vacantes"):
    """Exporta un DataFrame a un archivo Excel con formato profesional usando openpyxl."""
    if df.empty:
        df = pd.DataFrame(columns=list(COLUMNAS_EXCEL.values()))
    
    with pd.ExcelWriter(ruta_archivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=nombre_hoja)
        worksheet = writer.sheets[nombre_hoja]
        
        # Ajustar ancho de columnas automáticamente
        for col in worksheet.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

def exportar_excel(
    vacantes_actuales: List[Dict[str, Any]],
    novedades: Dict[str, Any],
    historico_completo: List[Dict[str, Any]]
):
    """Genera los archivos Excel en data/exportaciones/."""
    # 1. Vacantes Actuales
    df_act = pd.DataFrame(vacantes_actuales)
    if not df_act.empty:
        df_act = df_act.rename(columns=COLUMNAS_EXCEL)
        cols_presentes = [c for c in COLUMNAS_EXCEL.values() if c in df_act.columns]
        df_act = df_act[cols_presentes]
    ruta_act = EXPORTACIONES_DIR / "vacantes_actuales.xlsx"
    exportar_dataframe_a_excel(df_act, ruta_act, "Vacantes Activas")

    # 2. Vacantes Nuevas
    df_nuevas = pd.DataFrame(novedades.get("nuevas", []))
    if not df_nuevas.empty:
        df_nuevas = df_nuevas.rename(columns=COLUMNAS_EXCEL)
        cols_presentes = [c for c in COLUMNAS_EXCEL.values() if c in df_nuevas.columns]
        df_nuevas = df_nuevas[cols_presentes]
    ruta_nuevas = EXPORTACIONES_DIR / "vacantes_nuevas.xlsx"
    exportar_dataframe_a_excel(df_nuevas, ruta_nuevas, "Nuevas Vacantes")

    # 3. Histórico Completo
    df_hist = pd.DataFrame(historico_completo)
    if not df_hist.empty:
        df_hist = df_hist.rename(columns=COLUMNAS_EXCEL)
        cols_presentes = [c for c in COLUMNAS_EXCEL.values() if c in df_hist.columns]
        df_hist = df_hist[cols_presentes]
    ruta_hist = EXPORTACIONES_DIR / "historico_vacantes.xlsx"
    exportar_dataframe_a_excel(df_hist, ruta_hist, "Histórico Vacantes")

    logger.info(f"Archivos Excel generados exitosamente en {EXPORTACIONES_DIR}")

def exportar_json_para_web(
    vacantes_actuales: List[Dict[str, Any]],
    novedades: Dict[str, Any],
    historico_completo: List[Dict[str, Any]]
):
    """
    Genera los archivos JSON en docs/data/ para ser consumidos por GitHub Pages (dashboard web).
    """
    ahora_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Extraer métricas agregadas
    departamentos = sorted(list(set(v.get("departamento", "") for v in vacantes_actuales if v.get("departamento"))))
    municipios = sorted(list(set(v.get("municipio", "") for v in vacantes_actuales if v.get("municipio"))))
    areas = sorted(list(set(v.get("area", "") for v in vacantes_actuales if v.get("area"))))
    cargos = sorted(list(set(v.get("cargo", "") for v in vacantes_actuales if v.get("cargo"))))

    # Conteo por departamento
    conteo_deptos = {}
    for v in vacantes_actuales:
        d = v.get("departamento", "Otros")
        conteo_deptos[d] = conteo_deptos.get(d, 0) + 1

    # Conteo por área
    conteo_areas = {}
    for v in vacantes_actuales:
        a = v.get("area", "Otros")
        conteo_areas[a] = conteo_areas.get(a, 0) + 1

    stats = {
        "ultima_actualizacion": ahora_str,
        "total_activas": len(vacantes_actuales),
        "total_nuevas": len(novedades.get("nuevas", [])),
        "total_actualizadas": len(novedades.get("actualizadas", [])),
        "total_historico": len(historico_completo),
        "departamentos": departamentos,
        "municipios": municipios,
        "areas": areas,
        "cargos": cargos,
        "conteo_departamentos": conteo_deptos,
        "conteo_areas": conteo_areas,
    }

    # Escribir docs/data/stats.json
    with open(DOCS_DATA_DIR / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Escribir docs/data/vacantes_actuales.json
    with open(DOCS_DATA_DIR / "vacantes_actuales.json", "w", encoding="utf-8") as f:
        json.dump({
            "meta": stats,
            "vacantes": vacantes_actuales
        }, f, ensure_ascii=False, indent=2)

    # Escribir docs/data/novedades.json
    with open(DOCS_DATA_DIR / "novedades.json", "w", encoding="utf-8") as f:
        json.dump({
            "meta": stats,
            "novedades": novedades.get("nuevas", [])
        }, f, ensure_ascii=False, indent=2)

    # Guardar snapshot histórico con timestamp en data/historico/
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    snapshot_path = HISTORICO_DIR / f"vacantes_{timestamp}.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ahora_str,
            "total": len(vacantes_actuales),
            "vacantes": vacantes_actuales
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"JSONs exportados para GitHub Pages en {DOCS_DATA_DIR} y snapshot en {snapshot_path}")
