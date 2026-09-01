# Integración en la Nube con Google Apps Script y Google Sheets

Este módulo permite ejecutar el **Monitor de Vacantes del Sistema Maestro** directamente en la infraestructura gratuita de Google (en la nube 24/7, sin depender de que tu computadora esté encendida), almacenar el histórico en una Hoja de Cálculo de Google Sheets y recibir notificaciones instantáneas en tu correo Gmail.

---

## 🚀 Guía de Configuración en 3 Minutos

### 1. Crear la Hoja de Cálculo
1. Ve a [Google Sheets](https://sheets.new) y crea una nueva hoja de cálculo.
2. Nómbrala: `Monitor Sistema Maestro MEN`.

### 2. Abrir el Editor de Apps Script
1. En el menú superior de Google Sheets, ve a **Extensiones** > **Apps Script**.
2. Borra el contenido por defecto del editor.
3. Copia todo el código del archivo [`Codigo.gs`](./Codigo.gs) y pégalo en el editor.
4. Presiona el botón de **Guardar** (ícono de disquete o `Ctrl + S`).

### 3. Ejecutar la Primera Consulta Manualmente
1. En la barra superior del editor, selecciona la función `ejecutarMonitorSistemaMaestro`.
2. Haz clic en **Ejecutar**.
3. Google solicitará permisos para acceder a Google Sheets, conectarse a servicios externos (`UrlFetchApp`) y enviar correos (`GmailApp`). Concede los permisos.
4. Observa el Registro de ejecución: en pocos segundos verás cómo se extraen las vacantes del portal del Ministerio y se crean automáticamente las pestañas en tu Google Sheet:
   - `Vacantes_Actuales`: Todas las vacantes vigentes en el país.
   - `Novedades_Nuevas`: Únicamente las nuevas oportunidades detectadas.
   - `Historico`: Registro acumulado histórico con fecha de detección.

### 4. Activar la Ejecución Automática (Cada 15 min, 30 min o 1 hora)
En el selector de funciones de Apps Script, elige la frecuencia deseada y haz clic en **Ejecutar**:
* `activarCada15Minutos`: Se ejecuta automáticamente **cada 15 minutos**.
* `activarCada30Minutos`: Se ejecuta automáticamente **cada 30 minutos** (recomendado).
* `activarCada1Hora`: Se ejecuta automáticamente **cada 1 hora**.

> **Nota visual:** También puedes ir al menú lateral izquierdo de Apps Script, hacer clic en el ícono de **Activadores (reloj)** > **Añadir activador**:
> * Función a ejecutar: `ejecutarMonitorSistemaMaestro`
> * Tipo de evento: `Según tiempo`
> * Frecuencia: `Temporizador de minutos` (ej: cada 15 o 30 minutos) o `Temporizador de horas`.


---

## 🌐 Publicar como API Web (Opcional)

Si deseas conectar tu Google Sheet directamente con el dashboard de GitHub Pages:
1. En Apps Script, haz clic en el botón azul **Implementar** (arriba a la derecha) > **Nueva implementación**.
2. Selecciona el tipo: **Aplicación web**.
3. En *Quién tiene acceso*, elige: **Cualquier usuario**.
4. Haz clic en **Implementar** y copia la URL proporcionada. Esa URL responderá con un JSON de las vacantes activas en tiempo real.
