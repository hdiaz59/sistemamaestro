# Skill: Monitor de Vacantes Sistema Maestro

## 1. Nombre

**monitor-sistema-maestro**

## 2. Propósito

Desarrollar una aplicación que consulte automáticamente el portal oficial **Sistema Maestro del Ministerio de Educación Nacional de Colombia**, identifique las oportunidades/vacantes disponibles, detecte nuevas publicaciones respecto de consultas anteriores y genere un histórico de resultados.

Fuente principal:

`https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml`

La aplicación debe comenzar con una consulta **general**, sin restringir departamento, municipio, Secretaría de Educación, área o cargo.

---

# 3. Objetivo funcional

Construir un sistema capaz de responder automáticamente:

> **¿Qué nuevas oportunidades han sido publicadas en Sistema Maestro desde la última consulta?**

La aplicación debe:

1. Consultar el portal.
2. Ejecutar la búsqueda con los filtros abiertos.
3. Obtener todas las oportunidades disponibles.
4. Recorrer todas las páginas de resultados.
5. Extraer la información relevante.
6. Generar un identificador único por oportunidad.
7. Comparar contra el histórico.
8. Identificar únicamente las nuevas publicaciones.
9. Almacenar los resultados.
10. Mostrar las novedades.
11. Permitir filtros posteriores.
12. Preparar mecanismos de notificación.

---

# 4. Principio fundamental

No asumir que el portal entrega las vacantes directamente en HTML.

Primero determinar cómo funciona técnicamente:

```text
Página
   ↓
Formulario
   ↓
Botón Buscar
   ↓
Solicitud HTTP/AJAX
   ↓
Resultados
   ↓
Paginación
```

Si la información es dinámica, utilizar:

* Playwright como primera opción.
* Selenium como alternativa.
* `requests` únicamente cuando exista un endpoint HTTP estable y accesible.

---

# 5. Arquitectura

```text
┌──────────────────────────────────────┐
│          Sistema Maestro MEN         │
│ búsquedaVacantes.xhtml               │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       Módulo de extracción           │
│ Playwright / Selenium / Requests     │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       Normalización de datos         │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│      Identificador de vacante        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│        Base de datos histórica       │
└──────────────────┬───────────────────┘
                   │
                   ▼
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
     Nuevas vacantes    Sin cambios
          │
          ▼
┌──────────────────────────────────────┐
│       Filtros y clasificación        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│      Dashboard / Reporte / API       │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       Notificaciones opcionales      │
│ Email / Telegram / WhatsApp          │
└──────────────────────────────────────┘
```

---

# 6. Tecnologías recomendadas

## Backend

Python 3.11+

Librerías iniciales:

```text
playwright
pandas
openpyxl
SQLAlchemy
requests
beautifulsoup4
python-dotenv
```

Instalación:

```bash
pip install playwright pandas openpyxl sqlalchemy requests beautifulsoup4 python-dotenv
playwright install chromium
```

---

# 7. Estructura del proyecto

Crear:

```text
monitor-sistema-maestro/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── scraper.py
│   ├── parser.py
│   ├── normalizer.py
│   ├── detector.py
│   ├── database.py
│   ├── filters.py
│   ├── notifier.py
│   └── logger.py
│
├── data/
│   ├── sistema_maestro.db
│   ├── historico/
│   └── exportaciones/
│
├── tests/
│   ├── test_parser.py
│   ├── test_detector.py
│   └── test_normalizer.py
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── main.py
```

---

# 8. Módulo de configuración

Crear variables configurables:

```text
SYSTEMA_MAESTRO_URL
DATABASE_URL
HEADLESS
TIMEOUT
MAX_PAGES
EXPORT_EXCEL
LOG_LEVEL
```

Ejemplo:

```env
SISTEMA_MAESTRO_URL=https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml
DATABASE_URL=sqlite:///data/sistema_maestro.db
HEADLESS=true
TIMEOUT=60000
MAX_PAGES=100
```

No colocar credenciales directamente en el código.

---

# 9. Extracción

El scraper debe:

