/**
 * ==============================================================================
 * MONITOR SISTEMA MAESTRO MEN — GOOGLE APPS SCRIPT
 * ==============================================================================
 * Este script se ejecuta 100% en la nube de Google de forma gratuita.
 * Consulta automáticamente el portal Sistema Maestro, almacena las vacantes en
 * Google Sheets, detecta novedades respecto a consultas anteriores y envía
 * alertas por correo (Gmail) de forma automática.
 *
 * Configuración:
 * 1. Crea una Hoja de Cálculo en Google Drive.
 * 2. Ve a Extensiones > Apps Script.
 * 3. Pega este código en el editor y guarda.
 * 4. Ejecuta la función 'configurarDisparadorAutomatico' para activar la consulta cada 2 horas.
 * ==============================================================================
 */

const CONFIG = {
  URL_SISTEMA_MAESTRO: "https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml",
  USER_AGENT: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  NOTIFICAR_CORREO: true,
  CORREO_DESTINO: "", // Si se deja vacío, envía al correo del propietario de la cuenta de Google
  HOJA_ACTUALES: "Vacantes_Actuales",
  HOJA_NOVEDADES: "Novedades_Nuevas",
  HOJA_HISTORICO: "Historico",
};

/**
 * Función principal que ejecuta la consulta y detección.
 */
function ejecutarMonitorSistemaMaestro() {
  Logger.log("=== INICIANDO MONITOR SISTEMA MAESTRO MEN (GOOGLE APPS SCRIPT) ===");
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  inicializarHojas(ss);
  
  // 1. Obtener histórico previo para comparación
  const historicoPrevio = obtenerMapaHistorico(ss);
  Logger.log("Vacantes en histórico previo: " + Object.keys(historicoPrevio).length);
  
  // 2. Extraer vacantes desde el portal oficial
  const vacantesActuales = extraerVacantesDelPortal();
  Logger.log("Total vacantes extraídas del portal: " + vacantesActuales.length);
  
  if (vacantesActuales.length === 0) {
    Logger.log("No se obtuvieron vacantes en esta ejecución.");
    return;
  }
  
  // 3. Detectar novedades
  const nuevas = [];
  const actualizadas = [];
  
  vacantesActuales.forEach(function(v) {
    if (!historicoPrevio[v.id_vacante]) {
      nuevas.push(v);
    } else {
      const prev = historicoPrevio[v.id_vacante];
      if (prev.postulados !== v.postulados) {
        actualizadas.push(v);
      }
    }
  });
  
  Logger.log("Detección: " + vacantesActuales.length + " activas | " + nuevas.length + " NUEVAS | " + actualizadas.length + " actualizadas");
  
  // 4. Guardar datos en Google Sheets
  guardarEnHojas(ss, vacantesActuales, nuevas);
  
  // 5. Enviar alertas por correo si hay nuevas
  if (nuevas.length > 0 && CONFIG.NOTIFICAR_CORREO) {
    enviarAlertaCorreoGmail(nuevas);
  }
  
  Logger.log("=== MONITOREO FINALIZADO EXITOSAMENTE ===");
}

/**
 * Extrae las vacantes recorriendo las páginas del portal mediante UrlFetchApp.
 */
