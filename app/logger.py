"""
Módulo de Registro y Logging
Configura logs formateados a consola y a archivo logs/sistema_maestro.log con soporte seguro UTF-8 en Windows.
"""
import io
import logging
import sys
from app.config import LOGS_DIR, LOG_LEVEL

def setup_logger(name: str = "sistema_maestro") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler Consola con stream UTF-8 seguro
    try:
        if sys.platform.startswith("win"):
            # Envolver stdout para UTF-8 seguro
            stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
            console_handler = logging.StreamHandler(stream)
        else:
            console_handler = logging.StreamHandler(sys.stdout)
    except Exception:
        console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler Archivo UTF-8
    log_file = LOGS_DIR / "sistema_maestro.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
