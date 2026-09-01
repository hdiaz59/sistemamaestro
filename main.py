"""
Monitor de Vacantes - Sistema Maestro del Ministerio de Educación Nacional de Colombia
Punto de entrada principal para ejecución CLI y automatización.
"""
import sys
import time
from datetime import datetime
from app.config import SISTEMA_MAESTRO_URL
from app.logger import logger
from app.database import (
    init_db,
    obtener_vacantes_historicas_db,
    guardar_resultado_consulta,
    obtener_todas_las_vacantes_db
)
from app.scraper import SistemaMaestroScraper
from app.detector import detectar_novedades
from app.exporter import exportar_excel, exportar_json_para_web
from app.notifier import despachar_notificaciones

def ejecutar_monitor():
    """Ejecuta el ciclo completo del monitor de vacantes."""
    logger.info("=" * 65)
    logger.info("🚀 INICIANDO MONITOR DE VACANTES - SISTEMA MAESTRO MEN")
    logger.info("=" * 65)
    
    inicio_tiempo = time.time()
    
    # 1. Inicializar Base de Datos
    init_db()
    historicas = obtener_vacantes_historicas_db()
    logger.info(f"Histórico previo en base de datos: {len(historicas)} vacantes registradas.")

    # 2. Consultar portal oficial (Búsqueda general)
    scraper = SistemaMaestroScraper()
    try:
        vacantes_actuales = scraper.consultar()
    except Exception as e:
        logger.error(f"Fallo en la extracción de vacantes: {e}")
        return False

    if not vacantes_actuales:
        logger.warning("No se encontraron vacantes activas en el portal en este momento.")

    # 3. Detectar novedades comparando contra histórico
    novedades = detectar_novedades(vacantes_actuales, historicas)
    duracion = time.time() - inicio_tiempo

    # 4. Guardar en Base de Datos
    guardar_resultado_consulta(
        vacantes_actuales=vacantes_actuales,
        novedades=novedades,
        duracion_segundos=duracion,
        estado_ejecucion="EXITOSO"
    )

    # 5. Exportar archivos Excel y JSON para la web (GitHub Pages)
    historico_completo = obtener_todas_las_vacantes_db()
    exportar_excel(vacantes_actuales, novedades, historico_completo)
    exportar_json_para_web(vacantes_actuales, novedades, historico_completo)

    # 6. Notificaciones
    if novedades.get("nuevas"):
        despachar_notificaciones(novedades["nuevas"])

    # 7. Resumen en consola
    res = novedades["resumen"]
    logger.info("-" * 65)
    logger.info("📊 RESUMEN DE LA EJECUCIÓN:")
    logger.info(f"   • Total vacantes activas:     {res['total_actuales']}")
    logger.info(f"   • Nuevas publicaciones:       {res['total_nuevas']}")
    logger.info(f"   • Publicaciones actualizadas: {res['total_actualizadas']}")
    logger.info(f"   • Publicaciones cerradas:     {res['total_cerradas']}")
    logger.info(f"   • Duración total:             {duracion:.2f} segundos")
    
    if res['total_nuevas'] > 0:
        logger.info("\n🎉 DETALLE DE NUEVAS OPORTUNIDADES:")
        for i, n in enumerate(novedades["nuevas"]):
            logger.info(
                f"   [{i+1:02d}] {n.get('departamento')} | {n.get('municipio')} | "
                f"{n.get('area')} | {n.get('cargo')} | Cierre: {n.get('fecha_cierre_texto')}"
            )
    else:
        logger.info("\n✅ Sin nuevas vacantes respecto a la consulta anterior.")

    logger.info("=" * 65)
    return True

if __name__ == "__main__":
    exito = ejecutar_monitor()
    sys.exit(0 if exito else 1)