1. Abrir el portal.
2. Esperar que cargue completamente.
3. Identificar los controles del formulario.
4. Mantener los filtros en estado general.
5. Ejecutar la búsqueda.
6. Esperar los resultados.
7. Detectar la tabla o componente de resultados.
8. Extraer registros.
9. Detectar paginación.
10. Recorrer todas las páginas.
11. Evitar duplicados.
12. Cerrar correctamente el navegador.

Debe registrar:

```text
fecha_consulta
hora_consulta
url
numero_pagina
numero_registros
estado
error
```

---

# 10. Paginación

Nunca asumir que la primera página contiene todas las oportunidades.

Implementar:

```text
Página 1
   ↓
Extraer
   ↓
¿Existe página siguiente?
   │
   ├── Sí → Página 2
   │          ↓
   │       Extraer
   │          ↓
   │       continuar
   │
   └── No → finalizar
```

Agregar protección contra ciclos infinitos.

---

# 11. Modelo de datos

La entidad principal será:

## Vacante

Campos recomendados:

```text
id
id_externo
fecha_publicacion
fecha_cierre
secretaria_educacion
departamento
municipio
institucion_educativa
sede
cargo
area
nivel
tipo_vinculacion
tipo_vacante
priorizacion
estado
url
fecha_primera_deteccion
fecha_ultima_consulta
activa
hash_registro
```

No todos los campos deben asumirse existentes.

El parser debe adaptarse a los campos realmente publicados por el portal.

---

# 12. Identificación única

Prioridad:

### Nivel 1

Utilizar el identificador oficial de la vacante si el portal lo proporciona.

### Nivel 2

Utilizar el enlace o URL de la vacante.

### Nivel 3

Construir un hash a partir de:

```text
Secretaría
Departamento
Municipio
Institución
Cargo
Área
Fecha publicación
Fecha cierre
```

Ejemplo:

```python
hash_registro = sha256(
    datos_normalizados.encode("utf-8")
).hexdigest()
```

El identificador debe ser estable entre ejecuciones.

---

# 13. Detección de nuevas oportunidades

Lógica:

```python
actuales = consultar_portal()

historicas = consultar_base_datos()

nuevas = actuales[
    ~actuales["id_externo"].isin(
        historicas["id_externo"]
    )
]
```

Pero no depender exclusivamente del nombre o descripción.

Utilizar el identificador oficial cuando exista.

---

# 14. Estados

Cada oportunidad puede tener:

```text
NUEVA
ACTIVA
ACTUALIZADA
CERRADA
DESAPARECIDA
```

Una vacante debe considerarse **nueva** solamente cuando no exista previamente en el histórico.

Una modificación de una vacante existente debe clasificarse como:

```text
ACTUALIZADA
```

---

# 15. Histórico

Conservar todas las consultas.

No sobrescribir información histórica.

Registrar:

```text
id_vacante
fecha_consulta
estado
datos
```

Esto permitirá posteriormente analizar:

* número de vacantes publicadas;
* municipios con mayor número de oportunidades;
* áreas más demandadas;
* frecuencia de publicación;
* tiempo promedio de vigencia;
* evolución histórica.

---

# 16. Filtros

La consulta inicial debe ser:

```text
Departamento: TODOS
Municipio: TODOS
Secretaría: TODAS
Área: TODAS
Cargo: TODOS
Tipo: TODOS
```

Después permitir filtros opcionales.

Ejemplo:

```python
filtros = {
    "departamento": None,
    "municipio": None,
    "secretaria": None,
    "area": None,
    "cargo": None
}
```

`None` significa:

> No aplicar filtro.

---

# 17. Ejemplos de filtros

### Todas las oportunidades

```python
filtros = {}
```

### Departamento

```python
filtros = {
    "departamento": "Caldas"
}
```

### Municipio

```python
filtros = {
    "municipio": "Manizales"
}
```

### Área

```python
filtros = {
    "area": "Tecnología e Informática"
}
```

### Combinación

```python
filtros = {
    "departamento": "Caldas",
    "municipio": "Manizales",
    "area": "Tecnología e Informática"
}
```

