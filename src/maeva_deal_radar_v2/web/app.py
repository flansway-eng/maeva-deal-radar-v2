"""Interface web FastAPI pour Maeva Deal Radar Room.

Expose une interface utilisateur simple accessible depuis n'importe
quel navigateur. Pas d'installation requise pour Maeva.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

logging.basicConfig(level=logging.WARNING)

app = FastAPI(title="Maeva Deal Radar Room", version="2.0")

pipeline_status: dict[str, str] = {"state": "idle", "result": ""}

HTML_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Maeva Deal Radar Room</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f6fa; color: #2d3436; }
  header { background: #2d3436; color: white; padding: 1.5rem 2rem;
           display: flex; align-items: center; gap: 1rem; }
  header h1 { font-size: 1.4rem; font-weight: 600; }
  header span { background: #00b894; padding: 0.2rem 0.6rem;
                border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
  main { max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem;
         display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  @media (max-width: 700px) { main { grid-template-columns: 1fr; } }
  .card { background: white; border-radius: 12px; padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .card h2 { font-size: 1rem; font-weight: 600; color: #636e72;
              text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; }
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .stat { background: #f5f6fa; border-radius: 8px; padding: 1rem; text-align: center; }
  .stat .number { font-size: 2rem; font-weight: 700; color: #2d3436; }
  .stat .label { font-size: 0.8rem; color: #636e72; margin-top: 0.25rem; }
  .stat.keep .number { color: #00b894; }
  .stat.stop .number { color: #d63031; }
  .stat.review .number { color: #fdcb6e; }
  button { display: inline-flex; align-items: center; gap: 0.5rem;
    padding: 0.75rem 1.25rem; border-radius: 8px; border: none;
    font-size: 0.9rem; font-weight: 600; cursor: pointer;
    transition: all 0.2s; width: 100%; justify-content: center; }
  .btn-primary { background: #2d3436; color: white; }
  .btn-primary:hover { background: #636e72; }
  .btn-primary:disabled { background: #b2bec3; cursor: not-allowed; }
  .btn-secondary { background: #f5f6fa; color: #2d3436; border: 1px solid #dfe6e9; }
  .btn-secondary:hover { background: #dfe6e9; }
  .source-grid { display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
  .source-btn { flex: 1; padding: 0.6rem; border: 2px solid #dfe6e9;
                border-radius: 8px; background: white; cursor: pointer;
                font-size: 0.85rem; font-weight: 500; transition: all 0.2s;
                width: auto; }
  .source-btn.active { border-color: #2d3436; background: #2d3436; color: white; }
  input, textarea {
    width: 100%; padding: 0.75rem; border: 1px solid #dfe6e9;
    border-radius: 8px; font-size: 0.9rem; margin-bottom: 0.75rem;
    font-family: inherit; display: block; }
  input:focus, textarea:focus { outline: none; border-color: #2d3436; }
  textarea { resize: vertical; min-height: 80px; }
  .result-box { background: #f5f6fa; border-radius: 8px; padding: 1rem;
                font-size: 0.85rem; line-height: 1.6; white-space: pre-wrap;
                margin-top: 1rem; display: none; max-height: 300px; overflow-y: auto; }
  .result-box.visible { display: block; }
  .lead-item { border-bottom: 1px solid #f5f6fa; padding: 0.75rem 0; }
  .lead-item:last-child { border-bottom: none; }
  .lead-name { font-weight: 600; font-size: 0.95rem; }
  .lead-meta { font-size: 0.8rem; color: #636e72; margin-top: 0.2rem; }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px;
           font-size: 0.75rem; font-weight: 600; }
  .badge-keep { background: #d4edda; color: #155724; }
  .badge-stop { background: #f8d7da; color: #721c24; }
  .badge-review { background: #fff3cd; color: #856404; }
  .spinner { display: inline-block; width: 16px; height: 16px;
             border: 2px solid #ffffff40; border-top-color: white;
             border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .full-width { grid-column: 1 / -1; }
</style>
</head>
<body>
<header>
  <h1>🎯 Maeva Deal Radar Room</h1>
  <span>v2.0</span>
</header>
<main>

  <!-- STATS -->
  <div class="card">
    <h2>Tableau de bord</h2>
    <div class="stat-grid" id="stats">
      <div class="stat"><div class="number">—</div><div class="label">Total leads</div></div>
      <div class="stat keep"><div class="number">—</div><div class="label">KEEP</div></div>
      <div class="stat stop"><div class="number">—</div><div class="label">STOP</div></div>
      <div class="stat review"><div class="number">—</div><div class="label">REVIEW</div></div>
    </div>
  </div>

  <!-- PIPELINE -->
  <div class="card">
    <h2>Lancer le pipeline</h2>
    <div class="source-grid">
      <button class="source-btn active" data-source="bodacc">BODACC</button>
      <button class="source-btn active" data-source="rss">RSS</button>
      <button class="source-btn" data-source="pappers">Pappers</button>
    </div>
    <button class="btn-primary" id="btnPipeline" onclick="runPipeline()">
      ▶ Lancer la captation
    </button>
    <div class="result-box" id="pipelineResult"></div>
  </div>

  <!-- RECHERCHE -->
  <div class="card">
    <h2>Recherche sémantique</h2>
    <input type="text" id="searchQuery"
           placeholder="Ex: fonds PE mid-market Paris, closing récent IDF..."
           onkeydown="if(event.key==='Enter') searchLeads()">
    <button class="btn-secondary" onclick="searchLeads()">🔍 Rechercher</button>
    <div class="result-box" id="searchResult"></div>
  </div>

  <!-- QUALIFIER -->
  <div class="card">
    <h2>Qualifier un lead</h2>
    <input type="text" id="qCompany" placeholder="Nom de la société *">
    <input type="text" id="qUrl" placeholder="URL source *">
    <textarea id="qDesc" placeholder="Description du signal observé *"></textarea>
    <input type="text" id="qSignal"
           placeholder="Type de signal (hiring, expansion, deal_announced...)">
    <button class="btn-primary" onclick="qualifyLead()">⚡ Qualifier</button>
    <div class="result-box" id="qualifyResult"></div>
  </div>

  <!-- DERNIERS LEADS KEEP -->
  <div class="card full-width">
    <h2>Derniers leads KEEP</h2>
    <div id="recentLeads">
      <p style="color:#636e72;font-size:0.9rem">Chargement...</p>
    </div>
  </div>

</main>
<script>
const sources = new Set(['bodacc', 'rss']);
let pollInterval = null;

document.querySelectorAll('.source-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const s = btn.dataset.source;
    if (sources.has(s)) { sources.delete(s); btn.classList.remove('active'); }
    else { sources.add(s); btn.classList.add('active'); }
  });
});

async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    document.getElementById('stats').innerHTML = `
      <div class="stat">
        <div class="number">${d.total}</div>
        <div class="label">Total leads</div>
      </div>
      <div class="stat keep">
        <div class="number">${d.keep}</div>
        <div class="label">KEEP</div>
      </div>
      <div class="stat stop">
        <div class="number">${d.stop}</div>
        <div class="label">STOP</div>
      </div>
      <div class="stat review">
        <div class="number">${d.review}</div>
        <div class="label">REVIEW</div>
      </div>`;
  } catch(e) { console.error(e); }
}

async function loadRecentLeads() {
  try {
    const r = await fetch('/api/leads?limit=8&status=KEEP');
    const d = await r.json();
    const el = document.getElementById('recentLeads');
    if (!d.leads || d.leads.length === 0) {
      el.innerHTML = '<p style="color:#636e72;font-size:0.9rem">' +
        'Aucun lead KEEP en base. Lancez le pipeline pour commencer.</p>';
      return;
    }
    el.innerHTML = d.leads.map(lead => `
      <div class="lead-item">
        <div class="lead-name">${lead.company_name}
          <span class="badge badge-${(lead.qualification_status||'').toLowerCase()}">
            ${lead.qualification_status||''}
          </span>
        </div>
        <div class="lead-meta">${lead.signal_type||''} · ${lead.geography||''}</div>
        <div class="lead-meta" style="margin-top:0.2rem">
          ${(lead.content||'').substring(0,100)}...
        </div>
      </div>`).join('');
  } catch(e) { console.error(e); }
}

async function pollPipelineStatus(box, btn) {
  try {
    const r = await fetch('/api/pipeline/status');
    const d = await r.json();
    if (d.state === 'done') {
      clearInterval(pollInterval);
      pollInterval = null;
      box.textContent = d.result || 'Pipeline terminé.';
      btn.disabled = false;
      btn.innerHTML = '▶ Lancer la captation';
      loadStats();
      loadRecentLeads();
    } else if (d.state === 'running') {
      box.textContent = 'Pipeline en cours... ⏳';
    }
  } catch(e) { console.error(e); }
}

async function runPipeline() {
  const btn = document.getElementById('btnPipeline');
  const box = document.getElementById('pipelineResult');
  if (sources.size === 0) { alert('Sélectionnez au moins une source.'); return; }
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> En cours...';
  box.className = 'result-box visible';
  box.textContent = 'Démarrage du pipeline...';
  try {
    const r = await fetch('/api/pipeline', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({sources: [...sources], max_signals: 5})
    });
    const d = await r.json();
    box.textContent = d.result || 'Pipeline lancé.';
    pollInterval = setInterval(() => pollPipelineStatus(box, btn), 5000);
  } catch(e) {
    box.textContent = 'Erreur : ' + e.message;
    btn.disabled = false;
    btn.innerHTML = '▶ Lancer la captation';
  }
}

async function searchLeads() {
  const q = document.getElementById('searchQuery').value.trim();
  const box = document.getElementById('searchResult');
  if (!q) return;
  box.className = 'result-box visible';
  box.textContent = 'Recherche en cours...';
  try {
    const r = await fetch('/api/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query: q, k: 5})
    });
    const d = await r.json();
    box.textContent = d.result || 'Aucun résultat.';
  } catch(e) { box.textContent = 'Erreur : ' + e.message; }
}

async function qualifyLead() {
  const company = document.getElementById('qCompany').value.trim();
  const url = document.getElementById('qUrl').value.trim();
  const desc = document.getElementById('qDesc').value.trim();
  const signal = document.getElementById('qSignal').value.trim() || 'unknown';
  const box = document.getElementById('qualifyResult');
  if (!company || !url || !desc) {
    alert('Remplissez les champs obligatoires (*).'); return;
  }
  box.className = 'result-box visible';
  box.textContent = 'Qualification en cours...';
  try {
    const r = await fetch('/api/qualify', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        company_name: company, source_url: url,
        description: desc, signal_type: signal
      })
    });
    const d = await r.json();
    box.textContent = d.result || 'Erreur.';
  } catch(e) { box.textContent = 'Erreur : ' + e.message; }
}

loadStats();
loadRecentLeads();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """Page principale de l'interface Maeva."""
    return HTMLResponse(content=HTML_PAGE)


