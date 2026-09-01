"""
Módulo de Notificaciones
Envía alertas por Correo Electrónico (SMTP) y Telegram cuando se detectan nuevas vacantes.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import requests
from app.config import (
    SMTP_ENABLED, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    NOTIFICATION_RECIPIENTS, TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)
from app.logger import logger

def generar_html_correo(nuevas: List[Dict[str, Any]]) -> str:
    """Construye un cuerpo HTML estético para la alerta por correo."""
    filas = ""
    for v in nuevas:
        filas += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px; font-weight: bold; color: #1e293b;">{v.get('departamento', '')} - {v.get('municipio', '')}</td>
            <td style="padding: 10px; color: #334155;">{v.get('cargo', '')}</td>
            <td style="padding: 10px; color: #2563eb; font-weight: 500;">{v.get('area', '')}</td>
            <td style="padding: 10px; color: #dc2626; font-size: 13px;">{v.get('fecha_cierre_texto', '')}</td>
            <td style="padding: 10px;">
                <a href="{v.get('url_portal', 'https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml')}" 
                   style="background-color: #2563eb; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; display: inline-block;">
                   Ver Portal
                </a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 750px; margin: 0 auto; background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); padding: 24px; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 22px;">🚨 Nuevas Vacantes Detectadas</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Monitor Automático - Sistema Maestro MEN Colombia</p>
            </div>
            <div style="padding: 24px;">
                <p style="font-size: 15px; color: #475569;">
                    Se han identificado <strong>{len(nuevas)} nueva(s) oportunidad(es) docente(s)</strong> en el Sistema Maestro desde la última consulta:
                </p>
                <div style="overflow-x: auto; margin-top: 16px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                        <thead>
                            <tr style="background-color: #f1f5f9; color: #475569; font-size: 12px; text-transform: uppercase;">
                                <th style="padding: 10px;">Ubicación</th>
                                <th style="padding: 10px;">Cargo</th>
                                <th style="padding: 10px;">Área</th>
                                <th style="padding: 10px;">Cierre</th>
                                <th style="padding: 10px;">Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filas}
                        </tbody>
                    </table>
                </div>
            </div>
            <div style="background-color: #f8fafc; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                Generado automáticamente por el Monitor de Vacantes Sistema Maestro.
            </div>
        </div>
    </body>
    </html>
    """

def enviar_notificacion_correo(nuevas: List[Dict[str, Any]]):
    """Envía la alerta por correo electrónico mediante SMTP."""
    if not SMTP_ENABLED or not NOTIFICATION_RECIPIENTS or not SMTP_USER:
        return

    logger.info(f"Enviando alerta de correo a {len(NOTIFICATION_RECIPIENTS)} destinatarios...")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 {len(nuevas)} Nueva(s) Vacante(s) en Sistema Maestro MEN"
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(NOTIFICATION_RECIPIENTS)

        html_content = generar_html_correo(nuevas)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, NOTIFICATION_RECIPIENTS, msg.as_string())

        logger.info("Notificación por correo enviada exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar correo electrónico: {e}")

def enviar_notificacion_telegram(nuevas: List[Dict[str, Any]]):
    """Envía la alerta a un canal/chat de Telegram mediante Bot API."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    logger.info("Enviando alerta a Telegram...")
    try:
        texto = f"🚨 *Nuevas Oportunidades en Sistema Maestro*\n\n"
        texto += f"Se detectaron *{len(nuevas)}* nuevas publicaciones:\n\n"
        
        for i, v in enumerate(nuevas[:10]):  # Limitar a las primeras 10 en Telegram
            depto = v.get("departamento", "")
            mpio = v.get("municipio", "")
            area = v.get("area", "")
            cargo = v.get("cargo", "")
            cierre = v.get("fecha_cierre_texto", "")
            texto += f"📌 *{depto} - {mpio}*\n"
            texto += f"   • Área: {area}\n"
            texto += f"   • Cargo: {cargo}\n"
            texto += f"   • Cierre: {cierre}\n\n"

        if len(nuevas) > 10:
            texto += f"_...y {len(nuevas) - 10} vacantes más en el sistema._\n\n"

        texto += "🔗 [Ver portal Sistema Maestro](https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml)"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": texto,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        logger.info("Notificación de Telegram enviada exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar mensaje por Telegram: {e}")

def despachar_notificaciones(nuevas: List[Dict[str, Any]]):
    """Despacha las alertas configuradas si existen nuevas vacantes."""
    if not nuevas:
        return
    
    if SMTP_ENABLED:
        enviar_notificacion_correo(nuevas)
    if TELEGRAM_ENABLED:
        enviar_notificacion_telegram(nuevas)
