/**
 * JavaScript Client — Monitor Sistema Maestro MEN
 * Handles data fetching, live filtering, dynamic KPI calculations, table/card rendering,
 * SheetJS Excel/CSV export, and modal interaction.
 */

// Application State
const state = {
  allVacancies: [],
  filteredVacancies: [],
  meta: {},
  currentView: 'cards', // 'cards' | 'table'
  filters: {
    search: '',
    departamento: '',
    municipio: '',
    area: '',
    cargo: '',
    quickTag: null,
  },
  sort: {
    column: 'fecha_cierre_iso',
    ascending: true,
  },
  theme: localStorage.getItem('sm_theme') || 'dark',
};

// DOM Elements
const elements = {
  themeToggle: document.getElementById('theme-toggle'),
  themeIcon: document.getElementById('theme-icon'),
  lastUpdateText: document.getElementById('last-update-text'),
  kpiActivas: document.getElementById('kpi-activas'),
  kpiNuevas: document.getElementById('kpi-nuevas'),
  kpiDeptos: document.getElementById('kpi-deptos'),
  kpiMpios: document.getElementById('kpi-mpios'),
  
  searchInput: document.getElementById('search-input'),
  clearSearchBtn: document.getElementById('clear-search'),
  filterDepartamento: document.getElementById('filter-departamento'),
  filterMunicipio: document.getElementById('filter-municipio'),
  filterArea: document.getElementById('filter-area'),
  filterCargo: document.getElementById('filter-cargo'),
  resetFiltersBtn: document.getElementById('reset-filters-btn'),
  resultsCountText: document.getElementById('results-count-text'),
  
  viewCardsBtn: document.getElementById('view-cards-btn'),
  viewTableBtn: document.getElementById('view-table-btn'),
  vacanciesGrid: document.getElementById('vacancies-grid'),
  vacanciesTableContainer: document.getElementById('vacancies-table-container'),
  vacanciesTableBody: document.getElementById('vacancies-table-body'),
  emptyState: document.getElementById('empty-state'),
  emptyResetBtn: document.getElementById('empty-reset-btn'),
  
  exportMenuBtn: document.getElementById('export-menu-btn'),
  exportMenu: document.getElementById('export-menu'),
  exportExcelBtn: document.getElementById('export-excel-btn'),
  exportCsvBtn: document.getElementById('export-csv-btn'),
  exportJsonBtn: document.getElementById('export-json-btn'),
  
  detailModal: document.getElementById('detail-modal'),
  modalBadge: document.getElementById('modal-badge'),
  modalCargo: document.getElementById('modal-cargo'),
  modalBodyContent: document.getElementById('modal-body-content'),
  modalClose: document.getElementById('modal-close'),
  modalCopyBtn: document.getElementById('modal-copy-btn'),
  toast: document.getElementById('toast-message'),
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setupEventListeners();
  loadData();
});

// Theme Management
function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('sm_theme', state.theme);
  updateThemeIcon();
}

function updateThemeIcon() {
  if (state.theme === 'dark') {
    elements.themeIcon.className = 'ph ph-sun';
  } else {
    elements.themeIcon.className = 'ph ph-moon';
  }
}

// Toast Notifications
function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add('show');
  setTimeout(() => {
    elements.toast.classList.remove('show');
  }, 3000);
}

// Data Fetching
async function loadData() {
  try {
    elements.lastUpdateText.textContent = 'Actualizando datos...';
    // Intento 1: Cargar desde data/vacantes_actuales.json
    const response = await fetch('data/vacantes_actuales.json?t=' + Date.now());
    if (!response.ok) throw new Error('No se pudo cargar el archivo local');
    
    const data = await response.json();
    state.allVacancies = data.vacantes || [];
    state.meta = data.meta || {};
    
    populateDropdowns();
    applyFilters();
    updateKPICards();
    
    if (state.meta.ultima_actualizacion) {
      elements.lastUpdateText.textContent = `Actualizado: ${state.meta.ultima_actualizacion}`;
    } else {
      elements.lastUpdateText.textContent = 'Actualizado en vivo';
    }
  } catch (error) {
    console.warn('Error al cargar datos JSON:', error);
    elements.lastUpdateText.textContent = 'Modo de demostración';
    renderDemoDataIfEmpty();
  }
}