function extraerVacantesDelPortal() {
  const headers = {
    "User-Agent": CONFIG.USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7"
  };
  
  // Paso 1: GET Página 1
  const response = UrlFetchApp.fetch(CONFIG.URL_SISTEMA_MAESTRO, {
    headers: headers,
    muteHttpExceptions: true
  });
  
  const html = response.getContentText();
  const cookies = response.getAllHeaders()["Set-Cookie"] || "";
  
  const viewState = extraerViewState(html);
  const totalPaginas = extraerTotalPaginas(html);
  Logger.log("Página 1 obtenida. Total de páginas: " + totalPaginas + " | ViewState: " + (viewState ? "OK" : "No encontrado"));
  
  const todasLasVacantes = [];
  const idsVistos = {};
  
  // Parsear P1
  const vacsP1 = parsearTarjetasTexto(html);
  vacsP1.forEach(function(v) {
    if (!idsVistos[v.id_vacante]) {
      idsVistos[v.id_vacante] = true;
      todasLasVacantes.push(v);
    }
  });
  
  // Paso 2: POST AJAX para páginas siguientes
  if (totalPaginas > 1 && viewState) {
    const headersAjax = {
      "User-Agent": CONFIG.USER_AGENT,
      "Accept": "application/xml, text/xml, */*; q=0.01",
      "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
      "Faces-Request": "partial/ajax",
      "X-Requested-With": "XMLHttpRequest",
      "Cookie": cookies
    };
    
    for (let p = 2; p <= totalPaginas; p++) {
      const firstIdx = (p - 1) * 6;
      const payload = {
        "javax.faces.partial.ajax": "true",
        "javax.faces.source": "form-busqueda:tabla-vacantes",
        "javax.faces.partial.execute": "form-busqueda:tabla-vacantes",
        "javax.faces.partial.render": "form-busqueda:tabla-vacantes",
        "form-busqueda:tabla-vacantes": "form-busqueda:tabla-vacantes",
        "form-busqueda:tabla-vacantes_pagination": "true",
        "form-busqueda:tabla-vacantes_first": String(firstIdx),
        "form-busqueda:tabla-vacantes_rows": "6",
        "form-busqueda:tabla-vacantes_skipChildren": "true",
        "form-busqueda:tabla-vacantes_encodeFeature": "true",
        "form-busqueda": "form-busqueda",
        "javax.faces.ViewState": viewState
      };
      
      try {
        const resAjax = UrlFetchApp.fetch(CONFIG.URL_SISTEMA_MAESTRO, {
          method: "post",
          headers: headersAjax,
          payload: payload,
          muteHttpExceptions: true
        });
        
        const xmlText = resAjax.getContentText();
        const vacsP = parsearTarjetasTexto(xmlText);
        vacsP.forEach(function(v) {
          if (!idsVistos[v.id_vacante]) {
            idsVistos[v.id_vacante] = true;
            todasLasVacantes.push(v);
          }
        });
        
        Utilities.sleep(400); // Pausa de cortesía
      } catch (err) {
        Logger.log("Error al paginar página " + p + ": " + err);
      }
    }
  }
  
  return todasLasVacantes;
}

/**
 * Extrae ViewState mediante Regex.
 */
