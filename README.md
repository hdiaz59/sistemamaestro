# 🇨🇴 Monitor de Vacantes — Sistema Maestro MEN

> **Sistema automatizado e inteligente para la consulta, detección de novedades, generación de histórico y visualización pública de las oportunidades docentes del portal oficial Sistema Maestro del Ministerio de Educación Nacional de Colombia.**

Fuente oficial monitoreada: [sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml](https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml)

---

## 🌟 Características Principales

* ⚡ **Consulta General Automatizada:** Extrae todas las vacantes publicadas en el país recorriendo automáticamente todas las páginas sin limitar previamente por departamento o municipio.
* 🔍 **Detección Inteligente de Novedades:** Compara cada consulta contra la base histórica e identifica con precisión vacantes **`NUEVAS`**, **`ACTUALIZADAS`** (cambio en número de postulados) y **`CERRADAS`**.
* 🔑 **Identificador Único Determinista:** Genera un hash SHA-256 estable para cada vacante a partir de Secretaría, Departamento, Municipio, Cargo, Área, Priorización y Cierre.
* 📊 **Dashboard Web Interactivo para GitHub Pages (`github.io`):**
  * Diseño moderno con Glassmorphism, Modo Oscuro / Claro y tipografía Google Fonts.
  * Tarjetas KPI de vacantes activas, nuevas hoy, departamentos y municipios con ofertas.
  * Filtros en tiempo real por Departamento, Municipio, Área, Cargo y búsqueda libre.
  * Vista de Cuadrícula (Tarjetas con temporizador de cuenta regresiva) y Vista de Tabla con ordenamiento.
  * Exportación directa en el cliente a **Excel (.xlsx)**, **CSV (.csv)** y **JSON (.json)**.
* ☁️ **Automatización en la Nube con Google Apps Script (`google scripts`):**
  * Ejecución 100% en la nube de Google sin depender de que tu computadora esté encendida.
  * Almacenamiento histórico en **Google Sheets** (pestañas `Vacantes_Actuales`, `Novedades_Nuevas`, `Historico`).
  * Alertas instantáneas por correo electrónico vía **Gmail**.
  * Endpoint REST API en formato JSON.
* 🤖 **CI/CD con GitHub Actions:**
  * Flujo de trabajo programado (`cron: '0 */2 * * *'`) que actualiza los datos automáticamente y despliega a **GitHub Pages**.
* 📁 **Exportaciones Locales y Persistencia:**
  * Base de datos SQLite (`data/sistema_maestro.db`).
  * Archivos Excel en `data/exportaciones/`: `vacantes_actuales.xlsx`, `vacantes_nuevas.xlsx`, `historico_vacantes.xlsx`.
  * Snapshots históricos con marca de tiempo en `data/historico/`.

---

## 📂 Estructura del Proyecto

```text
Sistema Maestro/
│
├── app/                           # Motor central en Python
│   ├── __init__.py
│   ├── config.py                  # Configuración y rutas del sistema
│   ├── scraper.py                 # Extractor HTTP JSF/AJAX y fallback Playwright
│   ├── parser.py                  # Extractor de tarjetas HTML y XML CDATA
│   ├── normalizer.py              # Limpieza, reparación de tildes y hash SHA-256
│   ├── detector.py                # Comparador de novedades e histórico
│   ├── database.py                # Modelos SQLAlchemy y SQLite
│   ├── exporter.py                # Generador de Excel (.xlsx) y JSONs para la web
│   ├── notifier.py                # Despachador de alertas Email y Telegram
│   └── logger.py                  # Sistema de logs con soporte UTF-8
│
├── docs/                          # Aplicación Web para GitHub Pages (github.io)
│   ├── index.html                 # Estructura del Dashboard interactivo
│   ├── style.css                  # Sistema de diseño, Glassmorphism y temas
│   ├── app.js                     # Lógica reactiva de filtros, exportación y modales
│   └── data/                      # Datos JSON generados automáticamente
│       ├── vacantes_actuales.json
│       ├── novedades.json
│       └── stats.json
│
├── gas/                           # Módulo Google Apps Script (google scripts)
│   ├── Codigo.gs                  # Script completo para Google Sheets & Gmail
│   └── README.md                  # Guía de configuración en 3 minutos
│
├── .github/workflows/
│   └── monitor.yml                # Flujo de GitHub Actions para ejecución y despliegue
│
├── data/
│   ├── exportaciones/             # Archivos Excel exportados
│   ├── historico/                 # Snapshots JSON históricos
│   └── sistema_maestro.db         # Base de datos SQLite
│
├── tests/                         # Pruebas unitarias
│   ├── test_normalizer.py
│   ├── test_parser.py
│   ├── test_detector.py
│   └── test_database.py
│
├── main.py                        # Punto de entrada de ejecución local
├── requirements.txt               # Dependencias Python
├── .env.example                   # Plantilla de variables de entorno
└── README.md                      # Documentación
```

---

## 🚀 Instalación y Uso Local

### 1. Requisitos Previos
* Python 3.10 o superior.

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

*(Opcional si deseas soporte para renderizado Playwright):*
```bash
playwright install chromium
```

### 3. Ejecutar el Monitor
```bash
python main.py
```

Al ejecutar `main.py`:
1. Consulta el portal oficial Sistema Maestro.
2. Identifica todas las vacantes en Colombia.
3. Compara contra el histórico en `data/sistema_maestro.db`.
4. Muestra el resumen en la terminal.
5. Genera los archivos Excel en `data/exportaciones/`.
6. Actualiza los JSON de la web en `docs/data/`.

---

## 🌐 Publicación en GitHub Pages (`github.io`)

1. Sube este repositorio a tu cuenta de **GitHub**.
2. Ve a **Settings** > **Pages** en tu repositorio:
   * **Source**: `GitHub Actions` (o `Deploy from a branch` seleccionando la rama `main` y la carpeta `/docs`).
3. El flujo `.github/workflows/monitor.yml` se ejecutará cada 2 horas automáticamente, extrayendo las últimas ofertas, actualizando los datos y publicando el sitio en:
   ```text
   https://<tu-usuario>.github.io/<tu-repositorio>/
   ```

---

## ☁️ Integración con Google Apps Script (`google scripts`)

Para ejecutar el monitor en la nube sin costo y sin necesidad de tener tu equipo encendido:
1. Abre [Google Sheets](https://sheets.new) y crea una hoja llamada `Monitor Sistema Maestro MEN`.
2. Ve a **Extensiones** > **Apps Script**.
3. Pega el código de [`gas/Codigo.gs`](./gas/Codigo.gs).
4. Ejecuta la función `configurarDisparadorAutomatico` para que se ejecute periódicamente y te envíe alertas a tu correo Gmail.
5. Consulta la guía detallada en [`gas/README.md`](./gas/README.md).

---

## 🧪 Ejecución de Pruebas Unitarias

```bash
python -m unittest discover tests
```

---

## 📄 Licencia

Desarrollado con fines informativos y de acceso transparente a las oportunidades docentes oficiales en Colombia.