function renderDemoDataIfEmpty() {
  if (state.allVacancies.length === 0) {
    elements.lastUpdateText.textContent = 'Datos no encontrados';
    elements.emptyState.style.display = 'flex';
  }
}

// Dropdowns Population
function populateDropdowns() {
  // Departamentos
  const deptosConteo = {};
  state.allVacancies.forEach(v => {
    const d = v.departamento || 'Sin Departamento';
    deptosConteo[d] = (deptosConteo[d] || 0) + 1;
  });
  
  elements.filterDepartamento.innerHTML = '<option value="">Todos los Departamentos</option>';
  Object.keys(deptosConteo).sort().forEach(depto => {
    const opt = document.createElement('option');
    opt.value = depto;
    opt.textContent = `${depto} (${deptosConteo[depto]})`;
    elements.filterDepartamento.appendChild(opt);
  });
  
  // Municipios
  updateMunicipiosDropdown();
  
  // Áreas
  const areas = Array.from(new Set(state.allVacancies.map(v => v.area).filter(Boolean))).sort();
  elements.filterArea.innerHTML = '<option value="">Todas las Áreas</option>';
  areas.forEach(area => {
    const opt = document.createElement('option');
    opt.value = area;
    opt.textContent = area;
    elements.filterArea.appendChild(opt);
  });
  
  // Cargos
  const cargos = Array.from(new Set(state.allVacancies.map(v => v.cargo).filter(Boolean))).sort();
  elements.filterCargo.innerHTML = '<option value="">Todos los Cargos</option>';
  cargos.forEach(cargo => {
    const opt = document.createElement('option');
    opt.value = cargo;
    opt.textContent = cargo;
    elements.filterCargo.appendChild(opt);
  });
}

function updateMunicipiosDropdown() {
  const deptoSeleccionado = state.filters.departamento;
  const vacantesFiltradas = deptoSeleccionado 
    ? state.allVacancies.filter(v => v.departamento === deptoSeleccionado)
    : state.allVacancies;
    
  const mpios = Array.from(new Set(vacantesFiltradas.map(v => v.municipio).filter(Boolean))).sort();
  elements.filterMunicipio.innerHTML = '<option value="">Todos los Municipios</option>';
  mpios.forEach(mpio => {
    const opt = document.createElement('option');
    opt.value = mpio;
    opt.textContent = mpio;
    elements.filterMunicipio.appendChild(opt);
  });
}

// Filtering & Sorting
function applyFilters() {
  const { search, departamento, municipio, area, cargo, quickTag } = state.filters;
  const searchLower = search.toLowerCase().trim();
  const ahora = new Date();
  
  state.filteredVacancies = state.allVacancies.filter(v => {
    // Texto libre
    if (searchLower) {
      const matchText = [
        v.cargo, v.area, v.departamento, v.municipio, v.secretaria, v.tipo_priorizacion, v.zona
      ].filter(Boolean).join(' ').toLowerCase();
      if (!matchText.includes(searchLower)) return false;
    }
    
    // Filtros dropdown
    if (departamento && v.departamento !== departamento) return false;
    if (municipio && v.municipio !== municipio) return false;
    if (area && v.area !== area) return false;
    if (cargo && v.cargo !== cargo) return false;
    
    // Filtros rápidos
    if (quickTag === 'nuevas' && v.estado !== 'NUEVA') return false;
    if (quickTag === 'urgentes') {
      if (!v.fecha_cierre_iso) return false;
      const cierre = new Date(v.fecha_cierre_iso);
      const diffHoras = (cierre - ahora) / (1000 * 60 * 60);
      if (diffHoras < 0 || diffHoras > 24) return false;
    }
    if (quickTag === 'primaria' && !(v.area || '').toLowerCase().includes('primaria')) return false;
    if (quickTag === 'preescolar' && !(v.area || '').toLowerCase().includes('preescolar')) return false;
    if (quickTag === 'matematicas' && !(v.area || '').toLowerCase().includes('matem')) return false;
    if (quickTag === 'orientador' && !(v.cargo || '').toLowerCase().includes('orientador')) return false;
    
    return true;
  });
  
  // Ordenar
  sortVacancies();
  
  // Renderizar
  renderVacancies();
  
  // Actualizar contador y botón de reset
  elements.resultsCountText.innerHTML = `Mostrando <strong>${state.filteredVacancies.length}</strong> de ${state.allVacancies.length} oportunidades`;
  
  const hasActiveFilters = Boolean(search || departamento || municipio || area || cargo || quickTag);
  elements.resetFiltersBtn.style.display = hasActiveFilters ? 'inline-block' : 'none';
  elements.clearSearchBtn.style.display = search ? 'block' : 'none';
}

