"""
Monitor Server — CRECI-SP Scraper
====================================
Servidor FastAPI que serve o dashboard de monitoramento.

Uso:
  cd /home/samuel/Desktop/Scraper_antigravity/scraper
  source .venv/bin/activate
  python3 ../creci_scraper/monitor_server.py

Acesse: http://localhost:8765
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# ──────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent / "output"
PROGRESS_FILE   = BASE_DIR / "progress.json"
CHECKPOINT_FILE = BASE_DIR / "checkpoint.json"
CSV_FILE        = BASE_DIR / "imobiliarias_sjc.csv"
# ──────────────────────────────────────────────

app = FastAPI(title="CRECI Monitor", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def get_status():
    """Retorna o estado atual do scraper."""
    data = {}
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"erro": "Falha ao ler progress.json"}
    else:
        data = {
            "fase": "aguardando",
            "fase_desc": "Scraper ainda nao iniciado",
            "total": 0,
            "feitos": 0,
            "pendentes": 0,
            "aguardando_captcha": False,
            "ultima_atualizacao": "",
            "log_recente": [],
            "ultima_salva": {},
        }
    return JSONResponse(data)


@app.get("/api/registros")
def get_registros(limit: int = 50, offset: int = 0):
    """Retorna os registros do CSV (paginado)."""
    rows = []
    total = 0
    if CSV_FILE.exists():
        try:
            with open(CSV_FILE, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                all_rows = list(reader)
                total = len(all_rows)
                # Retorna os mais recentes primeiro
                rows = list(reversed(all_rows))[offset: offset + limit]
        except Exception as e:
            return JSONResponse({"erro": str(e), "rows": [], "total": 0})
    return JSONResponse({"rows": rows, "total": total})


@app.get("/api/stats")
def get_stats():
    """Retorna estatísticas do CSV."""
    stats = {
        "total": 0,
        "ativos": 0,
        "inativos": 0,
        "com_cnpj": 0,
        "com_email": 0,
        "com_telefone": 0,
    }
    if CSV_FILE.exists():
        try:
            with open(CSV_FILE, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats["total"] += 1
                    status = (row.get("status") or "").lower()
                    if "ativo" in status:
                        stats["ativos"] += 1
                    else:
                        stats["inativos"] += 1
                    if row.get("cnpj") and len(row["cnpj"]) > 5:
                        stats["com_cnpj"] += 1
                    if row.get("email") and "@" in row["email"]:
                        stats["com_email"] += 1
                    if row.get("telefones") and len(row["telefones"]) > 3:
                        stats["com_telefone"] += 1
        except Exception:
            pass
    return JSONResponse(stats)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CRECI-SP Monitor</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0e1a;
    --bg2: #111827;
    --bg3: #1a2236;
    --card: #141d2e;
    --border: #1e2d45;
    --accent: #3b82f6;
    --accent2: #6366f1;
    --green: #10b981;
    --yellow: #f59e0b;
    --red: #ef4444;
    --text: #e2e8f0;
    --muted: #64748b;
    --captcha: #f59e0b;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── Header ── */
  .header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
  }
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.3px;
  }
  .logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }
  .live-badge {
    display: flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.3);
    color: var(--green);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }
  .live-dot {
    width: 7px; height: 7px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
  }

  /* ── Layout ── */
  .container { max-width: 1400px; margin: 0 auto; padding: 28px 32px; }

  /* ── Phase Banner ── */
  .phase-banner {
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
  }
  .phase-banner::before {
    content: '';
    position: absolute;
    inset: 0;
    background: inherit;
    filter: blur(20px);
    opacity: 0.3;
    z-index: -1;
  }
  .phase-banner.aguardando {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(59,130,246,0.1));
    border: 1px solid rgba(99,102,241,0.3);
  }
  .phase-banner.coleta {
    background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.1));
    border: 1px solid rgba(59,130,246,0.3);
  }
  .phase-banner.extracao {
    background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(59,130,246,0.1));
    border: 1px solid rgba(16,185,129,0.3);
  }
  .phase-banner.captcha {
    background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(239,68,68,0.1));
    border: 1px solid rgba(245,158,11,0.5);
    animation: captcha-glow 1.5s ease-in-out infinite alternate;
  }
  @keyframes captcha-glow {
    from { box-shadow: 0 0 20px rgba(245,158,11,0.2); }
    to   { box-shadow: 0 0 40px rgba(245,158,11,0.4); }
  }
  .phase-banner.concluido {
    background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(59,130,246,0.1));
    border: 1px solid rgba(16,185,129,0.4);
  }
  .phase-icon { font-size: 36px; }
  .phase-content { flex: 1; }
  .phase-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 4px;
  }
  .phase-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
  }
  .phase-sub {
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
  }

  /* ── Stats Grid ── */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px;
    transition: transform 0.2s, border-color 0.3s;
    position: relative;
    overflow: hidden;
  }
  .stat-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent-line, var(--accent));
    border-radius: 14px 14px 0 0;
  }
  .stat-card:hover { transform: translateY(-2px); border-color: rgba(59,130,246,0.3); }
  .stat-label { font-size: 11px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
  .stat-value { font-size: 36px; font-weight: 700; color: var(--text); line-height: 1; margin-bottom: 4px; }
  .stat-sub { font-size: 12px; color: var(--muted); }
  .stat-card.green  { --accent-line: var(--green); }
  .stat-card.blue   { --accent-line: var(--accent); }
  .stat-card.purple { --accent-line: var(--accent2); }
  .stat-card.yellow { --accent-line: var(--yellow); }

  /* ── Progress Bar ── */
  .progress-section {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 24px;
  }
  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }
  .progress-title { font-size: 14px; font-weight: 600; }
  .progress-pct { font-size: 24px; font-weight: 700; color: var(--accent); }
  .progress-bar-bg {
    background: var(--bg3);
    border-radius: 999px;
    height: 10px;
    overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transition: width 1s ease;
    position: relative;
  }
  .progress-bar-fill::after {
    content: '';
    position: absolute;
    right: 0; top: 0; bottom: 0;
    width: 40px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
    animation: shimmer 1.5s ease-in-out infinite;
  }
  @keyframes shimmer {
    0%, 100% { opacity: 0; }
    50% { opacity: 1; }
  }
  .progress-meta { display: flex; gap: 20px; margin-top: 12px; font-size: 12px; color: var(--muted); }
  .progress-meta span strong { color: var(--text); }

  /* ── Current Card ── */
  .current-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 24px;
  }
  .current-title { font-size: 13px; font-weight: 600; color: var(--muted); margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px; }
  .current-name { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 6px; word-break: break-all; }
  .current-url { font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono', monospace; word-break: break-all; }
  .current-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
  .badge {
    font-size: 11px; font-weight: 500;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-flex; align-items: center; gap: 5px;
  }
  .badge.ok { background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
  .badge.warn { background: rgba(245,158,11,0.15); color: var(--yellow); border: 1px solid rgba(245,158,11,0.3); }
  .badge.info { background: rgba(59,130,246,0.15); color: var(--accent); border: 1px solid rgba(59,130,246,0.3); }

  /* ── Grid columns ── */
  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
  }
  @media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }

  /* ── Log Panel ── */
  .log-panel {
    background: #080d18;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0;
    height: 380px;
    display: flex;
    flex-direction: column;
  }
  .log-header {
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .log-body {
    flex: 1;
    overflow-y: auto;
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    line-height: 1.9;
  }
  .log-body::-webkit-scrollbar { width: 4px; }
  .log-body::-webkit-scrollbar-track { background: transparent; }
  .log-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
  .log-line { color: #94a3b8; transition: color 0.2s; }
  .log-line:first-child { color: var(--text); }
  .log-line.warn  { color: var(--yellow); }
  .log-line.error { color: var(--red); }
  .log-line.ok    { color: var(--green); }
  .log-line.action { color: #c084fc; font-weight: 500; }

  /* ── Last Saved ── */
  .last-saved {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px;
    height: 380px;
    display: flex;
    flex-direction: column;
  }
  .last-saved-title {
    font-size: 12px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 16px;
  }
  .last-saved-name { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
  .last-saved-creci { font-size: 12px; color: var(--accent); font-family: 'JetBrains Mono', monospace; margin-bottom: 16px; }
  .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .field-item { background: var(--bg3); border-radius: 10px; padding: 12px 14px; }
  .field-lbl { font-size: 10px; font-weight: 600; text-transform: uppercase; color: var(--muted); letter-spacing: 0.8px; margin-bottom: 4px; }
  .field-val { font-size: 14px; font-weight: 500; color: var(--text); }
  .field-val.ok    { color: var(--green); }
  .field-val.warn  { color: var(--yellow); }
  .field-val.muted { color: var(--muted); }

  /* ── Table ── */
  .table-section {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 24px;
  }
  .table-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .table-header h3 { font-size: 14px; font-weight: 600; }
  .table-count { font-size: 12px; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; }
  thead tr { background: rgba(255,255,255,0.02); }
  th {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--muted);
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 12px 14px;
    font-size: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    vertical-align: middle;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.02); }
  .pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
  }
  .pill.ativo    { background: rgba(16,185,129,0.15); color: var(--green); }
  .pill.inativo  { background: rgba(239,68,68,0.15);  color: var(--red);   }
  .pill.sim      { background: rgba(59,130,246,0.15);  color: var(--accent); }
  .pill.nao      { background: rgba(100,116,139,0.15); color: var(--muted);  }
  .razao { font-weight: 500; color: var(--text); max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .creci-code { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--accent); }

  /* ── Last update ── */
  #last-update { font-size: 11px; color: var(--muted); }

  /* Captcha alert */
  .captcha-alert {
    background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(239,68,68,0.1));
    border: 1px solid rgba(245,158,11,0.5);
    border-radius: 14px;
    padding: 16px 22px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 24px;
    animation: captcha-glow 1.5s ease-in-out infinite alternate;
  }
  .captcha-alert-icon { font-size: 28px; }
  .captcha-alert-text h4 { font-size: 15px; font-weight: 700; color: var(--yellow); margin-bottom: 2px; }
  .captcha-alert-text p { font-size: 12px; color: #d97706; }

  /* Scrollable table */
  .table-scroll { max-height: 420px; overflow-y: auto; }
  .table-scroll::-webkit-scrollbar { width: 4px; }
  .table-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  /* Empty state */
  .empty { padding: 48px; text-align: center; color: var(--muted); }
  .empty-icon { font-size: 40px; margin-bottom: 12px; }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="logo">
    <div class="logo-icon">🏢</div>
    CRECI-SP Monitor
  </div>
  <div style="display:flex; align-items:center; gap:16px;">
    <span id="last-update">Carregando...</span>
    <div class="live-badge">
      <div class="live-dot"></div>
      AO VIVO
    </div>
  </div>
</div>

<div class="container">

  <!-- CAPTCHA Alert (visível só quando aguardando) -->
  <div class="captcha-alert" id="captcha-alert" style="display:none;">
    <div class="captcha-alert-icon">⚠️</div>
    <div class="captcha-alert-text">
      <h4>Ação Necessária: Resolva o reCAPTCHA</h4>
      <p>O scraper está aguardando você resolver o reCAPTCHA no navegador aberto para revelar os dados mascarados.</p>
    </div>
  </div>

  <!-- Phase Banner -->
  <div class="phase-banner aguardando" id="phase-banner">
    <div class="phase-icon" id="phase-icon">⏳</div>
    <div class="phase-content">
      <div class="phase-label">Status atual</div>
      <div class="phase-title" id="phase-title">Aguardando início...</div>
      <div class="phase-sub" id="phase-sub">Inicie o scraper para começar</div>
    </div>
  </div>

  <!-- Stats -->
  <div class="stats-grid">
    <div class="stat-card blue">
      <div class="stat-label">Total encontradas</div>
      <div class="stat-value" id="stat-total">—</div>
      <div class="stat-sub">imobiliárias na lista</div>
    </div>
    <div class="stat-card green">
      <div class="stat-label">Já coletadas</div>
      <div class="stat-value" id="stat-feitos">0</div>
      <div class="stat-sub">com todos os dados</div>
    </div>
    <div class="stat-card yellow">
      <div class="stat-label">Pendentes</div>
      <div class="stat-value" id="stat-pendentes">—</div>
      <div class="stat-sub">ainda faltando</div>
    </div>
    <div class="stat-card purple">
      <div class="stat-label">Ativas no CSV</div>
      <div class="stat-value" id="stat-ativas">—</div>
      <div class="stat-sub" id="stat-inativas-sub">imobiliárias ativas</div>
    </div>
  </div>

  <!-- Progress Bar -->
  <div class="progress-section">
    <div class="progress-header">
      <span class="progress-title">Progresso Geral</span>
      <span class="progress-pct" id="pct-text">0%</span>
    </div>
    <div class="progress-bar-bg">
      <div class="progress-bar-fill" id="progress-fill" style="width:0%"></div>
    </div>
    <div class="progress-meta">
      <span><strong id="m-feitos">0</strong> coletadas</span>
      <span><strong id="m-pendentes">0</strong> pendentes</span>
      <span><strong id="m-total">0</strong> total</span>
    </div>
  </div>

  <!-- Two col: Log + Last saved -->
  <div class="two-col">

    <!-- Log -->
    <div class="log-panel">
      <div class="log-header">📋 Log de Execução</div>
      <div class="log-body" id="log-body">
        <div class="log-line" style="color:var(--muted)">Aguardando logs...</div>
      </div>
    </div>

    <!-- Last saved -->
    <div class="last-saved">
      <div class="last-saved-title">🏢 Última imobiliária salva</div>
      <div id="last-saved-content">
        <div class="empty">
          <div class="empty-icon">📭</div>
          Nenhum registro salvo ainda
        </div>
      </div>
    </div>

  </div>

  <!-- Table -->
  <div class="table-section">
    <div class="table-header">
      <h3>📊 Registros Coletados</h3>
      <span class="table-count" id="table-count">0 registros</span>
    </div>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Razão Social</th>
            <th>CRECI</th>
            <th>Status</th>
            <th>CEP</th>
            <th>CNPJ</th>
            <th>E-mail</th>
            <th>Telefone</th>
            <th>Coletado em</th>
          </tr>
        </thead>
        <tbody id="table-body">
          <tr><td colspan="8" class="empty"><div class="empty-icon">📋</div>Nenhum registro ainda</td></tr>
        </tbody>
      </table>
    </div>
  </div>

</div><!-- /container -->

<script>
const POLL_INTERVAL = 3000; // 3 segundos

const PHASE_CONFIG = {
  aguardando: { icon:'⏳', cls:'aguardando' },
  coleta:     { icon:'🔍', cls:'coleta'    },
  extracao:   { icon:'⚙️',  cls:'extracao'  },
  captcha:    { icon:'🔐', cls:'captcha'   },
  concluido:  { icon:'✅', cls:'concluido' },
};

async function fetchStatus() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    renderStatus(d);
  } catch(e) { console.warn('status err', e); }
}

async function fetchRegistros() {
  try {
    const r = await fetch('/api/registros?limit=100');
    const d = await r.json();
    renderTable(d.rows, d.total);
  } catch(e) { console.warn('registros err', e); }
}

async function fetchStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    document.getElementById('stat-ativas').textContent = d.ativos || '0';
    document.getElementById('stat-inativas-sub').textContent =
      `${d.ativos || 0} ativas / ${d.inativos || 0} inativas`;
  } catch(e) {}
}

function renderStatus(d) {
  // Ultima atualizacao
  if (d.ultima_atualizacao) {
    document.getElementById('last-update').textContent = 'Atualizado: ' + d.ultima_atualizacao.split(' ')[1];
  }

  // Fase
  const fase = d.aguardando_captcha ? 'captcha' : (d.fase || 'aguardando');
  const cfg = PHASE_CONFIG[fase] || PHASE_CONFIG.aguardando;
  const banner = document.getElementById('phase-banner');
  banner.className = 'phase-banner ' + cfg.cls;
  document.getElementById('phase-icon').textContent = cfg.icon;
  document.getElementById('phase-title').textContent = d.fase_desc || 'Aguardando...';
  document.getElementById('phase-sub').textContent =
    d.atual_nome ? `Processando: ${d.atual_nome}` : '';

  // Captcha alert
  document.getElementById('captcha-alert').style.display =
    d.aguardando_captcha ? 'flex' : 'none';

  // Stats
  const total = d.total || 0;
  const feitos = d.feitos || 0;
  const pendentes = d.pendentes || 0;
  document.getElementById('stat-total').textContent = total || '—';
  document.getElementById('stat-feitos').textContent = feitos;
  document.getElementById('stat-pendentes').textContent = pendentes || '—';

  // Progress
  const pct = total > 0 ? Math.round((feitos / total) * 100) : 0;
  document.getElementById('pct-text').textContent = pct + '%';
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('m-feitos').textContent = feitos;
  document.getElementById('m-pendentes').textContent = pendentes;
  document.getElementById('m-total').textContent = total;

  // Log
  const logBody = document.getElementById('log-body');
  const logs = d.log_recente || [];
  if (logs.length > 0) {
    logBody.innerHTML = logs.map(l => {
      let cls = 'log-line';
      if (l.includes('SALVO') || l.includes('ok') || l.includes('revelad')) cls += ' ok';
      else if (l.includes('CAPTCHA') || l.includes('ACAO') || l.includes('operador')) cls += ' action';
      else if (l.includes('ERRO') || l.includes('FALHOU') || l.includes('TIMEOUT')) cls += ' error';
      else if (l.includes('AVISO')) cls += ' warn';
      return `<div class="${cls}">${escHtml(l)}</div>`;
    }).join('');
  }

  // Última salva
  if (d.ultima_salva && d.ultima_salva.nome) {
    const u = d.ultima_salva;
    document.getElementById('last-saved-content').innerHTML = `
      <div class="last-saved-name">${escHtml(u.nome)}</div>
      <div class="last-saved-creci">CRECI: ${escHtml(u.creci || '—')}</div>
      <div class="field-grid">
        <div class="field-item">
          <div class="field-lbl">Status</div>
          <div class="field-val ${(u.status||'').toLowerCase().includes('ativo') ? 'ok':'warn'}">
            ${escHtml(u.status || '—')}
          </div>
        </div>
        <div class="field-item">
          <div class="field-lbl">CEP</div>
          <div class="field-val">${escHtml(u.cep || '—')}</div>
        </div>
        <div class="field-item">
          <div class="field-lbl">CNPJ</div>
          <div class="field-val ${u.tem_cnpj ? 'ok' : 'muted'}">${u.tem_cnpj ? '✓ Coletado' : '✗ Não coletado'}</div>
        </div>
        <div class="field-item">
          <div class="field-lbl">E-mail</div>
          <div class="field-val ${u.tem_email ? 'ok' : 'muted'}">${u.tem_email ? '✓ Coletado' : '✗ Não coletado'}</div>
        </div>
        <div class="field-item">
          <div class="field-lbl">Telefone</div>
          <div class="field-val ${u.tem_telefone ? 'ok' : 'muted'}">${u.tem_telefone ? '✓ Coletado' : '✗ Não coletado'}</div>
        </div>
        <div class="field-item">
          <div class="field-lbl">Coletado em</div>
          <div class="field-val" style="font-size:11px">${escHtml(u.coletado_em || '—')}</div>
        </div>
      </div>
    `;
  }
}

function renderTable(rows, total) {
  document.getElementById('table-count').textContent = `${total} registros`;
  const tbody = document.getElementById('table-body');
  if (!rows || rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty"><div class="empty-icon">📋</div>Nenhum registro ainda</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const statusCls = (r.status||'').toLowerCase().includes('ativo') ? 'ativo' : 'inativo';
    const cnpjPill = r.cnpj && r.cnpj.length > 5
      ? '<span class="pill sim">✓</span>'
      : '<span class="pill nao">—</span>';
    const emailPill = r.email && r.email.includes('@')
      ? '<span class="pill sim">✓</span>'
      : '<span class="pill nao">—</span>';
    const telPill = r.telefones && r.telefones.length > 3
      ? '<span class="pill sim">✓</span>'
      : '<span class="pill nao">—</span>';
    return `<tr>
      <td><div class="razao" title="${escHtml(r.razao_social||r.nome_fantasia||'')}">${escHtml(r.razao_social||r.nome_fantasia||'—')}</div></td>
      <td><span class="creci-code">${escHtml(r.creci||'—')}</span></td>
      <td><span class="pill ${statusCls}">${escHtml(r.status||'—')}</span></td>
      <td>${escHtml(r.cep||'—')}</td>
      <td>${cnpjPill}</td>
      <td>${emailPill}</td>
      <td>${telPill}</td>
      <td style="font-size:11px;color:var(--muted)">${escHtml((r.coletado_em||'').split(' ')[1]||'—')}</td>
    </tr>`;
  }).join('');
}

function escHtml(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Polling
async function poll() {
  await fetchStatus();
  await fetchRegistros();
  await fetchStats();
}

poll();
setInterval(poll, POLL_INTERVAL);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


if __name__ == "__main__":
    print("=" * 50)
    print("  CRECI-SP Monitor — Dashboard de Acompanhamento")
    print("  Acesse: http://localhost:8765")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")
