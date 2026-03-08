from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


def write_html(report: dict[str, Any], out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "report.html"
    summary = report["summary"]
    data_json = json.dumps(report, ensure_ascii=False)
    style = """
    body{font-family:Inter,Segoe UI,Arial,sans-serif;background:#0b1020;color:#e8edf8;margin:0}
    .wrap{max-width:1300px;margin:0 auto;padding:24px}
    .hero{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-bottom:18px}
    h1,h2,h3{margin:0 0 10px}
    .muted{color:#98a2b3}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:18px 0 26px}
    .card,.panel{background:#121933;border:1px solid #243055;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.18)}
    .card{padding:18px}.panel{padding:16px;margin-bottom:16px}
    .metric{font-size:28px;font-weight:700;margin-top:6px}.small{font-size:12px}.pill{display:inline-block;padding:4px 9px;border-radius:999px;background:#1d2750}
    table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px 8px;border-bottom:1px solid #243055;text-align:left;vertical-align:top}th{color:#a9b6d3;font-weight:600}
    .row{display:grid;grid-template-columns:1.3fr .7fr;gap:16px}.bars{display:flex;align-items:flex-end;gap:6px;height:160px;padding-top:10px}.bar{flex:1;background:linear-gradient(180deg,#5b8cff,#8f6cff);border-radius:8px 8px 0 0;min-width:8px;position:relative}.bar span{position:absolute;bottom:-22px;left:50%;transform:translateX(-50%);font-size:11px;color:#8ea0c6;white-space:nowrap}
    .graph{width:100%;height:420px;background:#0d1430;border-radius:14px;border:1px solid #243055}.legend{display:flex;gap:10px;flex-wrap:wrap}.dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:4px}
    .search{width:100%;padding:12px 14px;border-radius:12px;background:#0d1430;color:#e8edf8;border:1px solid #243055;box-sizing:border-box}.split{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    a{color:#8ab4ff;text-decoration:none}.footer{color:#7382a9;margin:28px 0 10px;font-size:13px}
    @media (max-width:980px){.row,.split{grid-template-columns:1fr}}
    """
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SwarmLens Report</title><style>{style}</style></head>
<body><div class="wrap">
<div class="hero"><div><h1>SwarmLens Investigation Report</h1><div class="muted">Case: {escape(summary['case_name'])} · Generated: {escape(summary['generated_at'])}</div></div><div><span class="pill">Campaign grade: {escape(summary['campaign_grade'])}</span></div></div>
<div class="grid">
<div class="card"><div class="muted small">Accounts analyzed</div><div class="metric">{summary['accounts']}</div></div>
<div class="card"><div class="muted small">Posts analyzed</div><div class="metric">{summary['posts']}</div></div>
<div class="card"><div class="muted small">Interactions analyzed</div><div class="metric">{summary['interactions']}</div></div>
<div class="card"><div class="muted small">High-risk accounts</div><div class="metric">{summary['high_risk_accounts']}</div></div>
<div class="card"><div class="muted small">Coordinated clusters</div><div class="metric">{summary['coordinated_clusters']}</div></div>
<div class="card"><div class="muted small">Campaign score</div><div class="metric">{summary['campaign_score']}</div></div>
</div>
<div class="row">
<div class="panel"><h2>Account Risk Ranking</h2><input class="search" id="riskSearch" placeholder="Filter accounts by username, grade, or reason"><div style="max-height:380px;overflow:auto;margin-top:12px"><table id="riskTable"><thead><tr><th>Username</th><th>Score</th><th>Grade</th><th>Reasons</th></tr></thead><tbody></tbody></table></div></div>
<div class="panel"><h2>Campaign Timeline</h2><div id="timelineBars" class="bars"></div><div class="footer">Each bar represents a 2-minute bucket of post activity.</div></div>
</div>
<div class="split">
<div class="panel"><h2>Cluster Summaries</h2><div style="max-height:320px;overflow:auto"><table id="clustersTable"><thead><tr><th>Cluster</th><th>Size</th><th>Average Risk</th><th>Top phrase</th></tr></thead><tbody></tbody></table></div></div>
<div class="panel"><h2>Repeated Message Evidence</h2><div style="max-height:320px;overflow:auto"><table id="reuseTable"><thead><tr><th>Accounts</th><th>Posts</th><th>Phrase</th></tr></thead><tbody></tbody></table></div></div>
</div>
<div class="panel"><h2>Network Overview</h2><div class="legend"><span><span class="dot" style="background:#5bc0ff"></span>Low risk</span><span><span class="dot" style="background:#ffc857"></span>Medium risk</span><span><span class="dot" style="background:#ff6b6b"></span>High risk</span></div><svg class="graph" id="graphSvg" viewBox="0 0 1000 420"></svg></div>
<div class="split">
<div class="panel"><h2>Suspicious Pairs</h2><div style="max-height:320px;overflow:auto"><table id="pairsTable"><thead><tr><th>Source</th><th>Target</th><th>Count</th><th>Pair score</th></tr></thead><tbody></tbody></table></div></div>
<div class="panel"><h2>Engagement Authenticity</h2><div style="max-height:320px;overflow:auto"><table id="authTable"><thead><tr><th>Target</th><th>Authenticity</th><th>Suspicious support</th><th>Interactions</th></tr></thead><tbody></tbody></table></div></div>
</div>
<div class="footer">SwarmLens generates probabilistic investigative indicators for public-data review. Scores support analyst prioritization and do not prove policy violations or operator identity.</div>
</div>
<script>const REPORT = {data_json};
const riskTbody = document.querySelector('#riskTable tbody');
function fillRisk(filter=''){{
 riskTbody.innerHTML='';
 const rows = REPORT.account_scores.filter(x => !filter || JSON.stringify(x).toLowerCase().includes(filter.toLowerCase()));
 rows.forEach(x => {{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${{x.username}}</td><td>${{x.score.toFixed(3)}}</td><td>${{x.grade}}</td><td>${{x.reasons.join(', ')}}</td>`; riskTbody.appendChild(tr); }});
}}
fillRisk(); document.getElementById('riskSearch').addEventListener('input', e=>fillRisk(e.target.value));
const timeline = REPORT.timeline.slice(0,24); const bars=document.getElementById('timelineBars'); const maxCount=Math.max(...timeline.map(x=>x.post_count),1); timeline.forEach((x,i)=>{{ const el=document.createElement('div'); el.className='bar'; el.style.height=(20 + (x.post_count/maxCount)*130)+'px'; el.title=`${{x.bucket}} → ${{x.post_count}} posts`; el.innerHTML=`<span>${{i+1}}</span>`; bars.appendChild(el); }});
function fillTable(id, rows, mapper){{ const tbody=document.querySelector(id+' tbody'); tbody.innerHTML=''; rows.forEach(r=>{{ const tr=document.createElement('tr'); tr.innerHTML=mapper(r); tbody.appendChild(tr); }}); }}
fillTable('#clustersTable', REPORT.cluster_summaries, r=>`<td>${{r.cluster_id}}</td><td>${{r.size}}</td><td>${{r.average_risk}}</td><td>${{r.top_phrase||'-'}}</td>`);
fillTable('#reuseTable', REPORT.exact_reuse.slice(0,25), r=>`<td>${{r.unique_accounts}}</td><td>${{r.count}}</td><td>${{r.text}}</td>`);
fillTable('#pairsTable', REPORT.suspicious_pairs.slice(0,25), r=>`<td>${{r.source}}</td><td>${{r.target}}</td><td>${{r.count}}</td><td>${{r.pair_score}}</td>`);
fillTable('#authTable', REPORT.authenticity.slice(0,25), r=>`<td>${{r.target_username}}</td><td>${{r.authenticity_score}}</td><td>${{r.suspicious_support}}</td><td>${{r.interaction_count}}</td>`);
const svg=document.getElementById('graphSvg'); const nodes=REPORT.graph.nodes.slice(0,30); const edges=REPORT.graph.edges.filter(e=>nodes.some(n=>n.id===e.source)&&nodes.some(n=>n.id===e.target)).slice(0,45); const centerX=500, centerY=210, radius=150;
const pos={{}}; nodes.forEach((n,i)=>{{ const angle=(Math.PI*2*i)/Math.max(nodes.length,1); pos[n.id]={{x:centerX+Math.cos(angle)*radius*(1+(i%3)*0.15), y:centerY+Math.sin(angle)*radius*(1+(i%4)*0.12)}}; }});
edges.forEach(e=>{{ const a=pos[e.source], b=pos[e.target]; if(!a||!b) return; const line=document.createElementNS('http://www.w3.org/2000/svg','line'); line.setAttribute('x1',a.x); line.setAttribute('y1',a.y); line.setAttribute('x2',b.x); line.setAttribute('y2',b.y); line.setAttribute('stroke','#31426f'); line.setAttribute('stroke-width',Math.min(1+e.count*0.5,4)); svg.appendChild(line); }});
nodes.forEach(n=>{{ const p=pos[n.id]; const g=document.createElementNS('http://www.w3.org/2000/svg','g'); const c=document.createElementNS('http://www.w3.org/2000/svg','circle'); const t=document.createElementNS('http://www.w3.org/2000/svg','text'); const color=n.risk>=0.65?'#ff6b6b':(n.risk>=0.45?'#ffc857':'#5bc0ff'); c.setAttribute('cx',p.x); c.setAttribute('cy',p.y); c.setAttribute('r',10 + n.risk*10); c.setAttribute('fill',color); c.setAttribute('opacity','0.92'); t.setAttribute('x',p.x+12); t.setAttribute('y',p.y+4); t.setAttribute('fill','#c8d6f2'); t.setAttribute('font-size','12'); t.textContent=n.label; g.appendChild(c); g.appendChild(t); svg.appendChild(g); }});
</script></body></html>"""
    html_path.write_text(html, encoding="utf-8")
    return html_path
