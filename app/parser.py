"""
Módulo de Extracción y Parsing HTML/JSF
Extrae tarjetas de vacantes, paginación y ViewState de páginas HTML y respuestas parciales AJAX de PrimeFaces.
"""
import re
import warnings
from typing import List, Dict, Any, Tuple, Optional
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# Suprimir advertencia de BeautifulSoup al parsear respuestas XML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def extraer_view_state(html_o_xml: str) -> Optional[str]:
    """Extrae el token javax.faces.ViewState del contenido."""
    if not html_o_xml:
        return None
    
    # 1. Buscar en etiquetas input de formularios
    soup = BeautifulSoup(html_o_xml, "html.parser")
    vs_tag = soup.find("input", {"name": "javax.faces.ViewState"})
    if vs_tag and vs_tag.get("value"):
        return vs_tag["value"].strip()
    
    # 2. Buscar en actualizaciones XML <update id="javax.faces.ViewState">
    update_tags = soup.find_all("update")
    for u in update_tags:
        if "ViewState" in (u.get("id") or ""):
            val = u.text.strip()
            if val:
                return val
            
    # 3. Fallback con regex
    match = re.search(r'id=["\']javax\.faces\.ViewState["\'][^>]*value=["\']([^"\']+)["\']', html_o_xml)
    if match:
        return match.group(1).strip()
    
    match_cdata = re.search(r'<update id="[^"]*javax\.faces\.ViewState[^"]*"><!\[CDATA\[(.*?)\]\]></update>', html_o_xml)
    if match_cdata:
        return match_cdata.group(1).strip()

    return None

def extraer_info_paginacion(html_o_xml: str) -> Tuple[int, int]:
    """
    Extrae la página actual y el número total de páginas del texto paginador '(1 of 4)'.
    Retorna (pagina_actual, total_paginas).
    """
    if not html_o_xml:
        return 1, 1
    
    soup = BeautifulSoup(html_o_xml, "html.parser")
    paginator_elem = soup.find(class_=lambda c: c and "ui-paginator-current" in c)
    texto = paginator_elem.get_text() if paginator_elem else ""
    
    if not texto:
        match_raw = re.search(r"\((\d+)\s+of\s+(\d+)\)", html_o_xml)
        if match_raw:
            return int(match_raw.group(1)), int(match_raw.group(2))
        return 1, 1

    match = re.search(r"\((\d+)\s+of\s+(\d+)\)", texto)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    return 1, 1

def extraer_tarjetas_de_soup(soup_contenedor, numero_pagina: int = 1) -> List[Dict[str, Any]]:
    """Extrae información cruda de cada tarjeta .ui-datagrid-column o .vacante evitando anidamientos duplicados."""
    # Buscar primero las columnas del datagrid
    cards = soup_contenedor.find_all(class_=lambda c: c and "ui-datagrid-column" in c)
    if not cards:
        cards = soup_contenedor.find_all(class_=lambda c: c and "vacante" in c)
    
    resultados = []
    for c in cards:
        # Extraer todos los labels
        labels = c.find_all("label")
        if not labels:
            continue
        
        datos = {"numero_pagina": numero_pagina}
        for l in labels:
            t = l.get_text(strip=True)
            if not t:
                continue
            
            # Clasificar campos basados en palabras clave
            t_lower = t.lower()
            if t_lower.startswith("cargo"):
                datos["cargo"] = t
            elif "postulados:" in t_lower:
                datos["postulados"] = t
            elif "priorizaci" in t_lower:
                datos["tipo_priorizacion"] = t
            elif "cierre vacante:" in t_lower:
                datos["cierre_vacante"] = t
            elif any(k in t_lower for k in ["área:", "area:", "rea:"]):
                datos["area"] = t
            elif "secretar" in t_lower:
                datos["secretaria"] = t
            elif "zona:" in t_lower:
                datos["zona"] = t
            elif "departamento:" in t_lower:
                datos["departamento"] = t
            elif "municipio:" in t_lower:
                datos["municipio"] = t
                
        # Solo agregar si tiene información representativa
        if datos.get("cargo") or datos.get("municipio") or datos.get("area"):
            resultados.append(datos)
            
    return resultados

def parsear_pagina_html(html_text: str, numero_pagina: int = 1) -> Tuple[List[Dict[str, Any]], Tuple[int, int], Optional[str]]:
    """
    Parsea una página HTML completa de Sistema Maestro.
    Retorna (lista_vacantes_crudas, (pag_actual, total_pags), view_state).
    """
    soup = BeautifulSoup(html_text, "html.parser")
    pag_info = extraer_info_paginacion(html_text)
    view_state = extraer_view_state(html_text)
    
    grid = soup.find(id=lambda i: i and "tabla-vacantes" in i)
    contenedor = grid if grid else soup
    vacantes = extraer_tarjetas_de_soup(contenedor, numero_pagina)
    
    return vacantes, pag_info, view_state

def parsear_respuesta_ajax(xml_text: str, numero_pagina: int = 1) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Parsea una respuesta parcial AJAX (XML) de PrimeFaces.
    Retorna (lista_vacantes_crudas, nuevo_view_state).
    """
    soup = BeautifulSoup(xml_text, "html.parser")
    vacantes = []
    nuevo_view_state = None
    
    for u in soup.find_all("update"):
        u_id = u.get("id", "")
        if "tabla-vacantes" in u_id:
            cdata_soup = BeautifulSoup(u.text, "html.parser")
            vacantes = extraer_tarjetas_de_soup(cdata_soup, numero_pagina)
        elif "ViewState" in u_id:
            nuevo_view_state = u.text.strip()
            
    return vacantes, nuevo_view_state
