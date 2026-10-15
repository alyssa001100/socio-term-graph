#!/usr/bin/env python3
"""生成静态检索页面 —— 无需服务器、无依赖，双击即可打开，也可直接托管。

用法：python3 build_site.py
输出：site/index.html（自包含，数据内嵌）
"""
import json, os
from collections import Counter
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>社会学术语知识系统</title>
<style>
:root{--bg:#fbfaf7;--fg:#1f1d1a;--mut:#6b6660;--line:#e3ded4;--acc:#8c5a2b;--chip:#f2ede4}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15px/1.7 -apple-system,"PingFang SC","Hiragino Sans GB",sans-serif}
header{padding:34px 28px 20px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:23px;letter-spacing:.5px}
.sub{color:var(--mut);margin:0 0 14px;font-size:14px}
.stats{display:flex;gap:22px;flex-wrap:wrap;font-size:13px;color:var(--mut)}
.stats b{color:var(--fg);font-size:16px;display:block}
.filters{padding:16px 28px;border-bottom:1px solid var(--line);
  background:rgba(251,250,247,.97);backdrop-filter:blur(6px);z-index:5}
/* 仅在筛选栏不会占满视口时才吸顶：窄屏下按钮换行会把面板撑得比屏幕还高，
  吸顶后卡片被完全遮住，内容无法触达 */
@media (min-width:900px){.filters{position:sticky;top:0}}
.fgroup{display:grid;grid-template-columns:64px minmax(0,1fr);gap:8px;align-items:start;margin-bottom:9px}
.chips{display:flex;gap:7px;flex-wrap:wrap}
.flabel{font-size:12px;color:var(--mut);padding-top:5px;letter-spacing:.5px}
.chip{border:1px solid var(--line);background:#fff;color:var(--fg);border-radius:14px;
  padding:3px 11px;font-size:13px;cursor:pointer;transition:.12s}
.chip:hover{border-color:var(--acc)}
.chip.on{background:var(--acc);border-color:var(--acc);color:#fff}
.chip i{font-style:normal;opacity:.5;font-size:11px;margin-left:4px}
#q{width:100%;margin-top:4px;padding:9px 13px;border:1px solid var(--line);border-radius:9px;
  font-size:14px;background:#fff;font-family:inherit}
#q:focus{outline:none;border-color:var(--acc)}
main{padding:22px 28px 70px;max-width:1000px}
.card{background:#fff;border:1px solid var(--line);border-radius:11px;padding:17px 19px;margin-bottom:13px}
.card.hl{border-color:var(--acc);box-shadow:0 0 0 3px rgba(140,90,43,.13)}
.ttl{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.zh{font-size:17px;font-weight:600}
.en{color:var(--mut);font-size:13px;font-style:italic}
.badge{font-size:11px;padding:1px 7px;border-radius:8px;background:var(--chip);color:var(--mut)}
.badge.cat{background:#efe2d2;color:#8c5a2b}
.meta{color:var(--mut);font-size:13px;margin:5px 0 9px}
.def{margin:0 0 10px}
.def b{color:var(--acc);font-weight:600}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px}
.tag{font-size:12px;background:var(--chip);color:#57514a;border-radius:5px;padding:1px 8px}
details{border-top:1px dashed var(--line);padding-top:8px;margin-top:9px}
summary{cursor:pointer;font-size:13px;color:var(--acc);outline:none;user-select:none}
summary::marker{color:var(--line)}
details ul{margin:8px 0 2px;padding-left:19px}
details li{margin-bottom:7px;font-size:14px}
.poly li{padding-left:2px}
.who{font-weight:600}
.reltype{background:#eef1f5;color:#3c4a5c;border-radius:5px;padding:0 6px;font-size:12px;margin:0 3px}
a.t{color:var(--acc);cursor:pointer;text-decoration:none;border-bottom:1px dotted var(--acc)}
.case{color:var(--mut);font-size:13px}
.mism{display:block;color:#8a4a3a;font-size:13px;margin-top:2px}
.empty{color:var(--mut);padding:36px 0;text-align:center}
footer{color:var(--mut);font-size:12px;padding:0 28px 40px}
</style>
</head>
<body>
<header>
  <h1>社会学术语知识系统</h1>
  <p class="sub">概念群：社会不平等是如何被生产、维持与再生产的？</p>
  <div class="stats" id="stats"></div>
</header>
<div class="filters">
  <div class="fgroup"><span class="flabel">流派</span><div class="chips" id="fSchool"></div></div>
  <div class="fgroup"><span class="flabel">应用场景</span><div class="chips" id="fApp"></div></div>
  <input id="q" placeholder="搜索术语、英文名、别名、定义、提出者…">
</div>
<main id="list"></main>
<footer id="foot"></footer>
<script>
const DATA = __DATA__;
const S = {school:new Set(), app:new Set(), q:''};

function chips(el, values, field, key){
  const cnt = {};
  DATA.terms.forEach(t => (t[field]||[]).forEach(v => cnt[v]=(cnt[v]||0)+1));
  el.innerHTML = values.filter(v => cnt[v]).map(v =>
    `<button class="chip" data-v="${v}">${v}<i>${cnt[v]}</i></button>`).join('');
  el.querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const v = b.dataset.v;
    S[key].has(v) ? S[key].delete(v) : S[key].add(v);
    b.classList.toggle('on');
    render();
  });
}

function matched(t){
  if (S.school.size && !t.school.some(s => S.school.has(s))) return false;
  if (S.app.size && !t.application.some(a => S.app.has(a))) return false;
  if (S.q){
    const q = S.q.toLowerCase();
    const hay = [t.name_zh, t.name_en, (t.aliases||[]).join(' '), t.definition,
                 t.proponent, t.first_source].join(' ').toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

const esc = s => String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

function relRow(t){
  const out = [];
  t.rel_out.forEach(r => out.push(
    `本条目<span class="reltype">${r.type}</span>→ <a class="t" data-j="${r.other_id}">${r.other}</a>`));
  t.rel_in.forEach(r => out.push(
    `<a class="t" data-j="${r.other_id}">${r.other}</a><span class="reltype">${r.type}</span>→ 本条目`));
  return out.length ? out.map(x=>`<li>${x}</li>`).join('') : '<li class="case">暂无</li>';
}

function card(t){
  const poly = (t.polysemy||[]).length ? t.polysemy.map(p => `
    <li><span class="who">${esc(p.author)}</span>：${esc(p.definition)}
      ${p.differs_from?`<span class="case">（与 ${esc(p.differs_from)} 不同：${esc(p.note||'')}）</span>`:''}
    </li>`).join('') : '<li class="case">本条无多义性记录</li>';
  const cases = t.cases.length ? t.cases.map(c => `
    <li>${esc(c.title)}<span class="case">　${esc(c.origin)}</span>
      ${c.mismatch?`<span class="mism">不符之处：${esc(c.mismatch)}</span>`:''}</li>`).join('')
    : '<li class="case">暂无</li>';
  const hots = t.hotspots.length ? t.hotspots.map(h => `
    <li>${esc(h.title)}<span class="case">　${h.date} · ${h.confidence}</span>
      <span class="mism">不符之处：${esc(h.mismatch)}</span></li>`).join('')
    : '<li class="case">暂无</li>';
  return `<div class="card" id="t-${t.term_id}">
    <div class="ttl"><span class="zh">${esc(t.name_zh)}</span>
      <span class="en">${esc(t.name_en)}</span>
      ${t.entry_type==='分析范畴'?'<span class="badge cat">分析范畴</span>':''}
      <span class="badge">${esc(t.status)}</span></div>
    <div class="meta">${esc(t.proponent)} · ${t.first_year} · ${esc(t.first_source)}</div>
    <p class="def"><b>定义</b>　${esc(t.definition)}</p>
    <div class="tags">${t.school.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}
      ${t.application.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div>
    <details><summary>多义性（${(t.polysemy||[]).length}）</summary><ul class="poly">${poly}</ul></details>
    <details><summary>概念关系（${t.rel_out.length + t.rel_in.length}）</summary><ul>${relRow(t)}</ul></details>
    ${t.cases.length ? `<details><summary>经典案例（${t.cases.length}）</summary><ul>${cases}</ul></details>` : ''}
    <details><summary>社会热点（${t.hotspots.length}）</summary><ul>${hots}</ul></details>
  </div>`;
}

function render(){
  const list = DATA.terms.filter(matched).sort((a,b)=>a.first_year-b.first_year);
  document.getElementById('list').innerHTML = list.length
    ? list.map(card).join('') : '<div class="empty">没有符合条件的术语</div>';
  document.getElementById('foot').textContent =
    `显示 ${list.length} / ${DATA.terms.length} 条术语　·　数据状态：全部待核对原文页码`;
  document.querySelectorAll('a.t').forEach(a => a.onclick = () => {
    const el = document.getElementById('t-' + a.dataset.j);
    if (el){ el.scrollIntoView({behavior:'smooth',block:'center'});
             el.classList.add('hl'); setTimeout(()=>el.classList.remove('hl'),1600); }
  });
}

document.getElementById('stats').innerHTML = [
  ['术语', DATA.meta.terms], ['概念关系', DATA.meta.relations],
  ['经典案例', DATA.meta.cases], ['社会热点', DATA.meta.hotspots],
  ['多义性条目', DATA.meta.polysemy]
].map(([k,v]) => `<div><b>${v}</b>${k}</div>`).join('');

chips(document.getElementById('fSchool'), DATA.enums.school, 'school', 'school');
chips(document.getElementById('fApp'), DATA.enums.application, 'application', 'app');
document.getElementById('q').oninput = e => { S.q = e.target.value.trim(); render(); };
render();
</script>
</body>
</html>
"""


def main():
    schema = yaml.safe_load(open(os.path.join(ROOT, "schema.yaml"), encoding="utf-8"))
    def load(n):
        return yaml.safe_load(open(os.path.join(ROOT, "data", n), encoding="utf-8")) or []
    terms, rels, cases, hots = (load("terms.yaml"), load("relations.yaml"),
                               load("cases.yaml"), load("hotspots.yaml"))

    name = {t["term_id"]: t["name_zh"] for t in terms}
    by_id = {t["term_id"]: t for t in terms}
    for t in terms:
        t["rel_out"], t["rel_in"], t["cases"], t["hotspots"] = [], [], [], []

    for r in rels:
        if r["from_term"] in by_id:
            by_id[r["from_term"]]["rel_out"].append(
                {"type": r["type"], "other": name.get(r["to_term"], r["to_term"]),
                 "other_id": r["to_term"]})
        if r["to_term"] in by_id:
            by_id[r["to_term"]]["rel_in"].append(
                {"type": r["type"], "other": name.get(r["from_term"], r["from_term"]),
                 "other_id": r["from_term"]})

    for c in cases:
        for a in c["attributions"]:
            if a["term_id"] in by_id:
                by_id[a["term_id"]]["cases"].append(
                    {"title": c["title"], "origin": c["origin"], "mismatch": a["mismatch"]})
    for h in hots:
        for a in h["attributions"]:
            if a["term_id"] in by_id:
                by_id[a["term_id"]]["hotspots"].append(
                    {"title": h["title"], "date": h["date"],
                     "confidence": a["confidence"], "mismatch": a["mismatch"]})

    payload = {
        "meta": {"terms": len(terms), "relations": len(rels), "cases": len(cases),
                 "hotspots": len(hots),
                 "polysemy": sum(1 for t in terms if t.get("polysemy"))},
        "enums": schema["enums"], "terms": terms,
    }
    out = os.path.join(ROOT, "site")
    os.makedirs(out, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    path = os.path.join(out, "index.html")
    open(path, "w", encoding="utf-8").write(html)
    print(f"已生成 {path}（{len(html)/1024:.0f} KB，自包含，无外部依赖）")


if __name__ == "__main__":
    main()