---

# 18. Exportación

Generar:

```text
data/exportaciones/
```

Archivos:

```text
vacantes_actuales.xlsx
vacantes_nuevas.xlsx
vacantes_actualizadas.xlsx
historico_vacantes.xlsx
```

El archivo de novedades debe contener como mínimo:

```text
Fecha detección
Fecha publicación
Departamento
Municipio
Secretaría
Institución
Cargo
Área
Fecha cierre
URL
Estado
```

---

# 19. Interfaz

En una segunda fase construir una interfaz web con:

**Streamlit** o **Dash**.

Vista principal:

```text
┌─────────────────────────────────────────────┐
│       MONITOR SISTEMA MAESTRO               │
├─────────────────────────────────────────────┤
│ Última consulta: 01/09/2026 14:00           │
│                                             │
│ Vacantes activas       1.245                │
│ Nuevas hoy                37                │
│ Actualizadas              12                │
│                                             │
├─────────────────────────────────────────────┤
│ Departamento [TODOS ▼]                     │
│ Municipio    [TODOS ▼]                     │
│ Área         [TODAS ▼]                     │
│ Cargo        [TODOS ▼]                     │
│                                             │
│              [BUSCAR]                       │
├─────────────────────────────────────────────┤
│ Nuevas oportunidades                       │
│                                             │
│ Municipio | Área | Cargo | Cierre | Ver    │
│ Manizales | ...  | ...   | ...    | 🔗     │
└─────────────────────────────────────────────┘
```

---

# 20. Notificaciones

Implementar inicialmente:

```text
Email
```

Después:

```text
Telegram
WhatsApp
```

No enviar todas las vacantes en cada ejecución.

Enviar solamente:

```text
NUEVAS VACANTES
```

Ejemplo:

```text
🚨 Nuevas oportunidades Sistema Maestro

Se detectaron 8 nuevas vacantes.

Caldas
- Manizales: 3
- Villamaría: 2
- Chinchiná: 1
- La Dorada: 2

Áreas:
- Primaria: 3
- Matemáticas: 2
- Inglés: 1
- Tecnología: 2

Consulta el detalle en el sistema.
```

---

# 21. Frecuencia

Permitir ejecución manual:

```bash
python main.py
```

Y ejecución automática mediante:

### Windows

Task Scheduler.

### Linux

Cron.

### Docker

Contenedor con proceso programado.

La frecuencia debe ser configurable.

---

# 22. Manejo de errores

El sistema debe controlar:

```text
Timeout
HTTP errors
Portal no disponible
Cambios en HTML
Cambios en selectores
Resultados vacíos
Paginación defectuosa
Duplicados
Errores de escritura
Errores de conexión
```

Nunca detener definitivamente el monitor por una vacante defectuosa.

Registrar errores en:

```text
logs/sistema_maestro.log
```

---

# 23. Detección de cambios del portal

Debido a que el portal puede cambiar su estructura, evitar selectores excesivamente frágiles.

Preferir:

```python
get_by_role()
get_by_text()
get_by_label()
```

antes que selectores CSS basados exclusivamente en posiciones.

Ejemplo frágil:

```python
page.locator(
    "#form\\:tabla\\:0\\:campo"
)
```

Preferible:

```python
page.get_by_text(
    "Buscar"
)
```

cuando sea posible.

---

# 24. Respeto por el portal

El sistema debe:

* utilizar una frecuencia razonable;
* evitar solicitudes innecesarias;
* no intentar evadir mecanismos de seguridad;
* no generar tráfico excesivo;
* respetar las condiciones de uso aplicables;
* almacenar localmente los resultados ya consultados.

Implementar caché cuando sea posible.

---

# 25. Seguridad

No almacenar:

```text
contraseñas
tokens
credenciales
cookies sensibles
```

en el repositorio.

Utilizar:

```text
.env
```

y agregarlo a:

```text
.gitignore
```

---

# 26. Pruebas

Crear pruebas para:

### Parser

Comprobar que una tabla HTML conocida se convierta correctamente.

