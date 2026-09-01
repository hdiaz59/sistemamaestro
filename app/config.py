"""
Módulo de Configuración Central
Carga variables de entorno y define rutas del proyecto.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Directorios de datos
DATA_DIR = BASE_DIR / "data"
HISTORICO_DIR = DATA_DIR / "historico"
EXPORTACIONES_DIR = DATA_DIR / "exportaciones"
DOCS_DIR = BASE_DIR / "docs"
DOCS_DATA_DIR = DOCS_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Asegurar que existan todos los directorios
for folder in [DATA_DIR, HISTORICO_DIR, EXPORTACIONES_DIR, DOCS_DIR, DOCS_DATA_DIR, LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# URL del Sistema Maestro
SISTEMA_MAESTRO_URL = os.getenv(
    "SISTEMA_MAESTRO_URL",
    "https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml"
)

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'sistema_maestro.db'}")

# Configuración del Scraper
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "100"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# Notificaciones por Correo
SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() in ("true", "1", "yes")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFICATION_RECIPIENTS = [
    r.strip() for r in os.getenv("NOTIFICATION_RECIPIENTS", "").split(",") if r.strip()
]

# Notificaciones por Telegram
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() in ("true", "1", "yes")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Log Level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