function extraerViewState(html) {
  const match = html.match(/name=["']javax\.faces\.ViewState["'][^>]*value=["']([^"']+)["']/);
  if (match) return match[1];
  const match2 = html.match(/<update id="[^"]*javax\.faces\.ViewState[^"]*"><!\[CDATA\[(.*?)\]\]><\/update>/);
  return match2 ? match2[1] : "";
}

/**
 * Extrae número de páginas de '(1 of 4)'.
 */
function extraerTotalPaginas(html) {
  const match = html.match(/\((\d+)\s+of\s+(\d+)\)/i);
  return match ? parseInt(match[2], 10) : 1;
}

/**
 * Parsea el texto de las tarjetas de vacantes.
 */
function parsearTarjetasTexto(htmlOXml) {
  const vacantes = [];
  // Dividir por bloques de panel de vacante
  const bloques = htmlOXml.split(/ui-datagrid-column/gi);
  
  for (let i = 1; i < bloques.length; i++) {
    const bloque = bloques[i];
    
    // Extraer campos
    const cargoMatch = bloque.match(/Cargo\s+([^<|]+)/i);
    const postMatch = bloque.match(/Postulados:\s*(\d+)/i);
    const priorMatch = bloque.match(/Tipo\s+Priorizaci[^:]*:\s*([^<|]+)/i);
    const cierreMatch = bloque.match(/Cierre\s+vacante:\s*([^<|]+)/i);
    const areaMatch = bloque.match(/[ÁA]rea:\s*([^<|]+)/i);
    const secMatch = bloque.match(/Secretar[^:]*:\s*([^<|]+)/i);
    const zonaMatch = bloque.match(/Zona:\s*([^<|]+)/i);
    const deptoMatch = bloque.match(/Departamento:\s*([^<|]+)/i);
    const mpioMatch = bloque.match(/Municipio:\s*([^<|]+)/i);
    
    if (cargoMatch || mpioMatch || areaMatch) {
      const v = {
        cargo: limpiarTexto(cargoMatch ? cargoMatch[1] : "Docente de Aula"),
        postulados: postMatch ? parseInt(postMatch[1], 10) : 0,
        tipo_priorizacion: limpiarTexto(priorMatch ? priorMatch[1] : "Vacantes Generales"),
        cierre_vacante: limpiarTexto(cierreMatch ? cierreMatch[1] : ""),
        area: limpiarTexto(areaMatch ? areaMatch[1] : "Sin Área"),
        secretaria: limpiarTexto(secMatch ? secMatch[1] : ""),
        zona: limpiarTexto(zonaMatch ? zonaMatch[1] : ""),
        departamento: limpiarTexto(deptoMatch ? deptoMatch[1] : ""),
        municipio: limpiarTexto(mpioMatch ? mpioMatch[1] : ""),
        url_portal: "https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml"
      };
      
      v.id_vacante = generarHashVacante(v);
      vacantes.push(v);
    }
  }
  
  return vacantes;
}

function limpiarTexto(str) {
  if (!str) return "";
  return str.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
}

function generarHashVacante(v) {
  const clave = [
    (v.secretaria || "").toLowerCase().trim(),
    (v.departamento || "").toLowerCase().trim(),
    (v.municipio || "").toLowerCase().trim(),
    (v.cargo || "").toLowerCase().trim(),
    (v.area || "").toLowerCase().trim(),
    (v.tipo_priorizacion || "").toLowerCase().trim(),
    (v.cierre_vacante || "").toLowerCase().trim()
  ].join("|");
  
  const rawDigest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, clave, Utilities.Charset.UTF_8);
  let hashStr = "";
  for (let i = 0; i < rawDigest.length; i++) {
    let byteVal = rawDigest[i];
    if (byteVal < 0) byteVal += 256;
    let hexStr = byteVal.toString(16);
    if (hexStr.length === 1) hexStr = "0" + hexStr;
    hashStr += hexStr;
  }
  return hashStr;
}

/**
 * Inicializa las pestañas en Google Sheets.
 */
function inicializarHojas(ss) {
  const cabeceras = [
    "Estado", "Departamento", "Municipio", "Secretaría", "Cargo",
    "Área", "Priorización", "Postulados", "Cierre Vacante",
    "Primera Detección", "Última Consulta", "Enlace Portal", "ID Vacante"
  ];
  
  [CONFIG.HOJA_ACTUALES, CONFIG.HOJA_NOVEDADES, CONFIG.HOJA_HISTORICO].forEach(function(nombre) {
    let sheet = ss.getSheetByName(nombre);
    if (!sheet) {
      sheet = ss.insertSheet(nombre);
      sheet.appendRow(cabeceras);
      sheet.getRange(1, 1, 1, cabeceras.length).setBackground("#1e3a8a").setFontColor("#ffffff").setFontWeight("bold");
      sheet.setFrozenRows(1);
    }
  });
}

/**
 * Lee el histórico de la pestaña Historico para comparación.
 */
function obtenerMapaHistorico(ss) {
  const sheet = ss.getSheetByName(CONFIG.HOJA_HISTORICO);
  if (!sheet) return {};
  
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return {};
  
  const mapa = {};
  for (let i = 1; i < data.length; i++) {
    const fila = data[i];
    const idVacante = fila[12]; // Columna ID Vacante
    if (idVacante) {
      mapa[idVacante] = {
        estado: fila[0],
        postulados: fila[7]
      };
    }
  }
  return mapa;
}

/**
 * Guarda los resultados en las pestañas de Google Sheets.
 */
function guardarEnHojas(ss, vacantesActuales, nuevas) {
  const ahora = Utilities.formatDate(new Date(), "GMT-5", "yyyy-MM-dd HH:mm:ss");
  
  // 1. Actualizar Hoja 'Vacantes_Actuales'
  const sheetAct = ss.getSheetByName(CONFIG.HOJA_ACTUALES);
  sheetAct.clearContents();
  const cabeceras = [
    "Estado", "Departamento", "Municipio", "Secretaría", "Cargo",
    "Área", "Priorización", "Postulados", "Cierre Vacante",
    "Primera Detección", "Última Consulta", "Enlace Portal", "ID Vacante"
  ];
  sheetAct.appendRow(cabeceras);
  sheetAct.getRange(1, 1, 1, cabeceras.length).setBackground("#1e3a8a").setFontColor("#ffffff").setFontWeight("bold");
  
  const filasAct = vacantesActuales.map(function(v) {
    return [
      nuevas.some(n => n.id_vacante === v.id_vacante) ? "NUEVA" : "ACTIVA",
      v.departamento, v.municipio, v.secretaria, v.cargo,
      v.area, v.tipo_priorizacion, v.postulados, v.cierre_vacante,
      ahora, ahora, v.url_portal, v.id_vacante
    ];
  });
  
  if (filasAct.length > 0) {
    sheetAct.getRange(2, 1, filasAct.length, cabeceras.length).setValues(filasAct);
  }
  
  // 2. Actualizar Hoja 'Novedades_Nuevas'
  const sheetNov = ss.getSheetByName(CONFIG.HOJA_NOVEDADES);
  sheetNov.clearContents();
  sheetNov.appendRow(cabeceras);
  sheetNov.getRange(1, 1, 1, cabeceras.length).setBackground("#047857").setFontColor("#ffffff").setFontWeight("bold");
  
  if (nuevas.length > 0) {
    const filasNov = nuevas.map(function(v) {
      return [
        "NUEVA", v.departamento, v.municipio, v.secretaria, v.cargo,
        v.area, v.tipo_priorizacion, v.postulados, v.cierre_vacante,
        ahora, ahora, v.url_portal, v.id_vacante
      ];
    });
    sheetNov.getRange(2, 1, filasNov.length, cabeceras.length).setValues(filasNov);
  }
  
  // 3. Añadir a Hoja 'Historico' solo las que sean totalmente nuevas
  const sheetHist = ss.getSheetByName(CONFIG.HOJA_HISTORICO);
  if (nuevas.length > 0) {
    const filasHistNuevas = nuevas.map(function(v) {
      return [
        "NUEVA", v.departamento, v.municipio, v.secretaria, v.cargo,
        v.area, v.tipo_priorizacion, v.postulados, v.cierre_vacante,
        ahora, ahora, v.url_portal, v.id_vacante
      ];
    });
    sheetHist.getRange(sheetHist.getLastRow() + 1, 1, filasHistNuevas.length, cabeceras.length).setValues(filasHistNuevas);
  }
}

/**
 * Envía un correo con la tabla formateada de nuevas vacantes vía GmailApp.
 */
function enviarAlertaCorreoGmail(nuevas) {
  const destinatario = CONFIG.CORREO_DESTINO || Session.getActiveUser().getEmail();
  if (!destinatario) return;
  
  let filasHtml = "";
  nuevas.forEach(function(v) {
    filasHtml += `
      <tr style="border-bottom:1px solid #e2e8f0;">
        <td style="padding:10px;font-weight:bold;">${v.departamento} - ${v.municipio}</td>
        <td style="padding:10px;">${v.cargo}</td>
        <td style="padding:10px;color:#2563eb;font-weight:600;">${v.area}</td>
        <td style="padding:10px;color:#dc2626;">${v.cierre_vacante}</td>
        <td style="padding:10px;"><a href="${v.url_portal}" style="background:#2563eb;color:white;padding:6px 12px;text-decoration:none;border-radius:6px;font-size:12px;">Ver Portal</a></td>
      </tr>
    `;
  });
  
  const cuerpoHtml = `
    <div style="font-family:sans-serif;max-width:700px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);color:#fff;padding:20px;text-align:center;">
        <h2 style="margin:0;">🚨 ${nuevas.length} Nueva(s) Vacante(s) en Sistema Maestro</h2>
        <p style="margin:6px 0 0;opacity:0.9;">Alerta automática de oportunidades docentes MEN Colombia</p>
      </div>
      <div style="padding:20px;">
        <table style="width:100%;border-collapse:collapse;text-align:left;font-size:14px;">
          <thead>
            <tr style="background:#f1f5f9;color:#475569;">
              <th style="padding:10px;">Ubicación</th>
              <th style="padding:10px;">Cargo</th>
              <th style="padding:10px;">Área</th>
              <th style="padding:10px;">Cierre</th>
              <th style="padding:10px;">Acción</th>
            </tr>
          </thead>
          <tbody>
            ${filasHtml}
          </tbody>
        </table>
      </div>
    </div>
  `;
  
  GmailApp.sendEmail(destinatario, "🚨 " + nuevas.length + " Nuevas Vacantes en Sistema Maestro MEN", "", {
    htmlBody: cuerpoHtml
  });
  Logger.log("Alerta de correo enviada a " + destinatario);
}

/**
 * Web App REST API: permite consultar las vacantes en JSON desde cualquier aplicación web.
 */
function doGet(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.HOJA_ACTUALES);
  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({ error: "Hoja no encontrada" }))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  const data = sheet.getDataRange().getValues();
  const vacantes = [];
  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    vacantes.push({
      estado: r[0],
      departamento: r[1],
      municipio: r[2],
      secretaria: r[3],
      cargo: r[4],
      area: r[5],
      tipo_priorizacion: r[6],
      postulados: r[7],
      fecha_cierre_texto: r[8],
      url_portal: r[11],
      id_vacante: r[12]
    });
  }
  
  return ContentService.createTextOutput(JSON.stringify({
    total: vacantes.length,
    actualizado: Utilities.formatDate(new Date(), "GMT-5", "yyyy-MM-dd HH:mm:ss"),
    vacantes: vacantes
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Configura el disparador temporal automático.
 * Puedes ajustar la frecuencia aquí:
 * - Cada 15 minutos: .everyMinutes(15)
 * - Cada 30 minutos: .everyMinutes(30)
 * - Cada 1 hora: .everyHours(1)
 * - Cada 2 horas: .everyHours(2)
 */
function configurarDisparadorAutomatico(minutos = 30) {
  // Eliminar disparadores previos de esta función para no duplicar
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === "ejecutarMonitorSistemaMaestro") {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Si son 15 o 30 minutos
  if (minutos === 15 || minutos === 30 || minutos === 10 || minutos === 5 || minutos === 1) {
    ScriptApp.newTrigger("ejecutarMonitorSistemaMaestro")
      .timeBased()
      .everyMinutes(minutos)
      .create();
    Logger.log(`✅ Disparador automático configurado: se ejecutará cada ${minutos} minutos.`);
  } else {
    // Si son horas (ej: 1 hora)
    const horas = Math.max(1, Math.round(minutos / 60));
    ScriptApp.newTrigger("ejecutarMonitorSistemaMaestro")
      .timeBased()
      .everyHours(horas)
      .create();
    Logger.log(`✅ Disparador automático configurado: se ejecutará cada ${horas} hora(s).`);
  }
}

// Funciones de acceso rápido directo desde el selector de Apps Script:
function activarCada15Minutos() {
  configurarDisparadorAutomatico(15);
}

function activarCada30Minutos() {
  configurarDisparadorAutomatico(30);
}

function activarCada1Hora() {
  configurarDisparadorAutomatico(60);
}