function sortVacancies() {
  const { column, ascending } = state.sort;
  state.filteredVacancies.sort((a, b) => {
    let valA = a[column] || '';
    let valB = b[column] || '';
    
    if (typeof valA === 'number' && typeof valB === 'number') {
      return ascending ? valA - valB : valB - valA;
    }
    
    valA = String(valA).toLowerCase();
    valB = String(valB).toLowerCase();
    
    if (valA < valB) return ascending ? -1 : 1;
    if (valA > valB) return ascending ? 1 : -1;
    return 0;
  });
}

function updateKPICards() {
  const activas = state.allVacancies.length;
  const nuevas = state.allVacancies.filter(v => v.estado === 'NUEVA').length;
  const deptos = new Set(state.allVacancies.map(v => v.departamento).filter(Boolean)).size;
  const mpios = new Set(state.allVacancies.map(v => v.municipio).filter(Boolean)).size;
  
  elements.kpiActivas.textContent = activas.toLocaleString('es-CO');
  elements.kpiNuevas.textContent = nuevas.toLocaleString('es-CO');
  elements.kpiDeptos.textContent = deptos.toLocaleString('es-CO');
  elements.kpiMpios.textContent = mpios.toLocaleString('es-CO');
}

// Rendering
function renderVacancies() {
  if (state.filteredVacancies.length === 0) {
    elements.vacanciesGrid.style.display = 'none';
    elements.vacanciesTableContainer.style.display = 'none';
    elements.emptyState.style.display = 'flex';
    return;
  }
  
  elements.emptyState.style.display = 'none';
  
  if (state.currentView === 'cards') {
    elements.vacanciesGrid.style.display = 'grid';
    elements.vacanciesTableContainer.style.display = 'none';
    renderCards();
  } else {
    elements.vacanciesGrid.style.display = 'none';
    elements.vacanciesTableContainer.style.display = 'block';
    renderTable();
  }
}

function calcularTiempoRestante(fechaIso) {
  if (!fechaIso) return { texto: 'Por confirmar', urgente: false };
  const diff = new Date(fechaIso) - new Date();
  if (diff <= 0) return { texto: 'Cerrada', urgente: true, cerrada: true };
  
  const horas = Math.floor(diff / (1000 * 60 * 60));
  const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (horas < 24) {
    return { texto: `Cierra en ${horas}h ${minutos}m`, urgente: true, cerrada: false };
  } else {
    const dias = Math.floor(horas / 24);
    return { texto: `Cierra en ${dias}d ${horas % 24}h`, urgente: false, cerrada: false };
  }
}

