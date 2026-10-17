#!/usr/bin/env python3
"""生成静态检索页面 —— 无需服务器、无依赖，双击即可打开，也可直接托管。

用法：python3 build_site.py
输出：site/index.html（自包含，数据内嵌）
"""
import json, math, os, random, sys
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
/* 折叠区展开/收起时的高度过渡由脚本用 WAAPI 驱动（见 wireDetails），
   这里只需要裁掉动画过程中的溢出，避免文字从框里冒出来 */
details>ul{overflow:hidden}
details li{margin-bottom:7px;font-size:14px}
.poly li{padding-left:2px}
.who{font-weight:600}
.reltype{background:#eef1f5;color:#3c4a5c;border-radius:5px;padding:0 6px;font-size:12px;margin:0 3px}
.reltype.br{background:#fdf1e3;color:#8c5a2b;border:1px dashed #d99a4e}
a.t{color:var(--acc);cursor:pointer;text-decoration:none;border-bottom:1px dotted var(--acc)}
.case{color:var(--mut);font-size:13px}
.relblock{margin-bottom:9px}
.relhead{font-size:14px}
.note{display:block;font-size:13.5px;color:#3f3a33;margin-top:3px}
.bd{display:block;font-size:13px;color:#7a6a55;margin-top:2px}
.src{display:block;font-size:12.5px;color:var(--mut);margin-top:3px}
.src i{font-style:normal;opacity:.75}
.tagline{display:inline-block;font-size:11px;padding:0 6px;border-radius:7px;
  background:#eef1f5;color:#3c4a5c;margin-right:5px}
.tagline.me{background:#efe2d2;color:#8c5a2b}
.ok{display:block;color:#2f5d46;font-size:13px;margin-top:2px}
.hotbox{border-left:2px solid var(--line);padding-left:10px;margin-bottom:10px}
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
#gen{padding:18px 28px 48px;display:none;max-width:1240px}
#gen svg{width:100%;height:auto;display:block}
.genbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.genbar select{padding:7px 10px;border:1px solid var(--line);border-radius:8px;
  background:#fff;font:inherit;font-size:13px;color:var(--fg)}
.genbar .hint{color:var(--mut);font-size:12.5px}
.genlane{fill:none;stroke:#e9e3d8;stroke-width:1}
.genlane-lbl{font-size:12px;fill:#57514a;font-weight:600}
.genyear{font-size:10.5px;fill:var(--mut)}
.genauthor{font-size:12px;fill:var(--fg)}
.gendot{fill:#fff;stroke:#8c5a2b;stroke-width:1.6;cursor:pointer}
.gendot.fork{stroke-width:2.6}
.gendot.pick{fill:var(--acc)}
.genring{fill:none;stroke:#8c5a2b;stroke-width:1;opacity:.45}
.gene{fill:none;stroke:#b9b1a4;stroke-width:1.2}
.gene.cross{stroke:#bf7a26;stroke-dasharray:4 3}
.genetype{font-size:10px;fill:var(--mut)}
.genetype.cross{fill:#a5681f}
.gendet{margin-top:6px;padding:12px 15px;border:1px solid var(--line);border-radius:9px;
  background:#fff;font-size:13.5px;line-height:1.75}
.gendet b{color:var(--acc);font-weight:600}
.gendet .src{display:block;color:var(--mut);font-size:12.5px;margin-top:4px}
.genwrap .lin{border-left:2px solid var(--line);padding:2px 0 2px 14px;margin:14px 0 4px}
.genwrap .linh{font-weight:600;font-size:14px;color:var(--fg)}
.genwrap .linq{color:var(--mut);font-size:12.5px;margin:3px 0 6px}
.genwrap .thesis{margin:0 0 4px;font-size:13.5px}
.genwrap .blind{margin:0 0 8px;font-size:12.5px;color:#6b6660}
.genwrap ol.stages{list-style:none;padding-left:0;margin:0}
.genwrap li.stage{padding:5px 0 5px 0;font-size:13px;border-top:1px dotted var(--line)}
.genwrap li.stage b{color:var(--acc);font-weight:600;margin-right:6px}
.genwrap li.stage .claim{display:block;color:#57514a;font-size:12.5px;margin-top:2px}
.genwrap li.chg{font-size:12.5px;color:#8a6740;padding:4px 0 4px 12px;border-left:2px solid #e6d3b8;margin:2px 0}
.genwrap .linbtn{margin-top:12px;border:1px solid var(--acc);background:#fff;color:var(--acc);
  border-radius:8px;padding:6px 13px;font:inherit;font-size:13px;cursor:pointer}
.genwrap .linbtn:hover{background:var(--acc);color:#fff}
#graph svg{width:100%;height:auto;display:block}
/* 窄屏上整张图会被缩到看不清标签，改为保持可读宽度、允许横向平移 */
@media (max-width:820px){
  #graph{overflow-x:auto;-webkit-overflow-scrolling:touch;padding:10px 14px 30px}
  #graph svg{width:760px;height:auto}
}
/* 群内连线用该群的颜色、压暗；跨群桥接用橙色虚线并压在最上层，
   一眼就能看出「哪几处是概念群之间的桥」 */
.e{stroke-width:1.3;opacity:.42}
.e.br{stroke:#c9822b;stroke-width:2.2;stroke-dasharray:6 4;opacity:1;
  /* 虚线流动：跨群桥接是「少数、需要留意」的那类边，让它自己动起来 */
  animation:dashflow 1.8s linear infinite}
@keyframes dashflow{to{stroke-dashoffset:-20}}
.lead{stroke-width:1;opacity:.4}
.gnode{cursor:pointer}
/* 悬停聚焦：只留这个节点和它的邻居，其余压暗——68 个节点谁也看不清谁 */
.e,.gnode{transition:opacity .18s ease}
#graph.focusing .e:not(.on),#graph.focusing .gnode:not(.on){opacity:.1}
#graph.focusing .gnode.on circle{stroke:var(--fg);stroke-width:1.6}
@media (prefers-reduced-motion:reduce){
  .e.br{animation:none}
  .e,.gnode{transition:none}
}
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
    <button class="vbtn" id="vGen">谱系</button>
  </div>
</div>
<div class="legend" id="legend"></div>
<main id="list"></main>
<div id="graph"></div>
<div id="gen"></div>
<footer id="foot"></footer>
<script>
const DATA = __DATA__;
const S = {cluster:new Set(), school:new Set(), app:new Set(), q:'', view:'list', anchor:null};
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;

// 邻接表：悬停聚焦用。关系已经在数据里，不另外存一份
const NB = {};
DATA.terms.forEach(t => { NB[t.term_id] = new Set([t.term_id,
  ...(t.rel_out || []).map(r => r.other_id),
  ...(t.rel_in  || []).map(r => r.other_id)]); });

// 折叠区的高度过渡：details 原生的开合是瞬间跳变，量一下内容高度再补间
function wireDetails(){
  document.querySelectorAll('details').forEach(d => {
    const box = d.querySelector(':scope > ul');
    if (!box) return;
    d.querySelector('summary').addEventListener('click', e => {
      if (RM) return;                        // 关掉动画偏好时，退回浏览器原生开合
      e.preventDefault();
      box.getAnimations().forEach(a => a.cancel());   // 连点两下时不叠加
      const h = box.offsetHeight;
      if (!d.open){
        d.open = true;
        const h2 = box.offsetHeight;      // 打开后才量得到自然高度
        box.animate([{height:'0px'},{height:h2+'px'}],
                    {duration:200, easing:'cubic-bezier(.2,.7,.2,1)'});
        // 逐条渐显：按阅读顺序，每条晚 38ms 上浮，最多叠 5 层
        [...box.children].forEach((el, i) => el.animate(
          [{opacity:0, transform:'translateY(6px)'}, {opacity:1, transform:'none'}],
          {duration:180, delay:Math.min(i, 5) * 38, fill:'backwards',
           easing:'cubic-bezier(.2,.7,.2,1)'}));
      } else {
        box.animate([{height:h+'px',opacity:1},{height:'0px',opacity:0}],
                    {duration:170, easing:'cubic-bezier(.4,0,.6,1)'})
           .onfinish = () => { d.open = false; };
      }
    });
  });
}

function chips(el, values, field, key){
  const cnt = {};
  DATA.terms.forEach(t => (t[field]||[]).forEach(v => cnt[v]=(cnt[v]||0)+1));
  el.innerHTML = values.filter(v => cnt[v]).map(v =>
    `<button class="chip" data-v="${v}">${v}<i>${cnt[v]}</i></button>`).join('');
  el.querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const v = b.dataset.v;
    S[key].has(v) ? S[key].delete(v) : S[key].add(v);
    b.classList.toggle('on');
    render(true);
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
  const block = (r, dir) => {
    // 桥接与否由两端的 cluster 推出，不写死在数据里：术语换了概念群，这里跟着变
    const br = DATA.clusterOf[t.term_id] !== DATA.clusterOf[r.other_id]
      ? '<span class="reltype br">跨群桥接</span>' : '';
    const head = dir === 'out'
      ? `本条目<span class="reltype">${esc(r.type)}</span>${br}→ <a class="t" data-j="${r.other_id}">${esc(r.other)}</a>`
      : `<a class="t" data-j="${r.other_id}">${esc(r.other)}</a><span class="reltype">${esc(r.type)}</span>${br}→ 本条目`;
    return `<div class="relblock"><div class="relhead">${head}</div>` +
      `<span class="note"><span class="tagline me">编者解读</span>${esc(r.explain || '')}</span>` +
      (r.boundary ? `<span class="bd"><span class="tagline">边界</span>${esc(r.boundary)}</span>` : '') +
      `<span class="src"><i>证据</i>　${esc(r.evidence || '')}<br><i>出处</i>　${esc(r.source || '')}</span>` +
      `</div>`;
  };
  t.rel_out.forEach(r => out.push(block(r, 'out')));
  t.rel_in.forEach(r => out.push(block(r, 'in')));
  return out.length ? out.join('') : '<li class="case">暂无</li>';
}

function genBlock(t){
  const g = t.gen;
  if (!g) return '';
  const n = g.lineages.reduce((s,l) => s + l.stages.length, 0);
  const body = g.lineages.map(l => {
    const stages = l.stages.map(s => {
      // 入边画在「后一版」前面：它描述的不是这一版是什么，而是这一版改掉了什么
      const ins = s.ins.map(e =>
        `<li class="chg">${e.cross ? '<span class="reltype br">跨脉</span>' : ''}` +
        `<span class="reltype">${esc(e.type)}</span>${esc(e.changed)}</li>`).join('');
      return ins + `<li class="stage"><b>${s.year}</b>${esc(s.author)}` +
        `<span class="wk">　${esc(s.work)}</span>` +
        `<span class="claim">${esc(s.claim)}</span></li>`;
    }).join('');
    return `<div class="lin"><div class="linh">${esc(l.name)}</div>` +
      `<p class="linq">这一脉问的是：${esc(l.question)}</p>` +
      `<p class="thesis">${esc(l.thesis)}</p>` +
      `<p class="blind"><span class="tagline">看不见</span>${esc(l.blind)}</p>` +
      `<ol class="stages">${stages}</ol></div>`;
  }).join('');
  return `<details class="genwrap"><summary>谱系（${g.lineages.length} 脉 · ${n} 个版本）</summary>` +
    `<div class="genbody">${body}` +
    `<button class="linbtn" data-j="${t.term_id}">◎ 以本术语为中心看谱系图</button></div></details>`;
}

function card(t){
  const poly = (t.polysemy||[]).length ? t.polysemy.map(p => `
    <li><span class="who">${esc(p.author)}</span>：${esc(p.definition)}
      ${p.differs_from?`<span class="case">（与 ${esc(p.differs_from)} 不同：${esc(p.note||'')}）</span>`:''}
    </li>`).join('') : '<li class="case">本条无多义性记录</li>';
  const cases = t.cases.length ? t.cases.map(c => `
    <li><span class="who">${esc(c.title)}</span><span class="case">　${esc(c.origin)}</span>
      ${c.match?`<span class="ok">相符之处：${esc(c.match)}</span>`:''}
      ${c.mismatch?`<span class="mism">不符之处：${esc(c.mismatch)}</span>`:''}</li>`).join('')
    : '<li class="case">暂无</li>';
  const hots = t.hotspots.length ? t.hotspots.map(h => `
    <li class="hotbox"><span class="who">${esc(h.title)}</span>
      <span class="case">　${h.date} · ${h.confidence}</span>
      <span class="ok">相符之处：${esc(h.match || '')}</span>
      <span class="mism">不符之处：${esc(h.mismatch)}</span>
      ${h.analysis?`<span class="note"><span class="tagline me">解析</span>${esc(h.analysis)}</span>`:''}
      ${h.dissent?`<span class="case">分歧：${esc(h.dissent)}</span>`:''}</li>`).join('')
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
    ${(t.polysemy||[]).length ? `<details><summary>多义性（${t.polysemy.length}）</summary><ul class="poly">${poly}</ul></details>` : ''}
    ${t.gen ? genBlock(t) : ''}
    ${t.rel_out.length + t.rel_in.length ? `<details><summary>概念关系（${t.rel_out.length + t.rel_in.length}）</summary><ul>${relRow(t)}</ul></details>` : ''}
    ${t.cases.length ? `<details><summary>经典案例（${t.cases.length}）</summary><ul>${cases}</ul></details>` : ''}
    ${t.hotspots.length ? `<details><summary>社会热点（${t.hotspots.length}）</summary><ul>${hots}</ul></details>` : ''}
  </div>`;
}

// 筛选后的位置补间（FLIP）：卡片不是重新排一遍，而是从原来的位置滑过去。
// 只在 chip 切换时用——搜索是逐键触发，每敲一个字都补间会显得抖
function render(flip){
  const prev = new Map();
  document.querySelectorAll('#list .card').forEach(c =>
    prev.set(c.id, c.getBoundingClientRect().top + window.scrollY));
  const list = DATA.terms.filter(matched).sort((a,b)=>a.first_year-b.first_year);
  document.getElementById('list').innerHTML = list.length
    ? list.map(card).join('') : '<div class="empty">没有符合条件的术语</div>';
  document.getElementById('foot').textContent =
    `显示 ${list.length} / ${DATA.terms.length} 条术语　·　数据状态：出处已登记作者与书目，${DATA.meta.drafts} 条尚未逐条复核`;
  document.querySelectorAll('a.t').forEach(a => a.onclick = () => {
    const el = document.getElementById('t-' + a.dataset.j);
    if (el){ el.scrollIntoView({behavior:'smooth',block:'center'});
             el.classList.add('hl'); setTimeout(()=>el.classList.remove('hl'),1600); }
  });
  document.querySelectorAll('.linbtn').forEach(b => b.onclick = e => {
    e.preventDefault(); openGen(b.dataset.j);
  });
  wireDetails();
  if (flip && !RM) document.querySelectorAll('#list .card').forEach(c => {
    const was = prev.get(c.id);
    if (was == null) return;                       // 新出现的卡片没有起点，直接落下
    const dy = Math.round(was - (c.getBoundingClientRect().top + window.scrollY));
    if (Math.abs(dy) < 2) return;
    c.animate([{transform:`translateY(${dy}px)`}, {transform:'none'}],
              {duration:220, easing:'cubic-bezier(.2,.7,.2,1)'});
  });
}

document.getElementById('sub').textContent =
  `${DATA.clusterOrder.length} 个概念群　·　术语之间以「关系」相连成网，` +
  `跨概念群处是桥接：网络视图里是橙色虚线，词条的关系条目上带「跨群桥接」标签　·　点节点可跳到词条　·　` +
  `谱系视图把同一个词的历代定义按年份与血脉排开`;

document.getElementById('stats').innerHTML = [
  ['术语', DATA.meta.terms], ['概念关系', DATA.meta.relations],
  ['经典案例', DATA.meta.cases], ['社会热点', DATA.meta.hotspots],
  ['多义性条目', DATA.meta.polysemy],
  ['谱系版本', DATA.meta.versions]
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
    draw(true);                      // 三组筛选行为一致：都走位置补间
  });
}

function legend(){
  document.getElementById('legend').innerHTML = DATA.clusterOrder.map(c =>
    `<div><span class="dot" style="background:${DATA.clusterColors[c]}"></span>` +
    `<b>${esc(c)}</b>　${esc(DATA.clusters[c]||'')}</div>`).join('');
}

function gotoCard(id){
  S.view = 'list';
  setViewBtns('list');
  draw();
  const el = document.getElementById('t-' + id);
  if (el){ el.scrollIntoView({behavior:'smooth', block:'center'});
           el.classList.add('hl'); setTimeout(()=>el.classList.remove('hl'), 1800); }
}

function focusNode(id){
  const g = document.getElementById('graph'), nb = NB[id] || new Set([id]);
  g.classList.add('focusing');
  g.querySelectorAll('.gnode').forEach(n => n.classList.toggle('on', nb.has(n.dataset.j)));
  g.querySelectorAll('.e').forEach(e => e.classList.toggle('on', e.dataset.a === id || e.dataset.b === id));
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
      `<line class="e${isBr ? ' br' : ''}" data-a="${t.term_id}" data-b="${r.other_id}"` +
      `${isBr ? '' : ` style="stroke:${col}"`}` +
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
  // 悬停聚焦：把「这个点和谁相连」从读标签变成看得见
  const gEl = document.getElementById('graph');
  gEl.querySelectorAll('.gnode').forEach(n => {
    n.onmouseenter = () => focusNode(n.dataset.j);
    n.onmouseleave = () => gEl.classList.remove('focusing');
  });
  document.getElementById('foot').textContent =
    `网络视图：${list.length} 个节点　·　实线＝群内关系（按概念群着色），橙色虚线＝跨概念群桥接　·　点节点可跳到词条`;
}

function openGen(id){
  S.anchor = id; S.view = 'gen';
  setViewBtns('gen');
  draw();
  const f = document.querySelector('.filters');
  if (f) window.scrollTo({top: f.offsetTop, behavior: RM ? 'auto' : 'smooth'});
}

function renderGen(){
  const list = DATA.terms.filter(t => t.gen);
  const host = document.getElementById('gen');
  if (!list.length){ host.innerHTML = '<div class="empty">还没有任何术语登记谱系</div>'; return; }
  const cur = list.find(t => t.term_id === S.anchor) || list[0];
  S.anchor = cur.term_id;
  const g = cur.gen;

  // 所有谱系共用一个年份刻度：若每条脉各自拉伸，两条脉的先后关系会被压掉，
  // 看上去像同时发生——而先后正是谱系唯一要说的事
  const years = g.lineages.flatMap(l => l.stages.map(s => +s.year));
  let lo = Math.min(...years), hi = Math.max(...years);
  if (hi === lo){ lo -= 4; hi += 4; }
  const W = 1000, X0 = 158, X1 = W - 52;
  const x = y => X0 + (y - lo) / (hi - lo) * (X1 - X0);
  const TOP = 74, LANE = 112;
  const H = TOP + g.lineages.length * LANE + 26;
  const laneY = i => TOP + i * LANE + 30;

  // 相邻版本年份太近时（如涂尔干 1893 与 1897），标签必然叠在一起：
  // 错开成上下两行，而不是把时间轴拉开——拉开就等于说谎
  const rowOf = {};
  g.lineages.forEach(l => {
    let lastX = -1e9, flip = false;
    l.stages.forEach(s => {
      const px = x(+s.year);
      if (px - lastX < 96) flip = !flip;
      rowOf[s.id] = flip ? 1 : 0;
      lastX = px;
    });
  });
  const off = id => rowOf[id] ? {yr: -34, au: 40} : {yr: -16, au: 22};

  const pos = {};
  g.lineages.forEach((l, i) => l.stages.forEach(s => {
    pos[s.id] = {x: x(+s.year), y: laneY(i), lane: i, s, l};
  }));

  const P = [];
  g.lineages.forEach((l, i) => {
    const y = laneY(i);
    P.push(`<line class="genlane" x1="${X0}" y1="${y}" x2="${X1}" y2="${y}"/>`);
    P.push(`<text class="genlane-lbl" x="12" y="${y - 10}">${esc(l.name)}</text>`);
    P.push(`<text class="genyear" x="12" y="${y + 7}">${l.stages.length} 个版本</text>`);
  });

  g.lineages.forEach(l => l.stages.forEach(s => s.ins.forEach(e => {
    const a = pos[e.from], b = pos[s.id];
    if (!a || !b) return;
    const cross = a.lane !== b.lane, mx = (a.x + b.x) / 2, span = Math.abs(b.x - a.x);
    // 同一泳道内，边与泳道线必然重合：拱起来才看得出这是一条边而不是参考线。
    // 拱高随跨度收缩，短边不会顶到上一行的年份标签
    // 拱高必须留出泳道上方的那点空间：超过它，弧顶会被 viewBox 裁掉，
    // 看上去像「这条边断成两截」
    const h = Math.min(56, Math.max(22, span * 0.20));
    const d = cross
      ? `M${a.x},${a.y} C${mx},${a.y} ${mx},${b.y} ${b.x},${b.y}`
      : `M${a.x},${a.y} Q${mx},${a.y - h * 2} ${b.x},${b.y}`;
    P.push(`<path class="gene${cross ? ' cross' : ''}" data-a="${e.from}" data-b="${s.id}" d="${d}"/>`);
    // 跨度太小的时候标在弧顶只会压住年份；这类边交给词条里的谱系列表去读
    if (cross || span >= 70)
      P.push(`<text class="genetype${cross ? ' cross' : ''}" x="${mx}"` +
        ` y="${cross ? (a.y + b.y) / 2 - 5 : a.y - h - 8}"` +
        ` style="text-anchor:middle;paint-order:stroke;stroke:#fbfaf7;stroke-width:3px">${esc(e.type)}</text>`);
  })));

  g.lineages.forEach(l => l.stages.forEach(s => {
    const p = pos[s.id];
    const o = off(s.id);
    if (s.fork) P.push(`<circle class="genring" cx="${p.x}" cy="${p.y}" r="12"/>`);
    P.push(`<text class="genyear" x="${p.x}" y="${p.y + o.yr}" style="text-anchor:middle">${s.year}</text>`);
    P.push(`<g class="gnode2" data-j="${s.id}">` +
      `<circle class="gendot${s.fork ? ' fork' : ''}" cx="${p.x}" cy="${p.y}" r="6"/>` +
      `<text class="genauthor" x="${p.x}" y="${p.y + o.au}" style="text-anchor:middle">${esc(s.author)}</text></g>`);
  }));

  const nVer = g.lineages.reduce((s,l) => s + l.stages.length, 0);
  host.innerHTML =
    `<div class="genbar"><select id="genSel">` +
    list.map(t => `<option value="${t.term_id}"${t.term_id === cur.term_id ? ' selected' : ''}>` +
      `${esc(t.name_zh)}（${t.gen.lineages.length} 脉 / ` +
      `${t.gen.lineages.reduce((s,l)=>s+l.stages.length,0)} 版）</option>`).join('') +
    `</select><span class="hint">横轴＝年份，每条泳道＝一条血脉，橙色虚线＝跨脉改写，带圈的点＝分叉点</span></div>` +
    `<svg viewBox="0 0 ${W} ${H}">${P.join('')}</svg>` +
    `<div class="gendet" id="genDet">点任一个版本，看它改掉了什么。</div>`;

  document.getElementById('genSel').onchange = e => { S.anchor = e.target.value; renderGen(); };
  const det = document.getElementById('genDet');
  host.querySelectorAll('.gnode2').forEach(n => n.onclick = () => {
    const s = pos[n.dataset.j].s;
    det.innerHTML = `<b>${s.year} · ${esc(s.author)}</b>　${esc(s.work)}<br>${esc(s.claim)}` +
      (s.ins.length
        ? s.ins.map(e => `<span class="src">${esc(e.type)}${e.cross ? '（跨脉）' : ''}：` +
            `${esc(e.changed)}${e.evidence ? '｜证据：' + esc(e.evidence) : ''}</span>`).join('')
        : `<span class="src">这条谱系的起点，没有前一个版本。</span>`);
    host.querySelectorAll('.gendot').forEach(c => c.classList.remove('pick'));
    n.querySelector('.gendot').classList.add('pick');
  });
  document.getElementById('foot').textContent =
    `谱系视图：${cur.name_zh}　·　${g.lineages.length} 条血脉、${nVer} 个版本　·　` +
    `分叉点由「一个版本有几条出边」推出，不单独存字段`;
}

// flip 只在「筛选条件变了、而列表本身还留着」时传 true；
// 换视图、搜索、跳词条都传默认值，避免每次重排都补间
function draw(flip){
  const v = S.view;
  document.getElementById('list').style.display  = v === 'list'  ? '' : 'none';
  document.getElementById('graph').style.display = v === 'graph' ? 'block' : 'none';
  document.getElementById('gen').style.display   = v === 'gen'   ? 'block' : 'none';
  if (v === 'graph') renderGraph();
  else if (v === 'gen') renderGen();
  else render(flip);
}

function setViewBtns(v){
  ['vList','vGraph','vGen'].forEach(k =>
    document.getElementById(k).classList.toggle('on', k === 'v' + v[0].toUpperCase() + v.slice(1)));
}

document.getElementById('vList').onclick  = () => { S.view = 'list';  setViewBtns('list');  draw(); };
document.getElementById('vGraph').onclick = () => { S.view = 'graph'; setViewBtns('graph'); draw(); };
document.getElementById('vGen').onclick   = () => { S.view = 'gen';   setViewBtns('gen');   draw(); };

clusterChips(document.getElementById('fCluster'));
chips(document.getElementById('fSchool'), DATA.enums.school, 'school', 'school');
chips(document.getElementById('fApp'), DATA.enums.application, 'application', 'app');
document.getElementById('q').oninput = e => { S.q = e.target.value.trim(); draw(); };
legend();
setViewBtns(S.view);
draw();
</script>
</body>
</html>
"""


# 概念群配色：每个群一种色相，靠颜色区分群，不靠位置。
# 六个群必须六种颜色——少一种就会静默落到 FALLBACK_COLOR，图上两个群变成同一个颜色，
# 而这种错误不会让任何校验失败，只会让读图的人看不懂。所以下面有配色自检。
CLUSTER_COLORS = {
    "社会不平等": "#8c5a2b",
    "社会秩序与越轨": "#3c6e71",
    "社会行动与理性化": "#7a5c9e",
    "城市、空间与社区": "#3f6fa8",
    "性别、家庭与照护": "#a8567a",
    "知识、文化与意义": "#6d8c3f",
}
FALLBACK_COLOR = "#6b6660"
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
        # 三圈候选：近圈放不下就往外挪，最远一圈也不超过「离节点过远」的 60px 上限。
        cands = []
        for extra in (0.0, 15.0, 30.0):
            g = gap + extra
            cands += [
                ("middle", x, y + r + g + h * 0.78),
                ("middle", x, y - r - g + h * 0.22),
                ("start", x + r + g, y + h * 0.28),
                ("end", x - r - g, y + h * 0.28),
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
        edge = {"type": r["type"], "evidence": r.get("evidence"),
                "explain": r.get("explain"), "boundary": r.get("boundary"),
                "source": r.get("source")}
        if r["from_term"] in by_id:
            by_id[r["from_term"]]["rel_out"].append(
                dict(edge, other=name.get(r["to_term"], r["to_term"]),
                     other_id=r["to_term"]))
        if r["to_term"] in by_id:
            by_id[r["to_term"]]["rel_in"].append(
                dict(edge, other=name.get(r["from_term"], r["from_term"]),
                     other_id=r["from_term"]))

    for c in cases:
        for a in c["attributions"]:
            if a["term_id"] in by_id:
                by_id[a["term_id"]]["cases"].append(
                    {"title": c["title"], "origin": c["origin"],
                     "match": a.get("match"), "mismatch": a["mismatch"]})
    for h in hots:
        for a in h["attributions"]:
            if a["term_id"] in by_id:
                by_id[a["term_id"]]["hotspots"].append(
                    {"title": h["title"], "date": h["date"],
                     "confidence": a["confidence"], "match": a.get("match"),
                     "mismatch": a["mismatch"], "analysis": h.get("analysis"),
                     "dissent": a.get("dissent")})

    # 谱系：按术语分组，每个版本按年份排；入边挂在「后一版」上，因为它描述的是这次改动
    gen_raw = load("genealogy.yaml") or {}
    if not isinstance(gen_raw, dict):
        gen_raw = {}
    node_by_id = {n["node_id"]: n for n in gen_raw.get("nodes", [])}
    in_edges, out_deg = {}, Counter()
    for e in gen_raw.get("edges", []):
        in_edges.setdefault(e["to"], []).append(e)
        out_deg[e["from"]] += 1

    gen = {}
    for l in gen_raw.get("lineages", []):
        stages = []
        for n in sorted([n for n in gen_raw.get("nodes", [])
                         if n["lineage_id"] == l["lineage_id"]],
                        key=lambda n: (n["year"], n["node_id"])):
            stages.append({
                "id": n["node_id"], "author": n["author"], "year": n["year"],
                "work": n["work"], "claim": n["claim"],
                # 分叉从拓扑推出：一个版本若有多条出边，它就是两条血脉的分岔点
                "fork": out_deg[n["node_id"]] >= 2,
                "ins": [{"type": e["type"], "changed": e["what_changed"],
                         "evidence": e.get("evidence"), "source": e.get("source"),
                         "from": e["from"],
                         "from_lineage": node_by_id[e["from"]]["lineage_id"],
                         "cross": node_by_id[e["from"]]["lineage_id"] != l["lineage_id"]}
                        for e in in_edges.get(n["node_id"], [])],
            })
        gen.setdefault(l["term_id"], {"lineages": []})["lineages"].append({
            "id": l["lineage_id"], "name": l["name"], "question": l["question"],
            "thesis": l["thesis"], "blind": l["blind_spot"], "stages": stages})
    for t in terms:
        if t["term_id"] in gen:
            t["gen"] = gen[t["term_id"]]

    cluster_names = list(schema.get("clusters", {}))
    lay = layout(terms, rels, cluster_names)
    rad = node_radii(terms, rels)
    lab = place_labels(terms, lay, rad, NET_W, NET_H)
    view = content_box(terms, lay, rad, lab)
    payload = {
        "meta": {"terms": len(terms), "relations": len(rels), "cases": len(cases),
                 "hotspots": len(hots),
                 "polysemy": sum(1 for t in terms if t.get("polysemy")),
                 "gen_terms": len(gen),
                 "lineages": len(gen_raw.get("lineages", [])),
                 "versions": len(gen_raw.get("nodes", [])),
                 "drafts": sum(1 for t in terms if t.get("status") == "草稿")},
        "enums": schema["enums"], "terms": terms,
        "clusters": schema.get("clusters", {}),
        "clusterOrder": cluster_names,
        "clusterColors": {c: CLUSTER_COLORS.get(c, FALLBACK_COLOR) for c in cluster_names},
        "clusterOf": {t["term_id"]: t.get("cluster") for t in terms},
        "layout": lay, "radius": rad, "label": lab, "view": view,
        "size": [NET_W, NET_H],
    }

    # 配色自检：缺配色或多群撞色都会让网络视图不可读，且不会触发任何数据校验
    missing = [c for c in cluster_names if c not in CLUSTER_COLORS]
    dupes = [col for col, n in Counter(CLUSTER_COLORS[c] for c in cluster_names
                                       if c in CLUSTER_COLORS).items() if n > 1]
    if missing or dupes:
        for c in missing:
            print(f"  配色自检：概念群「{c}」没有配色，会落到默认灰 —— 请在 CLUSTER_COLORS 里补一个")
        for col in dupes:
            print(f"  配色自检：颜色 {col} 被多个概念群共用 —— 图上会分不出群")
        sys.exit("配色自检不通过：概念群与配色必须一一对应。")
    print(f"  配色自检：{len(cluster_names)} 个概念群各自独立配色　OK")

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
