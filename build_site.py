#!/usr/bin/env python3
"""生成静态检索页面 —— 无需服务器、无依赖，双击即可打开，也可直接托管。

用法：python3 build_site.py
输出：site/index.html（自包含，数据内嵌）
"""
import json, math, os, random
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
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:5px}
.views{display:flex;gap:6px;margin-top:11px}
.vbtn{border:1px solid var(--line);background:#fff;color:var(--fg);border-radius:8px;
  padding:4px 16px;font-size:13px;cursor:pointer;font-family:inherit;transition:.12s}
.vbtn:hover{border-color:var(--acc)}
.vbtn.on{background:var(--acc);border-color:var(--acc);color:#fff}
#graph{padding:10px 28px 40px;display:none;max-width:1240px}
#graph svg{width:100%;height:auto;display:block}
/* 窄屏上整张图会被缩到看不清标签，改为保持可读宽度、允许横向平移 */
@media (max-width:820px){
  #graph{overflow-x:auto;-webkit-overflow-scrolling:touch;padding:10px 14px 30px}
  #graph svg{width:760px;height:auto}
}
/* 群内连线用该群的颜色、压暗；跨群桥接用橙色虚线并压在最上层，
   一眼就能看出「哪几处是概念群之间的桥」 */
.e{stroke-width:1.3;opacity:.42}
.e.br{stroke:#c9822b;stroke-width:2.2;stroke-dasharray:6 4;opacity:1}
.lead{stroke-width:1;opacity:.4}
.gnode{cursor:pointer}
.gnode circle{stroke:#fff;stroke-width:1.6}
.gnode:hover circle{stroke:#1f1d1a;stroke-width:2.2}
.gnode:hover text{font-weight:600}
/* 标签描一圈页面底色的边：压在连线或节点上也读得清 */
.gnode text{font-size:11px;fill:#3f3a33;
  paint-order:stroke;stroke:#fbfaf7;stroke-width:3.2px;stroke-linejoin:round}
.legend{display:flex;gap:22px;flex-wrap:wrap;padding:4px 28px 14px;font-size:13px;color:var(--mut);max-width:1240px}
.legend div{max-width:340px}
.legend b{color:var(--fg);font-weight:600}
</style>
</head>
<body>
<header>
  <h1>社会学术语知识系统</h1>
  <p class="sub" id="sub"></p>
  <div class="stats" id="stats"></div>
</header>
<div class="filters">
  <div class="fgroup"><span class="flabel">概念群</span><div class="chips" id="fCluster"></div></div>
  <div class="fgroup"><span class="flabel">流派</span><div class="chips" id="fSchool"></div></div>
  <div class="fgroup"><span class="flabel">应用场景</span><div class="chips" id="fApp"></div></div>
  <input id="q" placeholder="搜索术语、英文名、别名、定义、提出者…">
  <div class="views">
    <button class="vbtn on" id="vList">列表</button>
    <button class="vbtn" id="vGraph">网络</button>
  </div>
</div>
<div class="legend" id="legend"></div>
<main id="list"></main>
<div id="graph"></div>
<footer id="foot"></footer>
<script>
const DATA = __DATA__;
const S = {cluster:new Set(), school:new Set(), app:new Set(), q:'', view:'list'};

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
  if (S.cluster.size && !S.cluster.has(t.cluster)) return false;
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

document.getElementById('sub').textContent =
  `${DATA.clusterOrder.length} 个概念群　·　术语之间以「关系」相连成网，` +
  `跨概念群处是桥接（橙色虚线）　·　点节点可跳到词条`;

document.getElementById('stats').innerHTML = [
  ['术语', DATA.meta.terms], ['概念关系', DATA.meta.relations],
  ['经典案例', DATA.meta.cases], ['社会热点', DATA.meta.hotspots],
  ['多义性条目', DATA.meta.polysemy]
].map(([k,v]) => `<div><b>${v}</b>${k}</div>`).join('');

function clusterChips(el){
  const cnt = {};
  DATA.terms.forEach(t => cnt[t.cluster] = (cnt[t.cluster]||0)+1);
  el.innerHTML = DATA.clusterOrder.filter(c => cnt[c]).map(c =>
    `<button class="chip" data-v="${c}"><span class="dot" style="background:${DATA.clusterColors[c]}"></span>${c}<i>${cnt[c]}</i></button>`).join('');
  el.querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const v = b.dataset.v;
    S.cluster.has(v) ? S.cluster.delete(v) : S.cluster.add(v);
    b.classList.toggle('on');
    draw();
  });
}

function legend(){
  document.getElementById('legend').innerHTML = DATA.clusterOrder.map(c =>
    `<div><span class="dot" style="background:${DATA.clusterColors[c]}"></span>` +
    `<b>${esc(c)}</b>　${esc(DATA.clusters[c]||'')}</div>`).join('');
}

function gotoCard(id){
  S.view = 'list';
  document.getElementById('vList').classList.add('on');
  document.getElementById('vGraph').classList.remove('on');
  draw();
  const el = document.getElementById('t-' + id);
  if (el){ el.scrollIntoView({behavior:'smooth', block:'center'});
           el.classList.add('hl'); setTimeout(()=>el.classList.remove('hl'), 1800); }
}

function renderGraph(){
  const list = DATA.terms.filter(matched);
  const on = new Set(list.map(t => t.term_id));
  const inner = [], bridge = [];
  list.forEach(t => (t.rel_out || []).forEach(r => {
    if (!on.has(r.other_id)) return;
    const a = DATA.layout[t.term_id], b = DATA.layout[r.other_id];
    if (!a || !b) return;
    const isBr = DATA.clusterOf[t.term_id] !== DATA.clusterOf[r.other_id];
    const col = DATA.clusterColors[DATA.clusterOf[t.term_id]] || '#8c5a2b';
    (isBr ? bridge : inner).push(
      `<line class="e${isBr ? ' br' : ''}"${isBr ? '' : ` style="stroke:${col}"`}` +
      ` x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}"/>`);
  }));
  const P = inner.concat(bridge);
  const V = DATA.view || [0, 0, DATA.size[0], DATA.size[1]];
  list.forEach(t => {
    const p = DATA.layout[t.term_id];
    if (!p) return;
    const r = DATA.radius[t.term_id] || 6;
    const L = DATA.label[t.term_id] || [p[0], p[1] + r + 12, 'middle'];
    const col = DATA.clusterColors[t.cluster] || '#8c5a2b';
    const deg = (t.rel_out || []).length + (t.rel_in || []).length;
    // 标签摆在左右两侧时离节点较远，补一根引线，避免读成旁边那个点的标签
    if (L[2] !== 'middle')
      P.push(`<line class="lead" style="stroke:${col}" x1="${L[2] === 'start' ? p[0] + r : p[0] - r}"` +
             ` y1="${p[1]}" x2="${L[2] === 'start' ? L[0] - 2 : L[0] + 2}" y2="${L[1] - 11 * 0.28}"/>`);
    P.push(`<g class="gnode" data-j="${t.term_id}">` +
      `<title>${esc(t.name_zh)}　${esc(t.name_en)}　·　${esc(t.cluster)}　·　关系 ${deg} 条</title>` +
      `<circle cx="${p[0]}" cy="${p[1]}" r="${r}" fill="${col}"></circle>` +
      `<text x="${L[0]}" y="${L[1]}" style="text-anchor:${L[2]}">${esc(t.name_zh)}</text></g>`);
  });
  document.getElementById('graph').innerHTML =
    `<svg viewBox="${V.join(' ')}" preserveAspectRatio="xMidYMid meet">${P.join('')}</svg>`;
  document.querySelectorAll('.gnode').forEach(g => g.onclick = () => gotoCard(g.dataset.j));
  document.getElementById('foot').textContent =
    `网络视图：${list.length} 个节点　·　实线＝群内关系（按概念群着色），橙色虚线＝跨概念群桥接　·　点节点可跳到词条`;
}

function draw(){
  const isGraph = S.view === 'graph';
  document.getElementById('list').style.display = isGraph ? 'none' : '';
  document.getElementById('graph').style.display = isGraph ? 'block' : 'none';
  isGraph ? renderGraph() : render();
}

document.getElementById('vList').onclick = () => { S.view = 'list';
  document.getElementById('vList').classList.add('on');
  document.getElementById('vGraph').classList.remove('on'); draw(); };
document.getElementById('vGraph').onclick = () => { S.view = 'graph';
  document.getElementById('vGraph').classList.add('on');
  document.getElementById('vList').classList.remove('on'); draw(); };

clusterChips(document.getElementById('fCluster'));
chips(document.getElementById('fSchool'), DATA.enums.school, 'school', 'school');
chips(document.getElementById('fApp'), DATA.enums.application, 'application', 'app');
document.getElementById('q').oninput = e => { S.q = e.target.value.trim(); draw(); };
legend();
draw();
</script>
</body>
</html>
"""


CLUSTER_COLORS = {
    "社会不平等": "#8c5a2b",
    "社会秩序与越轨": "#3c6e71",
    "社会行动与理性化": "#7a5c9e",
}
NET_W, NET_H = 1000, 900


def layout(terms, rels, cluster_names, width=NET_W, height=NET_H, iters=900):
    """在构建时算好节点坐标：确定性、可验证，页面只负责渲染。

    力导向：节点两两排斥 + 关系边当弹簧 + 每个概念群向自己的锚点聚拢。
    锚点均匀分布在一个圆上，三个群therefore自然分开，群间桥接成为跨越的连线。
    规模大的群吸引系数更小，于是铺得更开——否则 28 个节点会挤成一块。
    """
    rnd = random.Random(7)
    n = max(1, len(cluster_names))
    cx, cy = width / 2, height / 2
    anchors, size_of = {}, {}
    for i, c in enumerate(cluster_names):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        anchors[c] = (cx + 340 * math.cos(ang), cy + 300 * math.sin(ang))
        size_of[c] = max(1, sum(1 for t in terms if t.get("cluster") == c))
    pos = {}
    by_id = {t["term_id"]: t for t in terms}
    for t in terms:
        c = t.get("cluster")
        ax, ay = anchors.get(c, (cx, cy))
        sp = 36 + 5.0 * size_of.get(c, 8)          # 大群初始撒得更开
        pos[t["term_id"]] = [ax + rnd.uniform(-sp, sp), ay + rnd.uniform(-sp, sp)]
    links = [(r["from_term"], r["to_term"]) for r in rels
             if r["from_term"] in pos and r["to_term"] in pos]
    ids = list(pos)
    for _ in range(iters):
        fx = dict.fromkeys(ids, 0.0)
        fy = dict.fromkeys(ids, 0.0)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                d2 = dx * dx + dy * dy
                if d2 < 1e-6:
                    dx, dy, d2 = rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1.0
                d = math.sqrt(d2)
                f = 1400.0 / d2
                ux, uy = dx / d, dy / d
                fx[a] += ux * f
                fy[a] += uy * f
                fx[b] -= ux * f
                fy[b] -= uy * f
        for a, b in links:
            dx = pos[b][0] - pos[a][0]
            dy = pos[b][1] - pos[a][1]
            d = math.hypot(dx, dy) or 1.0
            f = 0.06 * (d - 68)
            ux, uy = dx / d, dy / d
            fx[a] += ux * f
            fy[a] += uy * f
            fx[b] -= ux * f
            fy[b] -= uy * f
        for k in ids:
            c = by_id[k].get("cluster")
            ax, ay = anchors.get(c, (cx, cy))
            w = 0.055 * math.sqrt(10.0 / max(10, size_of.get(c, 8)))
            fx[k] += w * (ax - pos[k][0])
            fy[k] += w * (ay - pos[k][1])
            lim = min(14.0, 0.9 * min(width, height) / 40)
            pos[k][0] = max(44, min(width - 44, pos[k][0] + max(-lim, min(lim, fx[k]))))
            pos[k][1] = max(44, min(height - 44, pos[k][1] + max(-lim, min(lim, fy[k]))))
    return {k: [round(v[0], 1), round(v[1], 1)] for k, v in pos.items()}


def node_radii(terms, rels):
    """节点半径由度数决定，构建时算好，标签排布要用同一套数字。"""
    deg = Counter()
    for r in rels:
        deg[r["from_term"]] += 1
        deg[r["to_term"]] += 1
    return {t["term_id"]: round(min(13.0, 4.0 + math.sqrt(deg[t["term_id"]]) * 2.0), 2)
            for t in terms}


def _text_w(s, size=11.0):
    """粗略字宽：中日韩全角按 1em，其余按 0.55em。"""
    return sum(size if ord(ch) > 0x2E80 else size * (0.3 if ch == " " else 0.55)
               for ch in s)


def _text_box(anchor, lx, ly, w, h):
    """把「锚点 + 基线坐标」换算成矩形，用于重叠判定。"""
    top, bot = ly - h * 0.78, ly + h * 0.22
    if anchor == "middle":
        return (lx - w / 2, top, lx + w / 2, bot)
    if anchor == "start":
        return (lx, top, lx + w, bot)
    return (lx - w, top, lx, bot)


def place_labels(terms, pos, radius, width, height, size=11.0):
    """给每个节点挑一个不压其它标签的位置：构建时算好，且能被自检。

    候选顺序固定为「下、上、右、左」，取重叠代价最小者，同分取靠前的候选。
    不用随机数——同样的数据每次重建都得到同样的图。
    """
    placed = []
    circles = [(pos[t["term_id"]][0], pos[t["term_id"]][1], radius[t["term_id"]])
               for t in terms]
    out = {}
    order = sorted(terms, key=lambda t: (-radius[t["term_id"]], t["term_id"]))
    for t in order:
        tid = t["term_id"]
        x, y = pos[tid]
        r = radius[tid]
        w, h = _text_w(t["name_zh"], size), size * 1.3
        gap = 4.0
        cands = [
            ("middle", x, y + r + gap + h * 0.78),
            ("middle", x, y - r - gap + h * 0.22),
            ("start", x + r + gap, y + h * 0.28),
            ("end", x - r - gap, y + h * 0.28),
        ]
        best, best_pen = None, None
        for anchor, lx, ly in cands:
            pen = label_penalty(_text_box(anchor, lx, ly, w, h), placed,
                                circles, width, height)
            if best_pen is None or pen < best_pen:
                best, best_pen = (anchor, lx, ly), pen
            if best_pen == 0:
                break
        anchor, lx, ly = best
        out[tid] = [round(lx, 1), round(ly, 1), anchor]
        placed.append(_text_box(anchor, lx, ly, w, h))
    return out


def label_penalty(box, placed, circles, width, height):
    """代价：压到已有标签最重，越界次之，压到别的节点最轻。"""
    x0, y0, x1, y1 = box
    p = 0
    if x0 < 2 or x1 > width - 2 or y0 < 2 or y1 > height - 2:
        p += 50
    for b in placed:
        if x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1:
            p += 100
    for cx, cy, r in circles:
        dx = max(x0 - cx, 0.0, cx - x1)
        dy = max(y0 - cy, 0.0, cy - y1)
        if dx * dx + dy * dy < (r + 1.0) ** 2:
            p += 1
    return p


def content_box(terms, pos, radius, label, pad=34.0):
    """内容包围盒：节点圆 + 标签矩形，四周留一点边距，用来裁掉图内空白。"""
    xs, ys = [], []
    for t in terms:
        tid = t["term_id"]
        x, y = pos[tid]
        r = radius[tid]
        xs += [x - r, x + r]
        ys += [y - r, y + r]
        lx, ly, anchor = label[tid]
        w, h = _text_w(t["name_zh"]), 11.0 * 1.3
        b = _text_box(anchor, lx, ly, w, h)
        xs += [b[0], b[2]]
        ys += [b[1], b[3]]
    x0, y0 = min(xs) - pad, min(ys) - pad
    x1, y1 = max(xs) + pad, max(ys) + pad
    return [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]


def label_overlaps(terms, label, radius):
    """自检用：数一数最终还有几对标签互相压着。"""
    boxes = []
    for t in terms:
        lx, ly, anchor = label[t["term_id"]]
        w, h = _text_w(t["name_zh"]), 11.0 * 1.3
        boxes.append((t["term_id"], _text_box(anchor, lx, ly, w, h)))
    n = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                n += 1
    return n


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

    cluster_names = list(schema.get("clusters", {}))
    lay = layout(terms, rels, cluster_names)
    rad = node_radii(terms, rels)
    lab = place_labels(terms, lay, rad, NET_W, NET_H)
    view = content_box(terms, lay, rad, lab)
    payload = {
        "meta": {"terms": len(terms), "relations": len(rels), "cases": len(cases),
                 "hotspots": len(hots),
                 "polysemy": sum(1 for t in terms if t.get("polysemy"))},
        "enums": schema["enums"], "terms": terms,
        "clusters": schema.get("clusters", {}),
        "clusterOrder": cluster_names,
        "clusterColors": {c: CLUSTER_COLORS.get(c, "#6b6660") for c in cluster_names},
        "clusterOf": {t["term_id"]: t.get("cluster") for t in terms},
        "layout": lay, "radius": rad, "label": lab, "view": view,
        "size": [NET_W, NET_H],
    }

    # 布局自检：各概念群的重心两两之间应有足够距离，否则群在图上会糊成一团
    cents = {}
    for c in cluster_names:
        pts = [lay[t["term_id"]] for t in terms if t.get("cluster") == c]
        cents[c] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    for i, a in enumerate(cluster_names):
        for b in cluster_names[i + 1:]:
            d = math.dist(cents[a], cents[b])
            flag = "OK" if d > 180 else "过近，需调参"
            print(f"  布局自检：{a} ↔ {b} 重心距离 {d:.0f}　{flag}")
    ov = label_overlaps(terms, lab, rad)
    far = sum(1 for t in terms
              if math.dist(lab[t["term_id"]][:2], lay[t["term_id"]]) > 60)
    print(f"  布局自检：标签互相压叠 {ov} 对（应为 0）　·　离节点过远的标签 {far} 个（应为 0）")
    print(f"  视图裁切：画布 {NET_W}×{NET_H} → 内容 {view[2]:.0f}×{view[3]:.0f}"
          f"（省下 {100 - 100 * view[2] * view[3] / (NET_W * NET_H):.0f}% 的空白）")
    out = os.path.join(ROOT, "site")
    os.makedirs(out, exist_ok=True)
    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    path = os.path.join(out, "index.html")
    open(path, "w", encoding="utf-8").write(html)
    print(f"已生成 {path}（{len(html)/1024:.0f} KB，自包含，无外部依赖）")


if __name__ == "__main__":
    main()