function renderCards() {
  elements.vacanciesGrid.innerHTML = '';
  
  state.filteredVacancies.forEach(v => {
    const card = document.createElement('div');
    card.className = 'vacancy-card glass-card';
    
    const badgeClass = v.estado === 'NUEVA' ? 'badge-nueva' : (v.estado === 'ACTUALIZADA' ? 'badge-actualizada' : 'badge-activa');
    const badgeText = v.estado || 'ACTIVA';
    const countdown = calcularTiempoRestante(v.fecha_cierre_iso);
    const closingClass = countdown.urgente ? 'closing-banner' : 'closing-banner safe';
    
    card.innerHTML = `
      <div>
        <div class="card-header-bar">
          <div class="card-badges">
            <span class="badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="card-postulados">
            <i class="ph-bold ph-users"></i>
            <span>${v.postulados || 0} postulados</span>
          </div>
        </div>
        
        <div class="card-title-block" style="margin-top: 0.75rem;">
          <h3>${v.cargo || 'Docente de Aula'}</h3>
          <span class="card-area-tag">${v.area || 'Sin Área Especificada'}</span>
        </div>
        
        <div class="card-meta-list">
          <div class="meta-row">
            <i class="ph ph-map-pin"></i>
            <span><span class="meta-highlight">${v.departamento || ''}</span>, ${v.municipio || ''}</span>
          </div>
          <div class="meta-row">
            <i class="ph ph-buildings"></i>
            <span>Sec. Educación: ${v.secretaria || 'Oficial'}</span>
          </div>
          <div class="meta-row">
            <i class="ph ph-shield-check"></i>
            <span>${v.tipo_priorizacion || 'Vacantes Generales'}</span>
          </div>
        </div>
      </div>
      
      <div>
        <div class="${closingClass}">
          <span><i class="ph-bold ph-clock"></i> ${v.fecha_cierre_texto || 'Fecha de cierre'}</span>
          <span class="countdown-timer">${countdown.texto}</span>
        </div>
        
        <div class="card-actions">
          <button class="btn btn-secondary detail-btn" data-id="${v.id_vacante}">
            <i class="ph ph-info"></i> Detalles
          </button>
          <a href="${v.url_portal || 'https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml'}" target="_blank" rel="noopener" class="btn btn-primary">
            <i class="ph-bold ph-arrow-square-out"></i> Postularse
          </a>
        </div>
      </div>
    `;
    
    elements.vacanciesGrid.appendChild(card);
  });
}

function renderTable() {
  elements.vacanciesTableBody.innerHTML = '';
  
  state.filteredVacancies.forEach(v => {
    const tr = document.createElement('tr');
    const badgeClass = v.estado === 'NUEVA' ? 'badge-nueva' : (v.estado === 'ACTUALIZADA' ? 'badge-actualizada' : 'badge-activa');
    
    tr.innerHTML = `
      <td><span class="badge ${badgeClass}">${v.estado || 'ACTIVA'}</span></td>
      <td><strong>${v.departamento}</strong><br><small style="color:var(--text-muted);">${v.municipio}</small></td>
      <td><strong>${v.cargo}</strong></td>
      <td><span class="card-area-tag" style="margin:0;">${v.area}</span></td>
      <td><small>${v.tipo_priorizacion || 'General'}</small></td>
      <td><strong>${v.postulados || 0}</strong></td>
      <td><small>${v.fecha_cierre_texto}</small></td>
      <td>
        <div style="display:flex; gap: 0.35rem;">
          <button class="btn btn-secondary detail-btn" data-id="${v.id_vacante}" style="padding:4px 8px; font-size:0.75rem;">
            <i class="ph ph-info"></i>
          </button>
          <a href="${v.url_portal || 'https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml'}" target="_blank" rel="noopener" class="btn btn-primary" style="padding:4px 8px; font-size:0.75rem;">
            <i class="ph-bold ph-arrow-square-out"></i>
          </a>
        </div>
      </td>
    `;
    elements.vacanciesTableBody.appendChild(tr);
  });
}

