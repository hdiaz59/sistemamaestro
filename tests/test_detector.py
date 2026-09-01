"""
Pruebas unitarias para el módulo detector.py
"""
import unittest
from app.detector import detectar_novedades

class TestDetector(unittest.TestCase):

    def test_detectar_nuevas_y_actualizadas(self):
        historicas = {
            "hash_1": {"id_vacante": "hash_1", "postulados": 10, "activa": True},
            "hash_2": {"id_vacante": "hash_2", "postulados": 5, "activa": True},
            "hash_3": {"id_vacante": "hash_3", "postulados": 2, "activa": True},
        }

        actuales = [
            {"id_vacante": "hash_1", "postulados": 10, "departamento": "Caldas"}, # Sin cambios
            {"id_vacante": "hash_2", "postulados": 8, "departamento": "Caldas"},  # Actualizada (más postulados)
            {"id_vacante": "hash_4", "postulados": 1, "departamento": "Risaralda"}, # NUEVA
            {"id_vacante": "hash_5", "postulados": 0, "departamento": "Antioquia"},  # NUEVA
        ]

        resultado = detectar_novedades(actuales, historicas)
        
        # Nuevas deben ser 2 (hash_4, hash_5)
        self.assertEqual(len(resultado["nuevas"]), 2)
        nuevas_ids = [n["id_vacante"] for n in resultado["nuevas"]]
        self.assertIn("hash_4", nuevas_ids)
        self.assertIn("hash_5", nuevas_ids)

        # Actualizadas debe ser 1 (hash_2)
        self.assertEqual(len(resultado["actualizadas"]), 1)
        self.assertEqual(resultado["actualizadas"][0]["id_vacante"], "hash_2")

        # Sin cambios debe ser 1 (hash_1)
        self.assertEqual(len(resultado["sin_cambios"]), 1)
        self.assertEqual(resultado["sin_cambios"][0]["id_vacante"], "hash_1")

        # Cerradas debe ser 1 (hash_3 que ya no vino en actuales)
        self.assertEqual(len(resultado["cerradas"]), 1)
        self.assertEqual(resultado["cerradas"][0]["id_vacante"], "hash_3")

        # Resumen
        res = resultado["resumen"]
        self.assertEqual(res["total_actuales"], 4)
        self.assertEqual(res["total_nuevas"], 2)
        self.assertEqual(res["total_actualizadas"], 1)
        self.assertEqual(res["total_cerradas"], 1)

if __name__ == "__main__":
    unittest.main()
