const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('input');
const sendBtn    = document.getElementById('sendBtn');
const esPill     = document.getElementById('esPill');
const inputArea  = document.getElementById('inputArea');

esPill.addEventListener('click', () => esPill.classList.toggle('active'));
esPill.classList.add('active'); // ES actif par défaut

/* ── ICÔNES SVG ── */
const ICONS = {
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  truck: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`,
  server:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>`,
  map:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>`,
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  info:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  arrow: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="12" height="12"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`,
  up:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="18 15 12 9 6 15"/></svg>`,
  down:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="6 9 12 15 18 9"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="20 6 9 17 4 12"/></svg>`,
  tool:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
  pen:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`,
};

/* ── CATÉGORIES ── */
const CATEGORIES = [
  {
    key: 'occupation', title: "Taux d'occupation", desc: "Remplissage des brins par zone, plaque ou région",
    c1: '#f97316', c2: '#ea580c', light: '#fff7ed', border: '#fed7aa', icon: ICONS.chart, count: 6,
    questions: [
      { text: "Quelles zones ont un taux d'occupation supérieur à 50 % ?", icon: ICONS.up },
      { text: "Quelles plaques ont un taux d'occupation inférieur à 20 % ?", icon: ICONS.down },
      { text: "Quel est le taux d'occupation moyen par région ?", icon: ICONS.chart },
      { text: "Quelles sont les 5 zones les plus occupées ?", icon: ICONS.chart },
      { text: "Quelles zones ont un taux d'occupation à 100 % ?", icon: ICONS.chart },
      { text: "Taux d'occupation par zone DRV ?", icon: ICONS.chart },
    ]
  },
  {
    key: 'deploiement', title: 'Déploiement', desc: "Statuts, avancements et programmes GPON",
    c1: '#2563eb', c2: '#1d4ed8', light: '#eff6ff', border: '#bfdbfe', icon: ICONS.truck, count: 5,
    questions: [
      { text: 'Quelles plaques sont livrées ?', icon: ICONS.check },
      { text: 'Quelles plaques sont en travaux ?', icon: ICONS.tool },
      { text: 'Quelles plaques sont en design ?', icon: ICONS.pen },
      { text: 'Quels déploiements ont été réalisés en 2024 ?', icon: ICONS.truck },
      { text: 'Quels sont les programmes GPON disponibles ?', icon: ICONS.server },
    ]
  },
  {
    key: 'infrastructure', title: 'Infrastructure', desc: "NRO, plaques, brins et capacités réseau",
    c1: '#16a34a', c2: '#15803d', light: '#f0fdf4', border: '#bbf7d0', icon: ICONS.server, count: 6,
    questions: [
      { text: 'Quels NRO sont disponibles ?', icon: ICONS.server },
      { text: 'Combien de brins sont disponibles au total ?', icon: ICONS.chart },
      { text: 'Quelles plaques ont le plus de brins libres ?', icon: ICONS.chart },
      { text: 'Quelles plaques appartiennent au NRO SVD ?', icon: ICONS.server },
      { text: 'Quel est le nombre total de brins occupés ?', icon: ICONS.chart },
      { text: 'Quelle est la capacité totale du réseau ?', icon: ICONS.chart },
    ]
  },
  {
    key: 'geographie', title: 'Géographie', desc: "Couverture par région, commune et zone DRV",
    c1: '#7c3aed', c2: '#6d28d9', light: '#f5f3ff', border: '#ddd6fe', icon: ICONS.map, count: 5,
    questions: [
      { text: 'Quelles sont les régions couvertes ?', icon: ICONS.map },
      { text: 'Quelles communes sont couvertes à Dakar ?', icon: ICONS.map },
      { text: 'Quelles zones sont dans la DRV1 ?', icon: ICONS.map },
      { text: 'Quelles zones sont dans la DRV2 ?', icon: ICONS.map },
      { text: 'Combien de zones sont couvertes par département ?', icon: ICONS.chart },
    ]
  },
  {
    key: 'population', title: 'Population & Ménages', desc: "Concessions, ménages et population couverte",
    c1: '#dc2626', c2: '#b91c1c', light: '#fef2f2', border: '#fecaca', icon: ICONS.users, count: 4,
    questions: [
      { text: 'Quelle zone couvre le plus de ménages ?', icon: ICONS.users },
      { text: 'Quelle est la population totale couverte ?', icon: ICONS.users },
      { text: 'Combien de concessions sont raccordées à Dakar ?', icon: ICONS.users },
      { text: 'Nombre de ménages couverts par région ?', icon: ICONS.chart },
    ]
  },
  {
    key: 'general', title: 'Général FTTH', desc: "Définitions et concepts du réseau fibre",
    c1: '#0d9488', c2: '#0f766e', light: '#f0fdfa', border: '#99f6e4', icon: ICONS.info, count: 4,
    questions: [
      { text: "C'est quoi un NRO ?", icon: ICONS.info },
      { text: "C'est quoi une plaque FTTH ?", icon: ICONS.info },
      { text: 'Comment fonctionne le réseau GPON ?', icon: ICONS.info },
      { text: "Quelle est la différence entre brin total et brin occupé ?", icon: ICONS.info },
    ]
  },
];

/* ── INIT CARDS ── */
function buildCards() {
  const grid = document.getElementById('cardsGrid');
  if (!grid) return;
  grid.innerHTML = CATEGORIES.map(cat => `
    <div class="cat-card" onclick="openDrawer('${cat.key}')"
      style="--card-c1:${cat.c1};--card-c2:${cat.c2};--card-light:${cat.light};--card-border:${cat.border}">
      <div class="cat-card-icon">${cat.icon}</div>
      <div class="cat-card-title">${cat.title}</div>
      <div class="cat-card-desc">${cat.desc}</div>
      <span class="cat-card-count">${cat.count}</span>
      <span class="cat-card-arrow">${ICONS.arrow}</span>
    </div>`).join('');
}

buildCards();

/* ── DRAWER ── */
function openDrawer(key) {
  const cat = CATEGORIES.find(c => c.key === key);
  document.getElementById('drawerIconWrap').innerHTML = cat.icon;
  document.getElementById('drawerIconWrap').style.background = `linear-gradient(135deg,${cat.c1},${cat.c2})`;
  document.getElementById('drawerTitle').textContent    = cat.title;
  document.getElementById('drawerSubtitle').textContent = cat.desc;
  document.getElementById('drawerQuestions').innerHTML  = cat.questions.map((q, i) => `
    <button class="drawer-q"
      style="--dq-c1:${cat.c1};--dq-c2:${cat.c2};--dq-light:${cat.light};--dq-border:${cat.border}"
      data-question="${i}" data-cat="${cat.key}">
      <span class="drawer-q-icon">${q.icon}</span>
      <span>${q.text}</span>
      <span class="drawer-q-arrow">${ICONS.arrow}</span>
    </button>`).join('');

  document.getElementById('drawerQuestions').querySelectorAll('.drawer-q').forEach(btn => {
    btn.addEventListener('click', () => {
      const cat2 = CATEGORIES.find(c => c.key === btn.dataset.cat);
      sendFromDrawer(cat2.questions[parseInt(btn.dataset.question)].text);
    });
  });
  document.getElementById('drawerOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeDrawer(e) {
  if (e && e.target !== document.getElementById('drawerOverlay')) return;
  closeDrawerForce();
}

function closeDrawerForce() {
  document.getElementById('drawerOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function sendFromDrawer(question) {
  closeDrawerForce();
  showView('chat');
  esPill.classList.add('active'); // toujours ES pour les questions des cartes
  inputEl.value = question;
  envoyer();
}

/* ── VIEWS ── */
function showView(view) {
  document.getElementById('viewChat').style.display      = view === 'chat'      ? 'flex' : 'none';
  document.getElementById('viewDashboard').style.display = view === 'dashboard' ? 'flex' : 'none';
  document.getElementById('btnChat').classList.toggle('active', view === 'chat');
  document.getElementById('btnDash').classList.toggle('active', view === 'dashboard');
  if (view === 'dashboard') loadDashboard();
}

/* ── DASHBOARD ── */
let _charts = [];

function destroyCharts() {
  _charts.forEach(c => c.destroy());
  _charts = [];
}

function mkChart(id, config) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  _charts.push(new Chart(ctx, config));
}

async function loadDashboard() {
  destroyCharts();
  const body = document.getElementById('dashBody');
  body.innerHTML = `<div class="dash-loading"><div class="typing"><span></span><span></span><span></span></div><p>Chargement des données…</p></div>`;
  try {
    const res = await fetch('/stats');
    const d   = await res.json();
    if (d.error) { body.innerHTML = `<p style="color:#ef4444;padding:20px">${d.error}</p>`; return; }

    const tauxPct        = d.taux_moyen || 0;
    const brinsOccPct    = d.total_brins ? Math.round((d.brins_occupes / d.total_brins) * 100) : 0;
    const statutColors   = { 'LIVREE': '#22c55e', 'EN TRAVAUX': '#f97316', 'EN DESIGN': '#2563eb' };
    const PALETTE        = ['#f97316','#2563eb','#16a34a','#7c3aed','#dc2626','#0d9488','#d97706','#db2777','#0ea5e9','#84cc16'];

    body.innerHTML = `
      <!-- KPIs -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Enregistrements</div>
          <div class="kpi-value">${d.total_docs.toLocaleString('fr')}</div>
          <div class="kpi-sub">Lignes dans l'index</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Brins totaux</div>
          <div class="kpi-value">${d.total_brins.toLocaleString('fr')}</div>
          <div class="kpi-sub">${d.brins_occupes.toLocaleString('fr')} occupés &middot; ${d.brins_libres.toLocaleString('fr')} libres</div>
          <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${brinsOccPct}%"></div></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Taux d'occupation moyen</div>
          <div class="kpi-value">${tauxPct}<span>%</span></div>
          <div class="kpi-bar"><div class="kpi-bar-fill" style="width:${tauxPct}%;background:${tauxPct>70?'#dc2626':tauxPct>40?'#f97316':'#22c55e'}"></div></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Plaques uniques</div>
          <div class="kpi-value">${d.total_plaques.toLocaleString('fr')}</div>
          <div class="kpi-sub">Identifiants distincts</div>
        </div>
      </div>

      <!-- Ligne 1 : Donut statuts + Barres top zones -->
      <div class="dash-row">
        <div class="dash-card">
          <div class="dash-card-title">${ICONS.truck} Statut de déploiement</div>
          <div class="chart-wrap" style="max-width:280px;margin:0 auto">
            <canvas id="chartStatut"></canvas>
          </div>
        </div>
        <div class="dash-card">
          <div class="dash-card-title">${ICONS.chart} Top zones saturées</div>
          <div class="chart-wrap">
            <canvas id="chartTopZones"></canvas>
          </div>
        </div>
      </div>

      <!-- Ligne 2 : Barres régions + Barres DRV -->
      <div class="dash-row">
        <div class="dash-card">
          <div class="dash-card-title">${ICONS.map} Taux d'occupation par région</div>
          <div class="chart-wrap">
            <canvas id="chartRegion"></canvas>
          </div>
        </div>
        <div class="dash-card">
          <div class="dash-card-title">${ICONS.server} Taux d'occupation par zone DRV</div>
          <div class="chart-wrap">
            <canvas id="chartDrv"></canvas>
          </div>
        </div>
      </div>`;

    // Donut — statuts
    mkChart('chartStatut', {
      type: 'doughnut',
      data: {
        labels: d.par_statut.map(s => s.label),
        datasets: [{
          data: d.par_statut.map(s => s.count),
          backgroundColor: d.par_statut.map(s => statutColors[s.label] || '#9ca3af'),
          borderWidth: 2,
          borderColor: '#fff',
          hoverOffset: 6
        }]
      },
      options: {
        cutout: '65%',
        plugins: {
          legend: { position: 'bottom', labels: { font: { size: 12, family: 'Inter' }, padding: 16, usePointStyle: true } }
        }
      }
    });

    // Barres horizontales — top zones
    mkChart('chartTopZones', {
      type: 'bar',
      data: {
        labels: d.top_zones.map(z => z.label),
        datasets: [{
          label: 'Taux (%)',
          data: d.top_zones.map(z => z.taux),
          backgroundColor: d.top_zones.map(z => z.taux > 80 ? '#dc2626' : z.taux > 50 ? '#f97316' : '#22c55e'),
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        indexAxis: 'y',
        scales: {
          x: { min: 0, max: 100, grid: { color: '#f3f4f6' }, ticks: { callback: v => v + '%', font: { size: 11 } } },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } }
        },
        plugins: { legend: { display: false } }
      }
    });

    // Barres horizontales — régions
    mkChart('chartRegion', {
      type: 'bar',
      data: {
        labels: d.par_region.map(r => r.label),
        datasets: [{
          label: 'Taux moyen (%)',
          data: d.par_region.map(r => r.taux),
          backgroundColor: d.par_region.map((_, i) => PALETTE[i % PALETTE.length] + 'cc'),
          borderColor:     d.par_region.map((_, i) => PALETTE[i % PALETTE.length]),
          borderWidth: 1.5,
          borderRadius: 5,
          borderSkipped: false
        }]
      },
      options: {
        indexAxis: 'y',
        scales: {
          x: { min: 0, max: 100, grid: { color: '#f3f4f6' }, ticks: { callback: v => v + '%', font: { size: 11 } } },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } }
        },
        plugins: { legend: { display: false } }
      }
    });

    // Barres verticales — DRV
    mkChart('chartDrv', {
      type: 'bar',
      data: {
        labels: d.par_drv.map(z => z.label),
        datasets: [{
          label: 'Taux moyen (%)',
          data: d.par_drv.map(z => z.taux),
          backgroundColor: d.par_drv.map((_, i) => PALETTE[i % PALETTE.length] + 'cc'),
          borderColor:     d.par_drv.map((_, i) => PALETTE[i % PALETTE.length]),
          borderWidth: 1.5,
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        scales: {
          y: { min: 0, max: 100, grid: { color: '#f3f4f6' }, ticks: { callback: v => v + '%', font: { size: 11 } } },
          x: { grid: { display: false }, ticks: { font: { size: 12, weight: '600' } } }
        },
        plugins: { legend: { display: false } }
      }
    });

  } catch(e) {
    body.innerHTML = `<p style="color:#ef4444;padding:20px">Erreur : ${e.message}</p>`;
  }
}

/* ── CHAT ── */
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); envoyer(); }
}

function clearChat() {
  messagesEl.innerHTML = `
    <div class="welcome" id="welcome">
      <div class="welcome-logo"><img src="/static/Logo sonatel.png" alt="Sonatel" /></div>
      <h2>Bonjour, comment puis-je vous aider ?</h2>
      <p>Explorez les données du réseau FTTH Sonatel.<br>Choisissez une catégorie ci-dessous pour commencer.</p>
      <div class="cards-grid" id="cardsGrid"></div>
    </div>`;
  inputArea.style.display = 'none';
  buildCards();
}

function addMsg(role, content) {
  document.getElementById('welcome')?.remove();
  inputArea.style.display = 'block';
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="avatar ${role}">${role === 'bot' ? 'IA' : 'Vous'}</div>
    <div class="bubble">${content}</div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

async function envoyer() {
  const q = inputEl.value.trim();
  if (!q) return;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  sendBtn.disabled = true;
  addMsg('user', q);
  const typingDiv = addMsg('bot', '<div class="typing"><span></span><span></span><span></span></div>');
  const mode = esPill.classList.contains('active') ? 'elasticsearch' : 'faiss';
  try {
    const ctrl = new AbortController();
    const t    = setTimeout(() => ctrl.abort(), 60000);
    const res  = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, mode }),
      signal: ctrl.signal
    });
    clearTimeout(t);
    const data = await res.json();
    typingDiv.querySelector('.bubble').textContent = data.reponse || data.error;
  } catch(e) {
    typingDiv.querySelector('.bubble').textContent = e.name === 'AbortError' ? 'Délai dépassé, veuillez réessayer.' : 'Erreur de connexion.';
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

/* ── MODALS ── */
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

async function loadUrl() {
  const url = document.getElementById('urlInput').value.trim();
  const msg = document.getElementById('urlMsg');
  if (!url) { msg.textContent = 'URL vide'; msg.className = 'modal-msg error'; return; }
  msg.textContent = 'Indexation en cours…'; msg.className = 'modal-msg';
  const res  = await fetch('/load_url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) });
  const data = await res.json();
  msg.textContent = data.message || data.error;
  msg.className   = data.error ? 'modal-msg error' : 'modal-msg';
}

async function uploadFile() {
  const file = document.getElementById('fileInput').files[0];
  const msg  = document.getElementById('fileMsg');
  if (!file) { msg.textContent = 'Aucun fichier sélectionné'; msg.className = 'modal-msg error'; return; }
  msg.textContent = 'Indexation en cours…'; msg.className = 'modal-msg';
  const form = new FormData();
  form.append('file', file);
  const res  = await fetch('/upload', { method: 'POST', body: form });
  const data = await res.json();
  msg.textContent = data.message || data.error;
  msg.className   = data.error ? 'modal-msg error' : 'modal-msg';
}