// Modal View
function openDetailModal(vacanteId) {
  const v = state.allVacancies.find(item => item.id_vacante === vacanteId);
  if (!v) return;
  
  elements.modalBadge.className = `badge ${v.estado === 'NUEVA' ? 'badge-nueva' : (v.estado === 'ACTUALIZADA' ? 'badge-actualizada' : 'badge-activa')}`;
  elements.modalBadge.textContent = v.estado || 'ACTIVA';
  elements.modalCargo.textContent = v.cargo || 'Detalle de Convocatoria';
  
  elements.modalBodyContent.innerHTML = `
    <div class="modal-detail-row">
      <span class="modal-label">Área de Conocimiento</span>
      <span class="modal-val" style="color:var(--accent-blue); font-size:1.1rem; font-weight:700;">${v.area || 'N/A'}</span>
    </div>
    
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
      <div class="modal-detail-row">
        <span class="modal-label">Departamento</span>
        <span class="modal-val">${v.departamento || 'N/A'}</span>
      </div>
      <div class="modal-detail-row">
        <span class="modal-label">Municipio</span>
        <span class="modal-val">${v.municipio || 'N/A'}</span>
      </div>
    </div>
    
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
      <div class="modal-detail-row">
        <span class="modal-label">Secretaría de Educación</span>
        <span class="modal-val">${v.secretaria || 'N/A'}</span>
      </div>
      <div class="modal-detail-row">
        <span class="modal-label">Zona</span>
        <span class="modal-val">${v.zona || 'N/A'}</span>
      </div>
    </div>
    
    <div class="modal-detail-row">
      <span class="modal-label">Tipo de Priorización</span>
      <span class="modal-val">${v.tipo_priorizacion || 'Vacantes Generales'}</span>
    </div>
    
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
      <div class="modal-detail-row">
        <span class="modal-label">Cierre de Convocatoria</span>
        <span class="modal-val" style="color:var(--accent-red); font-weight:700;">${v.fecha_cierre_texto || 'N/A'}</span>
      </div>
      <div class="modal-detail-row">
        <span class="modal-label">Postulados Registrados</span>
        <span class="modal-val">${v.postulados || 0} docentes</span>
      </div>
    </div>
    
    <div class="modal-detail-row">
      <span class="modal-label">Identificador Único (Hash)</span>
      <span class="modal-val" style="font-family:monospace; font-size:0.75rem; word-break:break-all; color:var(--text-muted);">${v.id_vacante}</span>
    </div>
  `;
  
  elements.modalCopyBtn.onclick = () => {
    const textoCopiar = `📢 Oportunidad Sistema Maestro MEN\nCargo: ${v.cargo}\nÁrea: ${v.area}\nUbicación: ${v.departamento} - ${v.municipio}\nCierre: ${v.fecha_cierre_texto}\nPostulados: ${v.postulados}\nEnlace: https://sistemamaestro.mineducacion.gov.co/SistemaMaestro/busquedaVacantes.xhtml`;
    navigator.clipboard.writeText(textoCopiar).then(() => {
      showToast('📋 ¡Detalles copiados al portapapeles!');
    });
  };
  
  elements.detailModal.style.display = 'flex';
}

function closeDetailModal() {
  elements.detailModal.style.display = 'none';
}

// Client-Side Data Export
function exportToExcel() {
  if (state.filteredVacancies.length === 0) {
    showToast('No hay datos para exportar');
    return;
  }
  
  const dataExport = state.filteredVacancies.map(v => ({
    'Estado': v.estado,
    'Departamento': v.departamento,
    'Municipio': v.municipio,
    'Secretaría': v.secretaria,
    'Cargo': v.cargo,
    'Área': v.area,
    'Tipo Priorización': v.tipo_priorizacion,
    'Postulados': v.postulados,
    'Fecha Cierre': v.fecha_cierre_texto,
    'Enlace': v.url_portal,
    'ID Vacante': v.id_vacante,
  }));
  
  const ws = XLSX.utils.json_to_sheet(dataExport);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Vacantes Sistema Maestro');
  XLSX.writeFile(wb, `vacantes_sistema_maestro_${new Date().toISOString().slice(0,10)}.xlsx`);
  showToast('📊 Archivo Excel descargado exitosamente');
}

