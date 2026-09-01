"""
Pruebas unitarias para el módulo normalizer.py
"""
import unittest
from app.normalizer import (
    reparar_texto,
    limpiar_prefijo,
    extraer_numero_postulados,
    parsear_fecha_cierre,
    generar_id_vacante,
    normalizar_vacante
)

class TestNormalizer(unittest.TestCase):

    def test_reparar_texto_con_caracteres_mal_codificados(self):
        self.assertEqual(reparar_texto("Educaci\ufffdn"), "Educación")
        self.assertEqual(reparar_texto("\ufffdrea: Preescolar"), "Área: Preescolar")
        self.assertEqual(reparar_texto("Priorizaci\ufffdn"), "Priorización")
        self.assertEqual(reparar_texto("Caquet\ufffd"), "Caquetá")
        self.assertEqual(reparar_texto("Cartagena Del Chair\ufffd"), "Cartagena Del Chairá")

    def test_limpiar_prefijo(self):
        self.assertEqual(limpiar_prefijo("Cargo: Docente de Aula", "Cargo"), "Docente de Aula")
        self.assertEqual(limpiar_prefijo("Área: Preescolar", "Área"), "Preescolar")
        self.assertEqual(limpiar_prefijo("Secretaría de Educación: Pereira", "Secretaría de Educación"), "Pereira")
        self.assertEqual(limpiar_prefijo("Departamento: Risaralda", "Departamento"), "Risaralda")

    def test_extraer_numero_postulados(self):
        self.assertEqual(extraer_numero_postulados("Postulados: 26"), 26)
        self.assertEqual(extraer_numero_postulados("Postulados: 0"), 0)
        self.assertEqual(extraer_numero_postulados(""), 0)
        self.assertEqual(extraer_numero_postulados(None), 0)

    def test_parsear_fecha_cierre(self):
        res = parsear_fecha_cierre("Cierre vacante: 02/09/2026 a las 11:17")
        self.assertEqual(res["fecha_cierre_texto"], "02/09/2026 11:17")
        self.assertEqual(res["fecha_cierre_iso"], "2026-09-02 11:17:00")

    def test_generar_id_vacante_determinista(self):
        v1 = {
            "secretaria": "Pereira",
            "departamento": "Risaralda",
            "municipio": "Pereira",
            "cargo": "Docente de Aula",
            "area": "Preescolar",
            "tipo_priorizacion": "Vacantes Generales",
            "fecha_cierre_texto": "02/09/2026 11:17"
        }
        v2 = {
            "secretaria": "pereira",
            "departamento": "risaralda",
            "municipio": "pereira",
            "cargo": "docente de aula",
            "area": "preescolar",
            "tipo_priorizacion": "vacantes generales",
            "fecha_cierre_texto": "02/09/2026 11:17"
        }
        id1 = generar_id_vacante(v1)
        id2 = generar_id_vacante(v2)
        self.assertEqual(id1, id2)
        self.assertEqual(len(id1), 64)

    def test_normalizar_vacante_completa(self):
        raw = {
            "cargo": "Cargo Docente de Aula",
            "postulados": "Postulados: 15",
            "tipo_priorizacion": "Tipo Priorizaci\ufffdn: Vacantes Generales",
            "cierre_vacante": "Cierre vacante: 02/09/2026 a las 11:17",
            "area": "\ufffdrea: Matem\ufffdticas",
            "secretaria": "Secretar\ufffda de Educaci\ufffdn: Caldas",
            "zona": "Zona: Manzanares",
            "departamento": "Departamento: Caldas",
            "municipio": "Municipio: Manzanares"
        }
        norm = normalizar_vacante(raw)
        self.assertEqual(norm["cargo"], "Docente de Aula")
        self.assertEqual(norm["postulados"], 15)
        self.assertEqual(norm["area"], "Matemáticas")
        self.assertEqual(norm["departamento"], "Caldas")
        self.assertEqual(norm["municipio"], "Manzanares")
        self.assertEqual(norm["secretaria"], "Caldas")
        self.assertTrue(len(norm["id_vacante"]) == 64)

if __name__ == "__main__":
    unittest.main()
