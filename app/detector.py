"""
Módulo Detector de Novedades y Cambios
Compara las vacantes recién extraídas contra el histórico de la base de datos para clasificar novedades.
"""
from typing import List, Dict, Any
from app.logger import logger

def detectar_novedades(
    vacantes_actuales: List[Dict[str, Any]],
    vacantes_historicas: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compara las vacantes extraídas en la consulta actual con el histórico persistido.
    
    Retorna un diccionario con:
    - 'nuevas': lista de vacantes que no existían previamente.
    - 'actualizadas': lista de vacantes existentes que cambiaron de postulados u otro dato.
    - 'sin_cambios': lista de vacantes activas idénticas a la última consulta.
    - 'cerradas': lista de vacantes que antes estaban activas pero ya no figuran en el portal.
    - 'resumen': conteos estadísticos.
    """
    nuevas = []
    actualizadas = []
    sin_cambios = []
    ids_actuales = set()

    for v in vacantes_actuales:
        v_id = v["id_vacante"]
        ids_actuales.add(v_id)

        if v_id not in vacantes_historicas:
            v_copia = dict(v)
            v_copia["estado"] = "NUEVA"
            nuevas.append(v_copia)
        else:
            hist = vacantes_historicas[v_id]
            # Obtener datos del objeto SQLAlchemy o diccionario
            hist_postulados = getattr(hist, "postulados", hist.get("postulados") if isinstance(hist, dict) else 0)
            
            v_copia = dict(v)
            if v.get("postulados", 0) != hist_postulados:
                v_copia["estado"] = "ACTUALIZADA"
                v_copia["postulados_anteriores"] = hist_postulados
                actualizadas.append(v_copia)
            else:
                v_copia["estado"] = "ACTIVA"
                sin_cambios.append(v_copia)

    # Detectar cerradas
    cerradas = []
    for v_id, hist in vacantes_historicas.items():
        hist_activa = getattr(hist, "activa", hist.get("activa", True) if isinstance(hist, dict) else True)
        if v_id not in ids_actuales and hist_activa:
            if hasattr(hist, "to_dict"):
                c_dict = hist.to_dict()
            elif isinstance(hist, dict):
                c_dict = dict(hist)
            else:
                c_dict = {"id_vacante": v_id}
            c_dict["estado"] = "CERRADA"
            cerradas.append(c_dict)

    deptos_nuevas = sorted(list(set(n.get("departamento", "") for n in nuevas if n.get("departamento"))))
    mpios_nuevas = sorted(list(set(n.get("municipio", "") for n in nuevas if n.get("municipio"))))

    resumen = {
        "total_actuales": len(vacantes_actuales),
        "total_nuevas": len(nuevas),
        "total_actualizadas": len(actualizadas),
        "total_sin_cambios": len(sin_cambios),
        "total_cerradas": len(cerradas),
        "departamentos_con_nuevas": deptos_nuevas,
        "municipios_con_nuevas": mpios_nuevas,
    }

    logger.info(
        f"Detección completada: {resumen['total_actuales']} activas | "
        f"{resumen['total_nuevas']} NUEVAS | "
        f"{resumen['total_actualizadas']} actualizadas | "
        f"{resumen['total_cerradas']} cerradas"
    )

    return {
        "nuevas": nuevas,
        "actualizadas": actualizadas,
        "sin_cambios": sin_cambios,
        "cerradas": cerradas,
        "resumen": resumen
    }
