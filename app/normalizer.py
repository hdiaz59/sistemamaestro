"""
Módulo de Normalización de Datos
Limpia textos, repara codificación de caracteres, estandariza fechas y genera identificadores únicos (hash).
"""
import hashlib
import re
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional

# Diccionario de reemplazos para reparar caracteres mal codificados del portal JSF
REPARACIONES_TEXTO = {
    r"Educaci[\ufffd\?]n": "Educación",
    r"[\ufffd\?]rea": "Área",
    r"Priorizaci[\ufffd\?]n": "Priorización",
    r"Ingl[\ufffd\?]s": "Inglés",
    r"Matem[\ufffd\?]ticas": "Matemáticas",
    r"Caquet[\ufffd\?]": "Caquetá",
    r"Chair[\ufffd\?]": "Chairá",
    r"a[\ufffd\?]os": "años",
    r"asignaci[\ufffd\?]n": "asignación",
    r"Secretar[\ufffd\?]a": "Secretaría",
    r"f[\ufffd\?]sica": "física",
    r"recreaci[\ufffd\?]n": "recreación",
    r"Bogot[\ufffd\?]": "Bogotá",
    r"Atl[\ufffd\?]ntico": "Atlántico",
    r"Bol[\ufffd\?]var": "Bolívar",
    r"Boyac[\ufffd\?]": "Boyacá",
    r"C[\ufffd\?]rdoba": "Córdoba",
    r"Guain[\ufffd\?]a": "Guainía",
    r"Nari[\ufffd\?]o": "Nariño",
    r"Quind[\ufffd\?]o": "Quindío",
    r"San Andr[\ufffd\?]s": "San Andrés",
    r"Vaup[\ufffd\?]s": "Vaupés",
    r"Tecnolog[\ufffd\?]a": "Tecnología",
    r"Inform[\ufffd\?]tica": "Informática",
    r"Filosof[\ufffd\?]a": "Filosofía",
    r"Espa[\ufffd\?]ol": "Español",
    r"M[\ufffd\?]sica": "Música",
}

def reparar_texto(texto: Optional[str]) -> str:
    """Repara caracteres de reemplazo comunes del portal y normaliza espacios."""
    if not texto:
        return ""
    
    res = str(texto)
    for patron, reemplazo in REPARACIONES_TEXTO.items():
        res = re.sub(patron, reemplazo, res, flags=re.IGNORECASE)
    
    # Reemplazar cualquier caracter Unicode de reemplazo restante
    res = res.replace("\ufffd", "").replace("", "")
    # Normalizar espacios múltiples
    res = re.sub(r"\s+", " ", res).strip()
    return res

def limpiar_prefijo(texto: Optional[str], prefijo: str) -> str:
    """Elimina prefijos comunes como 'Área:', 'Cargo:', 'Municipio:', etc."""
    limpio = reparar_texto(texto)
    if not limpio:
        return ""
    
    # Remover prefijo ignorando mayúsculas/minúsculas y dos puntos
    patron = rf"^{re.escape(prefijo)}\s*:?\s*"
    limpio = re.sub(patron, "", limpio, flags=re.IGNORECASE).strip()
    return limpio

def extraer_numero_postulados(texto: Optional[str]) -> int:
    """Extrae el número entero de postulados."""
    if not texto:
        return 0
    match = re.search(r"\d+", str(texto))
    return int(match.group(0)) if match else 0

def parsear_fecha_cierre(texto: Optional[str]) -> Dict[str, Any]:
    """
    Parsea la fecha de cierre en formato del portal:
    '02/09/2026 a las 11:17' -> datetime ISO
    """
    limpio = reparar_texto(texto)
    # Extraer parte fecha y hora
    # Ej: 'Cierre vacante: 02/09/2026 a las 11:17'
    match = re.search(r"(\d{2}/\d{2}/\d{4})\s*(?:a\s+las\s*)?(\d{1,2}:\d{2})?", limpio, re.IGNORECASE)
    if not match:
        return {"fecha_cierre_texto": limpio, "fecha_cierre_iso": None}
    
    fecha_str = match.group(1)
    hora_str = match.group(2) if match.group(2) else "23:59"
    
    try:
        dt = datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M")
        return {
            "fecha_cierre_texto": f"{fecha_str} {hora_str}",
            "fecha_cierre_iso": dt.strftime("%Y-%m-%d %H:%M:00")
        }
    except Exception:
        return {"fecha_cierre_texto": limpio, "fecha_cierre_iso": None}

def normalizar_cadena_hash(texto: Optional[str]) -> str:
    """Normaliza texto para comparación y generación de hash único (sin acentos, minúsculas)."""
    if not texto:
        return ""
    t = str(texto).lower().strip()
    # Eliminar acentos
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    # Estandarizar espacios
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def generar_id_vacante(datos: Dict[str, Any]) -> str:
    """
    Genera un identificador único SHA-256 estable y determinista a partir de los datos normalizados.
    Secretaría + Departamento + Municipio + Cargo + Área + Tipo Priorización + Fecha Cierre
    """
    componentes = [
        normalizar_cadena_hash(datos.get("secretaria")),
        normalizar_cadena_hash(datos.get("departamento")),
        normalizar_cadena_hash(datos.get("municipio")),
        normalizar_cadena_hash(datos.get("cargo")),
        normalizar_cadena_hash(datos.get("area")),
        normalizar_cadena_hash(datos.get("tipo_priorizacion")),
        normalizar_cadena_hash(datos.get("fecha_cierre_texto")),
    ]
    clave = "|".join(componentes)
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()

def normalizar_vacante(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Toma un diccionario con datos crudos de una tarjeta y devuelve la estructura normalizada completa.
    """
    cargo = limpiar_prefijo(raw_dict.get("cargo"), "Cargo")
    area = limpiar_prefijo(raw_dict.get("area"), "Área")
    secretaria = limpiar_prefijo(raw_dict.get("secretaria"), "Secretaría de Educación")
    departamento = limpiar_prefijo(raw_dict.get("departamento"), "Departamento")
    municipio = limpiar_prefijo(raw_dict.get("municipio"), "Municipio")
    zona = limpiar_prefijo(raw_dict.get("zona"), "Zona")
    tipo_priorizacion = limpiar_prefijo(raw_dict.get("tipo_priorizacion"), "Tipo Priorización")
    
    postulados = extraer_numero_postulados(raw_dict.get("postulados"))
    info_cierre = parsear_fecha_cierre(raw_dict.get("cierre_vacante"))
    
    norm = {
        "cargo": cargo,
        "area": area,
        "secretaria": secretaria,
        "departamento": departamento,
        "municipio": municipio,
        "zona": zona,
        "tipo_priorizacion": tipo_priorizacion or "Vacantes Generales",
        "postulados": postulados,
        "fecha_cierre_texto": info_cierre["fecha_cierre_texto"],
        "fecha_cierre_iso": info_cierre["fecha_cierre_iso"],
        "url_portal": "https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml",
    }
    
    norm["id_vacante"] = generar_id_vacante(norm)
    return norm
