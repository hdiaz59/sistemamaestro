"""
Pruebas unitarias para el módulo database.py
"""
import unittest
from app.database import (
    init_db,
    guardar_resultado_consulta,
    obtener_todas_las_vacantes_db,
    obtener_vacantes_historicas_db
)

class TestDatabase(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_guardar_y_recuperar_vacantes(self):
        vacantes_mock = [
            {
                "id_vacante": "test_hash_abc_123",
                "cargo": "Docente de Matemáticas",
                "area": "Matemáticas",
                "secretaria": "Caldas",
                "departamento": "Caldas",
                "municipio": "Manizales",
                "zona": "Manizales",
                "tipo_priorizacion": "Vacantes Generales",
                "postulados": 10,
                "fecha_cierre_texto": "02/09/2026 11:30",
                "fecha_cierre_iso": "2026-09-02 11:30:00",
                "url_portal": "https://sistemamaestro.mineducacion.gov.co",
            }
        ]
        novedades_mock = {
            "nuevas": vacantes_mock,
            "actualizadas": [],
            "cerradas": []
        }

        guardar_resultado_consulta(vacantes_mock, novedades_mock, duracion_segundos=1.5)
        
        historicas = obtener_vacantes_historicas_db()
        self.assertIn("test_hash_abc_123", historicas)
        
        vacante_obj = historicas["test_hash_abc_123"]
        self.assertEqual(vacante_obj.municipio, "Manizales")
        self.assertEqual(vacante_obj.postulados, 10)
        self.assertTrue(vacante_obj.activa)

if __name__ == "__main__":
    unittest.main()