### Normalizador

Comprobar:

```text
" Tecnología e Informática "
→
"tecnologia_e_informatica"
```

### Detector

Dado:

```text
Histórico = [1,2,3]
Actuales = [2,3,4,5]
```

resultado esperado:

```text
Nuevas = [4,5]
```

### Duplicados

Comprobar que una misma vacante no se registre dos veces.

---

# 27. Flujo completo

```text
INICIO
  │
  ▼
Cargar configuración
  │
  ▼
Conectar al Sistema Maestro
  │
  ▼
Ejecutar búsqueda general
  │
  ▼
Obtener página 1
  │
  ▼
Extraer oportunidades
  │
  ▼
¿Página siguiente?
  │
 ┌┴──────────────┐
Sí               No
 │                │
 ▼                ▼
Siguiente       Normalizar
página             │
 │                  ▼
 └──────────────► Generar ID
                    │
                    ▼
              Consultar histórico
                    │
                    ▼
              Detectar novedades
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       Nuevas              Sin nuevas
          │                   │
          ▼                   │
      Guardar                 │
          │                   │
          ▼                   │
     Notificar                │
          │                   │
          └─────────┬─────────┘
                    ▼
              Actualizar BD
                    │
                    ▼
                  FIN
```

---

# 28. Criterios de aceptación

La aplicación será considerada funcional cuando:

* [ ] Acceda al portal Sistema Maestro.
* [ ] Ejecute una búsqueda general.
* [ ] Obtenga los resultados reales.
* [ ] Recorra todas las páginas.
* [ ] No limite inicialmente por municipio.
* [ ] No limite inicialmente por departamento.
* [ ] No limite inicialmente por área.
* [ ] No limite inicialmente por Secretaría.
* [ ] Identifique correctamente una vacante.
* [ ] Genere un identificador estable.
* [ ] Guarde el histórico.
* [ ] Detecte nuevas publicaciones.
* [ ] Evite duplicados.
* [ ] Exporte a Excel.
* [ ] Registre errores.
* [ ] Permita filtros posteriores.
* [ ] Permita ejecución automática.
* [ ] Prepare el sistema para notificaciones.

---

# 29. Regla principal para el agente desarrollador

Antes de escribir el scraper definitivo:

1. Abrir el portal.
2. Inspeccionar el formulario.
3. Identificar todos los filtros.
4. Identificar el botón de búsqueda.
5. Ejecutar manualmente una consulta.
6. Observar cómo se cargan los resultados.
7. Identificar la estructura de la tabla.
8. Identificar el mecanismo de paginación.
9. Identificar si existe un identificador único.
10. Solo después implementar los selectores definitivos.

**No asumir la estructura del portal.**

El código debe adaptarse a la estructura real observada en la aplicación web.

---

# 30. Evolución futura

La arquitectura debe permitir incorporar posteriormente:

```text
                  SISTEMA MAESTRO
                         │
                         ▼
                  Motor de extracción
                         │
                         ▼
                  Base histórica
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
       Dashboard       API            Alertas
          │                              │
          ▼                              ▼
      Power BI                    Email/WhatsApp
```

Y posteriormente incorporar IA para:

* clasificar oportunidades;
* resumir convocatorias;
* identificar oportunidades según perfil;
* priorizar vacantes;
* detectar cambios;
* generar resúmenes diarios;
* responder consultas en lenguaje natural.

La IA debe utilizarse **después de resolver correctamente la extracción y persistencia de los datos**. No utilizar IA como sustituto del mecanismo de captura de información.

---

# 31. Resultado esperado

El producto final debe funcionar como un:

> **Monitor automático de oportunidades del Sistema Maestro del Ministerio de Educación Nacional.**

Debe poder responder:

> **“Desde la última consulta, ¿qué nuevas oportunidades aparecieron en todo Colombia?”**

y mostrar:

```text
Total nuevas: XX

Departamento
Municipio
Secretaría
Institución
Área
Cargo
Fecha publicación
Fecha cierre
Enlace
```

sin exigir que el usuario configure previamente un municipio o departamento.
