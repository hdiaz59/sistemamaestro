"""
Módulo de Extracción / Scraper
Ejecuta la consulta automatizada contra el portal Sistema Maestro.
Soporta extracción ultrarrápida mediante sesión HTTP JSF y fallback con Playwright.
"""
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
import urllib3
from app.config import SISTEMA_MAESTRO_URL, TIMEOUT, MAX_PAGES, USER_AGENT
from app.logger import logger
from app.parser import parsear_pagina_html, parsear_respuesta_ajax
from app.normalizer import normalizar_vacante

# Deshabilitar advertencias de certificados no verificados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SistemaMaestroScraper:
    """Scraper para el portal Sistema Maestro del MEN."""

    def __init__(self, base_url: str = SISTEMA_MAESTRO_URL, timeout: int = TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout / 1000.0 if timeout > 1000 else timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": self.base_url,
        })

    def extraer_http(self) -> List[Dict[str, Any]]:
        """
        Extrae todas las vacantes disponibles recorriendo todas las páginas mediante solicitudes HTTP JSF/AJAX.
        """
        logger.info(f"Iniciando extracción HTTP desde {self.base_url}...")
        inicio = time.time()
        todas_las_vacantes: List[Dict[str, Any]] = []
        ids_vistos = set()

        # Paso 1: Obtener la primera página
        try:
            r1 = self.session.get(self.base_url, verify=False, timeout=self.timeout)
            r1.raise_for_status()
        except Exception as e:
            logger.error(f"Error al conectar con el portal Sistema Maestro: {e}")
            raise

        vacantes_p1_raw, (pag_actual, total_paginas), view_state = parsear_pagina_html(r1.text, numero_pagina=1)
        logger.info(f"Página 1 cargada. Total de páginas detectadas: {total_paginas}. Vacantes en P1: {len(vacantes_p1_raw)}")

        # Normalizar vacantes de P1
        for v_raw in vacantes_p1_raw:
            v_norm = normalizar_vacante(v_raw)
            if v_norm["id_vacante"] not in ids_vistos:
                ids_vistos.add(v_norm["id_vacante"])
                todas_las_vacantes.append(v_norm)

        # Si no hay más páginas o no hay ViewState, retornar P1
        if total_paginas <= 1 or not view_state:
            duracion = time.time() - inicio
            logger.info(f"Extracción finalizada en {duracion:.2f}s. Total vacantes obtenidas: {len(todas_las_vacantes)}")
            return todas_las_vacantes

        # Paso 2: Recorrer páginas siguientes mediante AJAX
        headers_ajax = {
            "User-Agent": USER_AGENT,
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Faces-Request": "partial/ajax",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://sistemamaestro.mineducacion.gov.co",
            "Referer": self.base_url,
        }

        limite_paginas = min(total_paginas, MAX_PAGES)
        for num_pag in range(2, limite_paginas + 1):
            first_idx = (num_pag - 1) * 6
            payload = {
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": "form-busqueda:tabla-vacantes",
                "javax.faces.partial.execute": "form-busqueda:tabla-vacantes",
                "javax.faces.partial.render": "form-busqueda:tabla-vacantes",
                "form-busqueda:tabla-vacantes": "form-busqueda:tabla-vacantes",
                "form-busqueda:tabla-vacantes_pagination": "true",
                "form-busqueda:tabla-vacantes_first": str(first_idx),
                "form-busqueda:tabla-vacantes_rows": "6",
                "form-busqueda:tabla-vacantes_skipChildren": "true",
                "form-busqueda:tabla-vacantes_encodeFeature": "true",
                "form-busqueda": "form-busqueda",
                "javax.faces.ViewState": view_state,
            }

            try:
                r_ajax = self.session.post(
                    self.base_url,
                    headers=headers_ajax,
                    data=payload,
                    verify=False,
                    timeout=self.timeout
                )
                r_ajax.raise_for_status()
                vacs_p_raw, nuevo_vs = parsear_respuesta_ajax(r_ajax.text, numero_pagina=num_pag)
                if nuevo_vs:
                    view_state = nuevo_vs

                agregadas = 0
                for v_raw in vacs_p_raw:
                    v_norm = normalizar_vacante(v_raw)
                    if v_norm["id_vacante"] not in ids_vistos:
                        ids_vistos.add(v_norm["id_vacante"])
                        todas_las_vacantes.append(v_norm)
                        agregadas += 1

                logger.info(f"Página {num_pag}/{limite_paginas} procesada. Vacantes extraídas: {len(vacs_p_raw)} (Nuevas únicas: {agregadas})")
                time.sleep(0.3)  # Pausa de cortesía para no saturar el servidor
            except Exception as e:
                logger.warning(f"Error al obtener página {num_pag}: {e}. Continuando con siguientes páginas...")

        duracion = time.time() - inicio
        logger.info(f"Extracción HTTP completada en {duracion:.2f}s. Total vacantes únicas: {len(todas_las_vacantes)}")
        return todas_las_vacantes

    def extraer_playwright(self) -> List[Dict[str, Any]]:
        """
        Fallback utilizando Playwright para navegación con motor de navegador real.
        """
        from playwright.sync_api import sync_playwright
        logger.info("Iniciando extracción con Playwright...")
        todas_las_vacantes = []
        ids_vistos = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent=USER_AGENT
            )
            page = context.new_page()
            page.goto(self.base_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)

            page_num = 1
            while page_num <= MAX_PAGES:
                html = page.content()
                vacs_raw, (pag_act, tot_pags), _ = parsear_pagina_html(html, numero_pagina=page_num)
                for v in vacs_raw:
                    v_norm = normalizar_vacante(v)
                    if v_norm["id_vacante"] not in ids_vistos:
                        ids_vistos.add(v_norm["id_vacante"])
                        todas_las_vacantes.append(v_norm)

                logger.info(f"[Playwright] Página {page_num}/{tot_pags} procesada. Total acumulado: {len(todas_las_vacantes)}")
                
                if page_num >= tot_pags:
                    break

                # Intentar avanzar a la siguiente página
                next_btn = page.locator(".ui-paginator-next").first
                if not next_btn.is_visible() or "ui-state-disabled" in (next_btn.get_attribute("class") or ""):
                    break

                next_btn.click()
                time.sleep(2)
                page_num += 1

            browser.close()

        return todas_las_vacantes

    def consultar(self) -> List[Dict[str, Any]]:
        """
        Método principal que intenta primero HTTP y en caso de fallo crítico recurre a Playwright.
        """
        try:
            return self.extraer_http()
        except Exception as e:
            logger.warning(f"Extracción HTTP falló ({e}). Intentando fallback con Playwright...")
            try:
                return self.extraer_playwright()
            except Exception as e_pw:
                logger.error(f"Fallo crítico en ambos métodos de extracción: {e_pw}")
                raise e_pw
