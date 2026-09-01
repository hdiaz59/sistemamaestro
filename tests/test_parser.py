"""
Pruebas unitarias para el módulo parser.py
"""
import unittest
from app.parser import (
    extraer_view_state,
    extraer_info_paginacion,
    parsear_pagina_html,
    parsear_respuesta_ajax
)

HTML_MOCK = """
<html>
<body>
<form id="form-busqueda" action="/SistemaMaestro/busquedaVacantes.xhtml">
    <input type="hidden" name="javax.faces.ViewState" value="token123456789" />
    <span class="ui-paginator-current">(1 of 5)</span>
    <div id="form-busqueda:tabla-vacantes">
        <div class="ui-datagrid-column">
            <div class="vacante">
                <label>Cargo Docente de Aula</label>
                <label>Postulados: 12</label>
                <label>Tipo Priorización: Vacantes Generales</label>
                <label>Cierre vacante: 02/09/2026 a las 11:17</label>
                <label>Área: Preescolar</label>
                <label>Secretaría de Educación: Pereira</label>
                <label>Departamento: Risaralda</label>
                <label>Municipio: Pereira</label>
            </div>
        </div>
    </div>
</form>
</body>
</html>
"""

XML_AJAX_MOCK = """<?xml version='1.0' encoding='UTF-8'?>
<partial-response>
  <changes>
    <update id="form-busqueda:tabla-vacantes"><![CDATA[
      <div class="ui-datagrid-column">
        <div class="vacante">
          <label>Cargo Docente Orientador</label>
          <label>Postulados: 5</label>
          <label>Área: Orientación Escolar</label>
          <label>Departamento: Caldas</label>
          <label>Municipio: Manizales</label>
          <label>Cierre vacante: 02/09/2026 a las 11:25</label>
        </div>
      </div>
    ]]></update>
    <update id="javax.faces.ViewState"><![CDATA[newtoken987654321]]></update>
  </changes>
</partial-response>
"""

class TestParser(unittest.TestCase):

    def test_extraer_view_state(self):
        vs = extraer_view_state(HTML_MOCK)
        self.assertEqual(vs, "token123456789")

    def test_extraer_info_paginacion(self):
        pag_actual, total_pags = extraer_info_paginacion(HTML_MOCK)
        self.assertEqual(pag_actual, 1)
        self.assertEqual(total_pags, 5)

    def test_parsear_pagina_html(self):
        vacs, pag_info, vs = parsear_pagina_html(HTML_MOCK, numero_pagina=1)
        self.assertEqual(len(vacs), 1)
        self.assertEqual(pag_info, (1, 5))
        self.assertEqual(vs, "token123456789")
        self.assertIn("Pereira", vacs[0].get("municipio", ""))

    def test_parsear_respuesta_ajax(self):
        vacs, nuevo_vs = parsear_respuesta_ajax(XML_AJAX_MOCK, numero_pagina=2)
        self.assertEqual(len(vacs), 1)
        self.assertEqual(nuevo_vs, "newtoken987654321")
        self.assertEqual(vacs[0].get("cargo"), "Cargo Docente Orientador")
        self.assertEqual(vacs[0].get("municipio"), "Municipio: Manizales")

if __name__ == "__main__":
    unittest.main()