function exportToCsv() {
  if (state.filteredVacancies.length === 0) {
    showToast('No hay datos para exportar');
    return;
  }
  
  const headers = ['Estado', 'Departamento', 'Municipio', 'Secretaria', 'Cargo', 'Area', 'Priorizacion', 'Postulados', 'Cierre', 'Enlace'];
  const rows = state.filteredVacancies.map(v => [
    `"${v.estado || ''}"`,
    `"${v.departamento || ''}"`,
    `"${v.municipio || ''}"`,
    `"${v.secretaria || ''}"`,
    `"${v.cargo || ''}"`,
    `"${v.area || ''}"`,
    `"${v.tipo_priorizacion || ''}"`,
    v.postulados || 0,
    `"${v.fecha_cierre_texto || ''}"`,
    `"${v.url_portal || ''}"`,
  ]);
  
  const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `vacantes_sistema_maestro_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast('📄 Archivo CSV descargado exitosamente');
}

function exportToJson() {
  if (state.filteredVacancies.length === 0) {
    showToast('No hay datos para exportar');
    return;
  }
  
  const jsonContent = JSON.stringify(state.filteredVacancies, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `vacantes_sistema_maestro_${new Date().toISOString().slice(0,10)}.json`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast('📁 Archivo JSON descargado exitosamente');
}

// Event Listeners
function setupEventListeners() {
  // Theme Toggle
  elements.themeToggle.addEventListener('click', toggleTheme);
  
  // Search Input
  elements.searchInput.addEventListener('input', (e) => {
    state.filters.search = e.target.value;
    applyFilters();
  });
  
  elements.clearSearchBtn.addEventListener('click', () => {
    elements.searchInput.value = '';
    state.filters.search = '';
    applyFilters();
  });
  
  // Dropdown Filters
  elements.filterDepartamento.addEventListener('change', (e) => {
    state.filters.departamento = e.target.value;
    state.filters.municipio = '';
    updateMunicipiosDropdown();
    applyFilters();
  });
  
  elements.filterMunicipio.addEventListener('change', (e) => {
    state.filters.municipio = e.target.value;
    applyFilters();
  });
  
  elements.filterArea.addEventListener('change', (e) => {
    state.filters.area = e.target.value;
    applyFilters();
  });
  
  elements.filterCargo.addEventListener('change', (e) => {
    state.filters.cargo = e.target.value;
    applyFilters();
  });
  
  // Quick Filter Tags
  document.querySelectorAll('.filter-tag').forEach(tagBtn => {
    tagBtn.addEventListener('click', () => {
      const tag = tagBtn.dataset.tag;
      if (state.filters.quickTag === tag) {
        state.filters.quickTag = null;
        tagBtn.classList.remove('active');
      } else {
        document.querySelectorAll('.filter-tag').forEach(b => b.classList.remove('active'));
        state.filters.quickTag = tag;
        tagBtn.classList.add('active');
      }
      applyFilters();
    });
  });
  
  // Reset Filters
  const resetAll = () => {
    state.filters = { search: '', departamento: '', municipio: '', area: '', cargo: '', quickTag: null };
    elements.searchInput.value = '';
    elements.filterDepartamento.value = '';
    elements.filterMunicipio.value = '';
    elements.filterArea.value = '';
    elements.filterCargo.value = '';
    document.querySelectorAll('.filter-tag').forEach(b => b.classList.remove('active'));
    updateMunicipiosDropdown();
    applyFilters();
  };
  
  elements.resetFiltersBtn.addEventListener('click', resetAll);
  elements.emptyResetBtn.addEventListener('click', resetAll);
  
  // View Switchers
  elements.viewCardsBtn.addEventListener('click', () => {
    state.currentView = 'cards';
    elements.viewCardsBtn.classList.add('active');
    elements.viewTableBtn.classList.remove('active');
    renderVacancies();
  });
  
  elements.viewTableBtn.addEventListener('click', () => {
    state.currentView = 'table';
    elements.viewTableBtn.classList.add('active');
    elements.viewCardsBtn.classList.remove('active');
    renderVacancies();
  });
  
  // Table Header Sort
  document.querySelectorAll('.custom-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.sort;
      if (state.sort.column === col) {
        state.sort.ascending = !state.sort.ascending;
      } else {
        state.sort.column = col;
        state.sort.ascending = true;
      }
      sortVacancies();
      renderTable();
    });
  });
  
  // Export Dropdown Toggle
  elements.exportMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.exportMenu.classList.toggle('show');
  });
  
  document.addEventListener('click', () => {
    elements.exportMenu.classList.remove('show');
  });
  
  elements.exportExcelBtn.addEventListener('click', (e) => { e.preventDefault(); exportToExcel(); });
  elements.exportCsvBtn.addEventListener('click', (e) => { e.preventDefault(); exportToCsv(); });
  elements.exportJsonBtn.addEventListener('click', (e) => { e.preventDefault(); exportToJson(); });
  
  // Modal Delegated Click
  document.addEventListener('click', (e) => {
    const detailBtn = e.target.closest('.detail-btn');
    if (detailBtn) {
      const id = detailBtn.dataset.id;
      openDetailModal(id);
    }
  });
  
  elements.modalClose.addEventListener('click', closeDetailModal);
  elements.detailModal.addEventListener('click', (e) => {
    if (e.target === elements.detailModal) closeDetailModal();
  });
}