@app.get("/api/stats")
async def api_stats() -> JSONResponse:
    """Statistiques de la base LanceDB."""
    try:
        from collections import Counter

        from maeva_deal_radar_v2.memory.vector_store import count, get_all
        total = count()
        if total == 0:
            return JSONResponse({"total": 0, "keep": 0, "stop": 0, "review": 0})
        leads = get_all()
        counts: dict[str, Any] = Counter(
            lead.get("qualification_status", "UNKNOWN") for lead in leads
        )
        return JSONResponse({
            "total": total,
            "keep": counts.get("KEEP", 0),
            "stop": counts.get("STOP", 0),
            "review": counts.get("REVIEW", 0),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/leads")
async def api_leads(limit: int = 10, status: str = "KEEP") -> JSONResponse:
    """Derniers leads qualifiés."""
    try:
        from maeva_deal_radar_v2.memory.vector_store import get_all
        all_leads = get_all()
        filtered = [
            lead for lead in all_leads
            if status == "ALL" or lead.get("qualification_status") == status
        ]
        safe_leads = []
        for lead in filtered[:limit]:
            safe = {k: v for k, v in lead.items() if k != "vector"}
            safe_leads.append(safe)
        return JSONResponse({"leads": safe_leads})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/pipeline")
async def api_pipeline(
    body: dict[str, Any],
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Lance le pipeline en arrière-plan."""
    if pipeline_status["state"] == "running":
        return JSONResponse({"result": "Pipeline déjà en cours..."})

    def run() -> None:
        pipeline_status["state"] = "running"
        pipeline_status["result"] = ""
        try:
            from maeva_deal_radar_v2.signals.bodacc import BodaccSource
            from maeva_deal_radar_v2.signals.pappers import PappersSource
            from maeva_deal_radar_v2.signals.pipeline import run_pipeline
            from maeva_deal_radar_v2.signals.rss import RssSource
            source_map = {
                "bodacc": BodaccSource,
                "rss": RssSource,
                "pappers": PappersSource,
            }
            requested = body.get("sources", ["bodacc", "rss"])
            max_signals = int(body.get("max_signals", 5))
            active = [source_map[s]() for s in requested if s in source_map]
            result = run_pipeline(
                sources=active,
                max_signals_per_source=max_signals,
                qualify_delay=0.3,
                store_in_lancedb=True,
                verbose=False,
            )
            pipeline_status["result"] = result.summary
        except Exception as exc:
            pipeline_status["result"] = f"Erreur : {exc}"
        finally:
            pipeline_status["state"] = "done"

    background_tasks.add_task(run)
    return JSONResponse({
        "result": (
            "Pipeline lancé en arrière-plan.\n"
            "Résultats dans 30-60 secondes.\n"
            "Le tableau de bord se mettra à jour automatiquement."
        )
    })


@app.get("/api/pipeline/status")
async def api_pipeline_status() -> JSONResponse:
    """Statut du pipeline en cours."""
    return JSONResponse(pipeline_status)


@app.post("/api/search")
async def api_search(body: dict[str, Any]) -> JSONResponse:
    """Recherche sémantique dans LanceDB."""
    try:
        from maeva_deal_radar_v2.memory.vector_store import search_similar
        query = str(body.get("query", ""))
        k = int(body.get("k", 5))
        results = search_similar(query=query, k=k)
        if not results:
            return JSONResponse({"result": f"Aucun lead trouvé pour : '{query}'"})
        lines = [f"Résultats pour '{query}' :\n"]
        for i, lead in enumerate(results, 1):
            lines.append(
                f"{i}. {lead.get('company_name')} "
                f"[{lead.get('qualification_status')}] "
                f"— {lead.get('signal_type')}"
            )
            content = lead.get("content", "")
            if content:
                lines.append(f"   {content[:120]}...")
        return JSONResponse({"result": "\n".join(lines)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/qualify")
async def api_qualify(body: dict[str, Any]) -> JSONResponse:
    """Qualifie un lead via Claude."""
    try:
        from maeva_deal_radar_v2.qualification.qualifier import qualify_lead
        result = qualify_lead(
            company_name=str(body.get("company_name", "")),
            source_url=str(body.get("source_url", "")),
            content=str(body.get("description", "")),
            signal_type=str(body.get("signal_type", "unknown")),
        )
        emoji = {"KEEP": "✓", "STOP": "✗", "REVIEW": "?"}.get(
            result.decision.value, "?"
        )
        text = (
            f"{emoji} Décision : {result.decision.value}\n"
            f"Confiance : {result.confidence:.0%}\n"
            f"Justification : {result.justification}"
        )
        return JSONResponse({"result": text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
