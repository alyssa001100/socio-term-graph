#!/usr/bin/env python3
"""生成四页静态站 —— 无需服务器、无依赖，双击即可打开，也可直接托管。

用法：python3 build_site.py
输出：site/index.html / terms.html / network.html / lineages.html（各自自包含，数据内嵌）
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
<title>__PAGE_TITLE__</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23e7a319'/%3E%3Cpath d='M32 10l19 11v22L32 54 13 43V21z' fill='%23000'/%3E%3C/svg%3E">
<style>
:root{
  --bg:#f3f5f6;--fg:#000;--mut:#52606d;--line:#d1d6dc;--steel:#a1abb5;
  --acc:#a15c00;--amber:#e7a319;--chip:#fff;--paper:#fff;--hero:#e7a319;
  --mono:"SFMono-Regular","Cascadia Mono","Roboto Mono",Menlo,Consolas,monospace;
  --sans:-apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --serif:"Italiana","Bodoni 72",Didot,Georgia,"Songti SC",serif;
  --script:"Snell Roundhand","Apple Chancery","Marck Script","STKaiti",cursive;
}
*{box-sizing:border-box}
html{overscroll-behavior:none}
@view-transition{navigation:auto}
::view-transition-old(root),::view-transition-new(root){animation-duration:.24s}
body{margin:0;background-color:var(--bg);color:var(--fg);
  background-image:
    linear-gradient(rgba(161,171,181,.15) 1px,transparent 1px),
    linear-gradient(90deg,rgba(161,171,181,.15) 1px,transparent 1px),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='104' height='104'%3E%3Cpath d='M26.5 18.5v16M18.5 26.5h16' stroke='%23a1abb5' stroke-opacity='.4' stroke-width='.7'/%3E%3C/svg%3E");
  background-size:26px 26px,26px 26px,104px 104px;
  font:14px/1.75 var(--sans);-webkit-font-smoothing:antialiased}
::selection{background:#000;color:#fff}
header{padding:0 28px;border-bottom:1px solid var(--fg);background:rgba(243,245,246,.72)}
.topline{display:flex;align-items:center;justify-content:space-between;gap:20px;
  padding:17px 0;border-bottom:1px solid rgba(0,0,0,.14);
  font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase}
.brand{display:flex;align-items:center;gap:11px;min-width:0}
.mark{width:19px;height:19px;flex:0 0 19px;background:var(--amber);
  clip-path:polygon(50% 0,100% 28%,100% 72%,50% 100%,0 72%,0 28%);
  box-shadow:0 0 0 1px rgba(0,0,0,.18)}
.brand-cn{font-family:var(--sans);font-size:12px;font-weight:600;letter-spacing:.08em;white-space:nowrap}
.brand-en{color:var(--mut);white-space:nowrap}
.topmeta{color:var(--mut);white-space:nowrap}
.topmeta .plus{color:var(--amber);font-size:15px;vertical-align:-1px;margin-left:7px}
a.brand{text-decoration:none;color:inherit}
.sitenav{display:flex;align-items:center;gap:18px;flex-wrap:wrap;
  font-family:var(--mono);font-size:9px;letter-spacing:.11em;text-transform:uppercase}
.sitenav a{color:var(--mut);text-decoration:none;border-bottom:1px solid transparent;
  padding-bottom:2px;transition:color .14s,border-color .14s}
.sitenav a:hover{color:#000;border-bottom-color:var(--amber)}
body.page-terms .sitenav a[data-nav="terms"],
body.page-network .sitenav a[data-nav="network"],
body.page-lineages .sitenav a[data-nav="lineages"]{color:#000;border-bottom-color:var(--amber)}
.hero{padding:42px 0 28px;max-width:1060px}
.kicker{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--mut)}
h1{margin:10px 0 19px;font-family:var(--sans);font-size:clamp(40px,6.2vw,74px);
  line-height:1.02;letter-spacing:-.045em;font-weight:600}
h1 span{display:block;color:var(--mut);font-size:.58em;line-height:1.08;letter-spacing:.01em;margin-top:4px}
.sub{max-width:860px;margin:0;color:var(--mut);font-family:var(--mono);
  font-size:11px;line-height:1.95;letter-spacing:.045em}
.stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));
  border-top:1px solid var(--fg);border-bottom:1px solid var(--fg);margin-top:30px}
.stat{padding:13px 12px 11px;border-right:1px solid var(--line);min-width:0}
.stat:last-child{border-right:0}
.statno{display:block;font-family:var(--mono);font-size:9px;color:var(--steel);letter-spacing:.08em}
.stat b{display:block;font-family:var(--mono);font-size:24px;line-height:1.12;font-weight:500;margin:2px 0 3px}
.statlabel{display:block;font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* 多页壳：home 只显示入场层与三纪走廊；terms / network / lineages 只显示各自的工具层。 */
.home-hero,.home-index{display:none}
body.page-home .app-header,
body.page-home .filters,body.page-home .legend,body.page-home .sectionhead,
body.page-home main,body.page-home #graph,body.page-home #lins,body.page-home footer{display:none!important}
body.page-terms .strata,body.page-network .strata,body.page-lineages .strata{display:none!important}
body.page-terms .app-header .hero,body.page-network .app-header .hero,body.page-lineages .app-header .hero,
body.page-terms .app-header .stats,body.page-network .app-header .stats,body.page-lineages .app-header .stats{display:none}
/* 子页面页头：每个页面只保留自己的标题、问题与规模，不再复用首页大标题。 */
.subhead{display:none;border-bottom:1px solid var(--line);background:rgba(243,245,246,.72)}
body.page-terms .subhead,body.page-network .subhead,body.page-lineages .subhead{display:block}
.subhead-in{max-width:1184px;margin:0 auto;padding:46px 28px 30px;display:grid;
  grid-template-columns:minmax(0,1.15fr) minmax(330px,.85fr);gap:56px;align-items:end}
.subhead .kicker::before{content:"";display:inline-block;width:24px;height:1px;background:var(--amber);
  vertical-align:3px;margin-right:10px}
.subhead h1{margin:7px 0 0;font-size:clamp(48px,6vw,86px);line-height:.98;letter-spacing:-.05em}
.subhead h1 span{display:block;color:var(--mut);font-family:var(--mono);font-size:.28em;
  line-height:1.2;letter-spacing:.16em;font-weight:400;margin-top:12px}
.subhead-desc{margin:0;color:var(--mut);font-family:var(--mono);font-size:11px;
  line-height:1.9;letter-spacing:.035em}
.subhead-metrics{display:flex;border-top:1px solid var(--fg);margin-top:20px}
.subhead-metric{flex:1;min-width:0;padding:11px 14px 0 0;border-right:1px solid var(--line)}
.subhead-metric:last-child{border-right:0;padding-right:0}
.subhead-metric b{display:block;font-family:var(--mono);font-size:24px;line-height:1.1;font-weight:500}
.subhead-metric span{display:block;margin-top:3px;font-family:var(--mono);font-size:8.5px;
  letter-spacing:.13em;color:var(--mut);text-transform:uppercase;white-space:nowrap}
/* 入场层：参考稿的整屏色块、居中排版与底部渐隐，但换成本站的琥珀色。 */
.home-hero{min-height:100vh;background:var(--hero);color:#000;flex-direction:column;position:relative}
body.page-home .home-hero{display:flex}
.home-nav{display:flex;align-items:center;justify-content:space-between;gap:24px;
  padding:20px 32px;border-bottom:1px solid rgba(0,0,0,.2)}
.home-brand{display:flex;align-items:center;gap:11px;text-decoration:none;color:#000;
  font-family:var(--mono);font-size:9px;letter-spacing:.13em;text-transform:uppercase;white-space:nowrap}
.home-brand .mark{width:17px;height:17px;flex-basis:17px;background:#000;box-shadow:none}
.home-nav .sitenav a{color:rgba(0,0,0,.58)}
.home-nav .sitenav a:hover,.home-nav .sitenav a[data-nav="home"]{color:#000;border-bottom-color:#000}
.home-issue{font-family:var(--mono);font-size:9px;letter-spacing:.12em;
  color:rgba(0,0,0,.52);white-space:nowrap}
.home-center{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;padding:38px 40px 18px;position:relative;z-index:2}
@keyframes homeRise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:no-preference){
  .home-logo{animation:homeRise .7s cubic-bezier(.2,.7,.2,1) both}
  .home-mission{animation:homeRise .7s .08s cubic-bezier(.2,.7,.2,1) both}
  .home-signature{animation:homeRise .8s .14s cubic-bezier(.2,.7,.2,1) both}
  .home-copy{animation:homeRise .8s .22s cubic-bezier(.2,.7,.2,1) both}
  .home-actions{animation:homeRise .8s .3s cubic-bezier(.2,.7,.2,1) both}
}
.home-logo{width:80px;height:80px;color:#000;margin-bottom:28px}
.home-logo svg{width:100%;height:100%;display:block}
.home-mission{max-width:600px;margin:0 0 18px;font-size:13px;line-height:1.95;
  letter-spacing:.08em;text-transform:uppercase;color:rgba(0,0,0,.78);font-weight:600}
.home-signature{font-family:var(--script);font-size:clamp(96px,10.5vw,158px);line-height:.82;
  letter-spacing:-.02em;margin:0 0 22px;font-weight:400}
.home-signature span{display:block;font-family:var(--mono);font-size:9px;letter-spacing:.28em;
  margin-top:12px;color:rgba(0,0,0,.52);text-transform:uppercase}
.home-copy{max-width:570px;margin:0 0 24px;font-size:14.5px;line-height:1.95;
  font-weight:400;color:rgba(0,0,0,.82)}
.home-copy p{margin:0 0 12px}
.home-copy p:last-child{margin-bottom:0}
.home-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:center}
.home-cta{display:inline-flex;align-items:center;gap:10px;padding:10px 16px;background:#000;color:#fff;
  text-decoration:none;font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;
  border:1px solid #000;transition:background .16s,color .16s,border-color .16s}
.home-cta:hover{background:transparent;color:#000}
.home-cta.ghost{background:transparent;color:#000}
.home-cta.ghost:hover{background:#000;color:#fff}
.home-scroll{text-align:center;font-family:var(--mono);font-size:8.5px;letter-spacing:.16em;
  color:rgba(0,0,0,.52);padding:8px 0 5px;text-transform:uppercase}
.home-scroll span{display:inline-block;animation:scrolldown 1.6s ease-in-out infinite}
@keyframes scrolldown{50%{transform:translateY(4px)}}
.home-visual{position:relative;height:34vh;min-height:240px;flex:0 0 auto;overflow:hidden}
.home-visual canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
.home-visual-fade{position:absolute;top:0;left:0;right:0;height:110px;z-index:2;pointer-events:none;
  background:linear-gradient(to bottom,var(--hero),color-mix(in srgb,var(--hero) 0%,transparent))}
.home-visual-label{position:absolute;left:32px;bottom:16px;z-index:3;font-family:var(--mono);
  font-size:8.5px;letter-spacing:.12em;color:rgba(0,0,0,.5);text-transform:uppercase}
/* 入口索引：四张真正的页面卡片。 */
.home-index{border-bottom:1px solid var(--fg);background:var(--bg);padding:64px 32px 72px}
body.page-home .home-index{display:block}
.home-index-in{max-width:1184px;margin:0 auto}
.home-index-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:26px}
.home-index-head h2{margin:6px 0 0;font-size:clamp(30px,4vw,52px);line-height:1.02;letter-spacing:-.04em}
.home-index-head h2 span{color:var(--mut)}
.home-index-head p{max-width:350px;margin:0;font-size:12.5px;color:var(--mut);line-height:1.8}
.home-index-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;
  border:1px solid var(--fg);background:#000}
.idx-card{position:relative;display:flex;flex-direction:column;min-height:232px;padding:18px 18px 16px;
  background:#fff;text-decoration:none;color:var(--fg);border-right:1px solid var(--fg);
  transition:background .18s,color .18s}
.idx-card:last-child{border-right:0}
.idx-card:hover{background:#000;color:#fff}
.idx-no{font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--acc)}
.idx-card:hover .idx-no{color:var(--amber)}
.idx-card b{font-size:23px;line-height:1.15;letter-spacing:-.025em;margin:14px 0 2px}
.idx-en{font-family:var(--mono);font-size:8.5px;letter-spacing:.1em;color:var(--mut);text-transform:uppercase}
.idx-card:hover .idx-en{color:rgba(255,255,255,.55)}
.idx-card p{font-size:12px;line-height:1.75;color:var(--mut);margin:18px 0 0}
.idx-card:hover p{color:rgba(255,255,255,.72)}
.idx-arrow{position:absolute;right:16px;bottom:14px;font-family:var(--mono);font-size:16px;color:var(--acc)}
.idx-card:hover .idx-arrow{color:var(--amber)}
/* 三纪走廊：恐龙是时期的路标，不是装饰。滚动让它们沿地层线前进。 */
.strata{border-bottom:1px solid var(--fg);background:rgba(255,255,255,.38)}
.strata-head{max-width:1184px;margin:0 auto;padding:26px 28px 16px;
  display:flex;align-items:flex-end;justify-content:space-between;gap:24px}
.strata-head h2{margin:6px 0 0;font-size:clamp(24px,3.4vw,40px);line-height:1.08;
  letter-spacing:-.035em;font-weight:600}
.strata-head h2 span{color:var(--mut)}
.strata-hint{max-width:360px;margin:0;text-align:right;font-family:var(--mono);
  font-size:10px;line-height:1.8;color:var(--mut);letter-spacing:.04em}
.strata-rows{max-width:1184px;margin:0 auto;border-top:1px solid var(--fg)}
.stratum{--p:0;position:relative;display:grid;grid-template-columns:260px minmax(0,1fr);
  min-height:132px;border-bottom:1px solid var(--fg);background:rgba(255,255,255,.72);
  cursor:pointer;outline:none;transition:background .18s,box-shadow .18s}
.stratum:last-child{border-bottom:0}
.stratum:hover,.stratum:focus-visible{background:#fff}
.stratum:focus-visible{box-shadow:inset 0 0 0 2px var(--amber)}
.stratum.on{background:#fff;box-shadow:inset 4px 0 0 var(--amber)}
.stratum-meta{padding:17px 20px 14px;border-right:1px solid var(--line);
  position:relative;z-index:4;background:inherit}
.stratum-no{font-family:var(--mono);font-size:9px;letter-spacing:.15em;color:var(--acc)}
.stratum-name{margin:4px 0 1px;font-size:29px;line-height:1.05;font-weight:600;letter-spacing:-.035em}
.stratum-span{font-family:var(--mono);font-size:9.5px;letter-spacing:.08em;color:var(--mut)}
.stratum-q{margin:7px 0 0;font-size:11.5px;line-height:1.55;color:var(--mut);max-width:220px}
.stratum-count{display:inline-block;margin-top:7px;font-family:var(--mono);
  font-size:8.5px;letter-spacing:.06em;color:var(--steel)}
.stratum-track{position:relative;overflow:hidden;min-height:132px;
  background-image:linear-gradient(90deg,rgba(0,0,0,.055) 1px,transparent 1px);
  background-size:54px 100%}
.stratum-track::before{content:"";position:absolute;left:0;right:0;bottom:25px;
  border-top:1px dashed rgba(82,96,109,.55)}
.stratum-progress{position:absolute;left:0;bottom:24px;height:1px;width:0;
  background:var(--amber);z-index:2;transition:width .08s linear}
.dino{position:absolute;left:0;bottom:18px;width:200px;height:108px;z-index:3;
  pointer-events:none;will-change:transform}
.dino svg{width:100%;height:100%;display:block;overflow:visible}
.dino-fill{fill:#171717;transition:fill .18s}
.dino .plate{fill:var(--amber);transition:fill .18s}
.dino .eye{fill:#fff}
.stratum:hover .dino-fill,.stratum.on .dino-fill{fill:var(--acc)}
.stratum:hover .plate,.stratum.on .plate{fill:#000}
.dino .leg{transform-box:fill-box;transform-origin:top center;
  animation:stride .34s ease-in-out infinite alternate}
.dino .leg.b{animation-delay:-.17s;animation-duration:.4s}
.dino .tail{transform-box:fill-box;transform-origin:right center;
  animation:tailsway 1.25s ease-in-out infinite alternate}
.dino .body{transform-box:fill-box;transform-origin:center bottom;
  animation:bob .34s ease-in-out infinite alternate}
@keyframes stride{to{transform:rotate(15deg)}}
@keyframes tailsway{to{transform:rotate(4deg) translateY(-1px)}}
@keyframes bob{to{transform:translateY(-2px)}}
.stratum-enter{position:absolute;right:16px;bottom:10px;font-family:var(--mono);
  font-size:8.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--steel)}
.stratum.on .stratum-enter,.stratum:hover .stratum-enter{color:var(--acc)}
.period-dossier{max-width:1184px;margin:0 auto;background:#fff;
  border-top:1px solid var(--fg);padding:0 28px 28px;scroll-margin-top:18px}
.period-dossier[hidden]{display:none}
.dossier-head{display:flex;justify-content:space-between;gap:22px;align-items:flex-start;
  padding:22px 0 12px;border-bottom:1px solid var(--fg)}
.dossier-head h3{font-size:32px;line-height:1.08;margin:5px 0 4px;letter-spacing:-.035em}
.dossier-head h3 span{font-family:var(--mono);font-size:10px;letter-spacing:.08em;
  color:var(--mut);margin-left:9px;font-weight:400}
.dossier-q{margin:0;font-size:13px;color:#2b3136}
.dossier-close{flex:0 0 auto;border:1px solid var(--fg);background:#fff;color:var(--fg);
  font-family:var(--mono);font-size:9px;letter-spacing:.1em;padding:6px 10px;cursor:pointer;
  border-radius:0;transition:background .14s,color .14s}
.dossier-close:hover{background:#000;color:#fff}
.dossier-note{max-width:950px;margin:12px 0 0;font-size:12.5px;line-height:1.8;color:var(--mut)}
.branch-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;
  margin-top:18px;align-items:start}
.branch{border:1px solid var(--fg);background:#fff;min-width:0}
.branch-head{display:flex;align-items:baseline;gap:8px;padding:8px 11px;
  border-bottom:1px solid var(--fg);background:var(--bg)}
.branchno{font-family:var(--mono);font-size:8.5px;color:var(--acc);letter-spacing:.1em}
.branch-head b{font-size:12.5px;font-weight:600}
.branch-head span:last-child{margin-left:auto;font-family:var(--mono);font-size:8.5px;color:var(--mut)}
.lineage-card{padding:12px 12px 10px;border-bottom:1px solid var(--line)}
.lineage-card:last-child{border-bottom:0}
.lc-top{display:flex;align-items:center;gap:6px}
.lc-id{font-family:var(--mono);font-size:8.5px;color:var(--steel);letter-spacing:.06em}
.lc-tier{font-family:var(--mono);font-size:8px;padding:0 5px;border:1px solid var(--line);
  color:var(--mut);letter-spacing:.05em}
.lc-tier.core{background:var(--amber);border-color:var(--amber);color:#000}
.lineage-card h4{margin:5px 0 3px;font-size:14px;line-height:1.35;letter-spacing:-.01em}
.lc-meta{font-family:var(--mono);font-size:9px;color:var(--mut);letter-spacing:.03em}
.lc-q{margin:6px 0 0;font-size:12px;line-height:1.6;color:#2b3136}
.lc-more{margin-top:7px;border-top:1px solid var(--line);padding-top:5px}
.lc-more summary{font-size:9.5px;padding:1px 0}
.lc-thesis{font-size:12px;line-height:1.65;margin:5px 0}
.lc-blind{font-size:11.5px;color:var(--mut);line-height:1.6;margin:4px 0}
.lc-terms{display:flex;gap:4px;flex-wrap:wrap;margin-top:7px}
.termchip{border:1px solid var(--line);background:#fff;color:var(--fg);border-radius:0;
  padding:1px 6px;font-size:10px;font-family:var(--sans);cursor:pointer;
  transition:background .14s,color .14s,border-color .14s}
.termchip:hover{background:#000;color:#fff;border-color:#000;box-shadow:inset 0 -2px 0 var(--amber)}
.lc-open{margin-top:8px;border:0;border-bottom:1px dotted var(--acc);background:none;color:var(--acc);
  font-family:var(--mono);font-size:9px;letter-spacing:.06em;padding:0 0 1px;cursor:pointer}
.lc-open:hover{background:var(--amber);color:#000;border-bottom-color:transparent}
.filters{padding:14px 28px 15px;border-bottom:1px solid var(--fg);
  background:rgba(243,245,246,.94);backdrop-filter:blur(8px);z-index:5}
@media (min-width:900px){.filters{position:sticky;top:0}}
.fgroup{display:grid;grid-template-columns:80px minmax(0,1fr);gap:12px;align-items:start;
  margin-bottom:8px;padding-top:8px;border-top:1px solid rgba(0,0,0,.09)}
.fgroup:first-child{border-top:0;padding-top:0}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.flabel{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);padding-top:6px}
.chip{border:1px solid var(--line);background:#fff;color:var(--fg);border-radius:0;
  padding:4px 9px;font-size:12px;cursor:pointer;font-family:var(--sans);
  transition:background .14s,color .14s,border-color .14s,box-shadow .14s}
.chip:hover{border-color:#000;background:#000;color:#fff}
.chip.on{background:#000;border-color:#000;color:#fff;box-shadow:inset 0 -2px 0 var(--amber)}
.chip i{font-style:normal;opacity:.55;font-size:10px;margin-left:5px;font-family:var(--mono)}
.searchwrap{position:relative;margin-top:8px}
.searchwrap::before{content:"⌕";position:absolute;right:2px;bottom:7px;font-size:17px;line-height:1;color:var(--mut);pointer-events:none}
#q{width:100%;padding:10px 30px 9px 2px;border:0;border-bottom:1px solid var(--fg);border-radius:0;
  font-size:12px;background:transparent;font-family:var(--mono);letter-spacing:.035em;color:var(--fg)}
#q::placeholder{color:var(--steel)}
#q:focus{outline:none;border-bottom-color:var(--amber);box-shadow:0 1px 0 var(--amber)}
.views{display:flex;gap:0;margin-top:11px;border:1px solid var(--fg);width:max-content;max-width:100%}
.vbtn{border:0;border-right:1px solid var(--fg);border-radius:0;background:#fff;color:var(--fg);
  display:inline-block;text-decoration:none;line-height:1.35;padding:7px 18px;font-size:10px;cursor:pointer;font-family:var(--mono);
  letter-spacing:.12em;text-transform:uppercase;transition:background .14s,color .14s,box-shadow .14s}
.vbtn:last-child{border-right:0}
.vbtn:hover{background:#000;color:#fff}
.vbtn.on{background:#000;border-color:#000;color:#fff;box-shadow:inset 0 -3px 0 var(--amber)}
.legend{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:1px;background:#000;
  border:1px solid #000;max-width:1184px;margin:0 auto}
.legend div{background:#fff;padding:10px 11px;font-size:11px;color:var(--mut);min-width:0}
.legendno{font-family:var(--mono);font-size:9px;color:var(--steel);margin-right:8px}
.legend b{color:var(--fg);font-weight:600;font-size:12px;margin-right:5px}
.legendq{display:block;margin-top:3px;font-size:10.5px;line-height:1.55}
.sectionhead{display:flex;align-items:baseline;justify-content:space-between;gap:16px;
  max-width:1184px;margin:18px auto 0;padding:9px 0;
  border-bottom:1px solid var(--fg);font-family:var(--mono);
  font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--mut)}
.sectionhead b{font-weight:500;color:var(--fg)}
main{padding:18px 28px 70px;max-width:1000px;margin:0 auto}
.card{position:relative;background:#fff;border:1px solid var(--fg);border-radius:0;
  padding:20px 22px;margin-bottom:16px;transition:box-shadow .15s,border-color .15s}
.card:hover{box-shadow:6px 6px 0 rgba(0,0,0,.07)}
.card.hl{border-color:var(--amber);box-shadow:0 0 0 2px var(--amber)}
.card::before{content:attr(data-index);position:absolute;right:18px;top:15px;
  font-family:var(--mono);font-size:9px;color:var(--steel);letter-spacing:.08em}
.ttl{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;padding-right:38px}
.zh{font-size:20px;font-weight:600;letter-spacing:-.02em;line-height:1.35}
.en{color:var(--mut);font-size:10px;font-style:normal;font-family:var(--mono);
  letter-spacing:.08em;text-transform:uppercase}
.badge{font-size:9px;padding:1px 6px;border-radius:0;background:#fff;color:var(--mut);
  border:1px solid var(--line);font-family:var(--mono);letter-spacing:.08em;text-transform:uppercase}
.badge.cat{background:var(--amber);border-color:var(--amber);color:#000}
.meta{color:var(--mut);font-size:10px;margin:7px 0 11px;font-family:var(--mono);letter-spacing:.035em}
.def{margin:0 0 11px}
.def b{color:#000;font-weight:500;font-family:var(--mono);font-size:10px;letter-spacing:.08em;
  background:var(--amber);padding:0 5px;margin-right:7px}
.tags{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px}
.tag{font-size:10px;background:#fff;color:var(--mut);border:1px solid var(--line);border-radius:0;
  padding:1px 7px;font-family:var(--mono);letter-spacing:.03em}
details{border-top:1px solid var(--line);padding-top:7px;margin-top:10px}
summary{cursor:pointer;font-size:11px;color:var(--fg);outline:none;user-select:none;
  font-family:var(--mono);letter-spacing:.04em;list-style:none;padding:2px 0}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";color:var(--acc);margin-right:7px;font-size:13px;line-height:1}
details[open] summary::before{content:"−"}
summary:hover{color:var(--acc)}
details ul{margin:8px 0 2px;padding-left:19px}
details>ul{overflow:hidden}
details li{margin-bottom:8px;font-size:13.5px}
.poly li{padding-left:2px}
.who{font-weight:600}
.reltype{background:#f3f5f6;color:var(--mut);border:1px solid var(--line);border-radius:0;
  padding:0 5px;font-size:9px;margin:0 3px;font-family:var(--mono);letter-spacing:.05em}
.reltype.br{background:#fff8e8;color:#8a5200;border:1px dashed #d39a32}
a.t{color:var(--acc);cursor:pointer;text-decoration:none;border-bottom:1px dotted var(--acc)}
a.t:hover{background:var(--amber);color:#000;border-bottom-color:transparent}
.case{color:var(--mut);font-size:12.5px}
.relblock{margin-bottom:10px}
.relhead{font-size:13px}
.note{display:block;font-size:13px;color:#2b3136;margin-top:3px}
.bd{display:block;font-size:12.5px;color:var(--mut);margin-top:2px}
.src{display:block;font-size:11.5px;color:var(--mut);margin-top:4px;font-family:var(--mono)}
.src i{font-style:normal;color:var(--steel)}
.tagline{display:inline-block;font-size:9px;padding:0 5px;border-radius:0;
  background:#f3f5f6;color:var(--mut);border:1px solid var(--line);margin-right:5px;
  font-family:var(--mono);letter-spacing:.05em}
.tagline.me{background:#fff8e8;color:#8a5200;border-color:#e9c77d}
.ok{display:block;color:#2f5d46;font-size:12.5px;margin-top:2px}
.hotbox{border-left:2px solid var(--amber);padding-left:10px;margin-bottom:10px}
.mism{display:block;color:#8a4a3a;font-size:12.5px;margin-top:2px}
.empty{color:var(--mut);padding:46px 0;text-align:center;font-family:var(--mono);font-size:11px;letter-spacing:.08em}
footer{color:var(--mut);font-size:9px;padding:0 28px 40px;font-family:var(--mono);
  letter-spacing:.07em;max-width:1184px;margin:0 auto}
.dot{width:8px;height:8px;border-radius:0;display:inline-block;margin-right:6px;vertical-align:1px}
#graph{padding:18px 28px 34px;display:none;max-width:1184px;margin:0 auto;background:#fff;border:1px solid var(--fg)}
#lins{padding:18px 28px 34px;display:none;max-width:1184px;margin:0 auto;background:#fff;border:1px solid var(--fg);overflow-x:auto}
#lins>svg{width:100%;height:auto;display:block;min-width:980px}
@media (min-width:1100px){
  #lins{overflow-x:visible}
  .linplay{position:sticky;top:calc(var(--filterh,0px) + 8px);z-index:6}
}
.linhint{color:var(--mut);font-size:11px;margin-bottom:10px;font-family:var(--mono);line-height:1.75}
.linplay{display:grid;grid-template-columns:168px minmax(0,1fr);gap:16px;align-items:center;
  border:1px solid var(--fg);background:#fff;padding:12px 14px;margin:0 0 12px}
.playbtn{display:flex;align-items:center;justify-content:center;gap:9px;width:100%;height:38px;
  border:1px solid #000;border-radius:0;background:#000;color:#fff;cursor:pointer;
  font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;
  transition:background .15s,color .15s,border-color .15s,box-shadow .15s}
.playbtn:hover{background:#fff;color:#000;box-shadow:inset 0 -3px 0 var(--amber)}
.playbtn.playing{background:var(--amber);border-color:var(--amber);color:#000}
.playico{font-family:var(--mono);font-size:11px;color:var(--amber);line-height:1}
.playbtn.playing .playico{color:#000}
.playmid{min-width:0}
.playhead{display:flex;align-items:baseline;gap:10px;min-width:0}
.playyear{font-family:var(--mono);font-size:25px;font-weight:500;line-height:1;letter-spacing:-.025em}
.playnote{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  font-family:var(--mono);font-size:11px;letter-spacing:.02em;color:#000}
.playnote:not(:empty)::before{content:"●";color:var(--amber);font-size:7px;vertical-align:2px;margin-right:7px}
.playtrack{--p:0%;position:relative;padding-top:27px}
.playsaur{position:absolute;top:0;left:clamp(22px,var(--p),calc(100% - 22px));
  width:42px;height:23px;transform:translateX(-50%);pointer-events:none;color:#000;
  overflow:hidden;contain:layout paint}
#lins .playtrack .playsaur svg{width:42px;height:23px;min-width:0;max-width:42px;max-height:23px;
  display:block;overflow:hidden}
.playsaur .dino-fill{fill:#000}
.playsaur .eye{fill:var(--amber);stroke:none}
.playsaur .leg{transform-box:fill-box;transform-origin:50% 0}
.playsaur .tail{transform-box:fill-box;transform-origin:100% 50%}
.timeline.playing .playsaur .leg.a{animation:saurLegA .22s ease-in-out infinite alternate}
.timeline.playing .playsaur .leg.b{animation:saurLegB .22s ease-in-out infinite alternate}
.timeline.playing .playsaur .tail{animation:saurTail .34s ease-in-out infinite alternate}
@keyframes saurLegA{to{transform:translateY(-2px)}}
@keyframes saurLegB{to{transform:translateY(2px)}}
@keyframes saurTail{to{transform:rotate(3deg)}}
.linrange{--p:0%;-webkit-appearance:none;appearance:none;display:block;width:100%;height:20px;
  margin:0;background:transparent;cursor:pointer}
.linrange::-webkit-slider-runnable-track{height:2px;
  background:linear-gradient(90deg,var(--amber) 0 var(--p),var(--line) var(--p) 100%)}
.linrange::-webkit-slider-thumb{-webkit-appearance:none;width:13px;height:13px;margin-top:-5.5px;
  border:2px solid var(--amber);border-radius:0;background:#000}
.linrange::-moz-range-track{height:2px;background:var(--line)}
.linrange::-moz-range-progress{height:2px;background:var(--amber)}
.linrange::-moz-range-thumb{width:11px;height:11px;border:2px solid var(--amber);border-radius:0;background:#000}
.linrange:focus-visible{outline:1px solid var(--amber);outline-offset:4px}
.playticks{position:relative;height:12px;margin-top:-2px;
  font-family:var(--mono);font-size:8px;letter-spacing:.05em;color:var(--steel)}
.playticks span{position:absolute;top:0;transform:translateX(-50%)}
.playticks span:first-child{transform:none}
.playticks span:last-child{transform:translateX(-100%)}
.playstages{display:flex;margin-top:4px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.playstages span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  padding:4px 6px 5px;border-right:1px solid var(--line);font-family:var(--mono);
  font-size:9px;letter-spacing:.06em;color:var(--mut);transition:background .15s,color .15s}
.playstages span:last-child{border-right:0}
.playstages span.on{background:#fff8e8;color:#000}
.playstages b{font-weight:600;margin-right:5px}
.playstages small{font-size:8px;color:var(--steel);margin-left:2px}
.playstages span.on small{color:var(--acc)}
.stephead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:2px 0 8px}
.stephead b{font-size:12px;color:var(--fg);font-family:var(--mono);letter-spacing:.06em}
.stephead span{font-size:11px;color:var(--mut)}
.stageband{fill:#fbfcfc}
.stageband.alt{fill:#f3f5f6}
.stageguide{stroke:#d1d6dc;stroke-width:1;stroke-dasharray:2 5}
.stageaxis{stroke:#000;stroke-width:1.1}
.stagearrow{fill:#000}
.stagename{font-size:11px;font-weight:600;fill:#000;font-family:var(--mono);letter-spacing:.06em}
.stagespan{font-size:9px;fill:var(--mut);font-family:var(--mono)}
.stageno{font-size:8.5px;fill:var(--acc);font-weight:600;letter-spacing:.1em;font-family:var(--mono)}
.stagenode circle{fill:#fff;stroke:#000;stroke-width:1.1}
.branchrule{stroke:#d1d6dc;stroke-width:1}
.branchrule.core{stroke:#a1abb5;stroke-width:1.4}
.branchlabel{font-size:9px;fill:#7a848d;letter-spacing:.03em;font-family:var(--mono)}
.branchlabel.core{fill:#000;font-weight:600}
.yearline{stroke:#e9edef;stroke-width:.8}
.yearlabel{font-size:9px;fill:#7a848d;font-family:var(--mono)}
.yearaxis{font-size:9px;fill:#52606d;font-weight:600;font-family:var(--mono)}
.linaxis{cursor:pointer;outline:none}
.linaxis.dim{opacity:.18}
.thit{fill:transparent}
.tline{stroke:#a1abb5;stroke-width:1.6;stroke-linecap:round;transition:stroke .15s,stroke-width .15s}
.linaxis:hover .tline,.linaxis.on .tline{stroke:var(--amber);stroke-width:3}
.tstart{fill:#fff;stroke:#000;stroke-width:1.1;transition:fill .15s}
.linaxis:hover .tstart,.linaxis.on .tstart{fill:var(--amber);stroke:var(--amber)}
.tid{font-size:8px;font-weight:600;fill:#7a848d;opacity:.9;font-family:var(--mono)}
.linaxis:hover .tid,.linaxis.on .tid{fill:#000;opacity:1}
.tdot{fill:#000;opacity:.5;transition:opacity .15s}
.linaxis:hover .tdot,.linaxis.on .tdot{opacity:1;fill:var(--acc)}
.tdotrack{stroke:#a1abb5;stroke-width:1;opacity:.45}
.tcount{font-size:8px;fill:#7a848d;font-family:var(--mono)}
.timecursor{stroke:var(--amber);stroke-width:1.2;stroke-dasharray:4 4;opacity:0;pointer-events:none}
.timecursor-dot{fill:var(--amber);stroke:#000;stroke-width:1;opacity:0;pointer-events:none}
.timecursor-label{font-size:8.5px;font-family:var(--mono);fill:#000;opacity:0;pointer-events:none;
  paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}
.timeline .timecursor,.timeline .timecursor-dot,.timeline .timecursor-label{opacity:1}
.timeline .tdot{opacity:0}
.timeline .tdot.shown{opacity:.5}
.timeline .linaxis.on .tdot.shown{opacity:1}
.timeline .tdot.new{fill:var(--amber);opacity:1;r:4.2px}
.timeline .linaxis.future .tline{stroke:#d1d6dc;stroke-width:1.2}
.timeline .linaxis.future .tstart{fill:#fff;stroke:#a1abb5}
.timeline .linaxis.future .tid{opacity:.35}
.timeline .linaxis.live .tline{stroke:var(--amber);stroke-width:3.2}
.timeline .linaxis.live .tstart{fill:var(--amber);stroke:var(--amber)}
.timeline .linaxis.live .tid{fill:#000;opacity:1}
.timeline .linaxis.live .tdot.shown{opacity:1}
.timeline.playing .timecursor{animation:timelineDash 1s linear infinite}
@keyframes timelineDash{to{stroke-dashoffset:-16}}
@media (prefers-reduced-motion:reduce){
  .timeline.playing .timecursor{animation:none}
  .timeline .tdot{transition:none}
  .timeline.playing .playsaur .leg,.timeline.playing .playsaur .tail{animation:none}
}
.linhover{position:fixed;z-index:80;display:none;max-width:350px;padding:11px 13px;
  border:1px solid #000;border-radius:0;background:#fff;
  box-shadow:6px 6px 0 rgba(0,0,0,.14);pointer-events:none;font-size:12px;line-height:1.55}
.linhover b{display:block;color:#000;font-size:13px;margin-bottom:2px}
.linhover span{display:block;color:var(--mut);font-size:10px;font-family:var(--mono)}
.linhover p{margin:6px 0 2px;color:#2b3136}
.linhover small{color:var(--mut);font-size:10px;font-family:var(--mono)}
.lindet{margin-top:8px;padding:15px 17px;border:1px solid #000;border-radius:0;
  background:#fff;font-size:13px;line-height:1.75;box-shadow:5px 5px 0 rgba(0,0,0,.05)}
.lindhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.lindhead b{font-size:15px;color:var(--fg)}
.lindspan{font-size:10px;color:var(--mut);font-family:var(--mono)}
.lindq{color:var(--mut);margin:5px 0 6px}
.lindth{margin:0 0 4px}
.lindb{margin:0 0 4px;color:#4b555e;font-size:12.5px}
.lindper{font-size:11px;color:var(--mut);margin-top:5px;font-family:var(--mono)}
.lindterms{list-style:none;padding:0;margin:10px 0 0;border-top:1px solid var(--line)}
.lindterms li{padding:7px 0;border-bottom:1px solid var(--line);font-size:12.5px}
.lindterms li:last-child{border-bottom:0}
.lindterms .note{margin-top:2px}
.linwrap .places{list-style:none;padding-left:0;margin:8px 0 0}
.linwrap .pl{padding:8px 0;border-top:1px solid var(--line)}
.linwrap .plh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.linwrap .plper,.linwrap .plbranch{font-size:9px;color:var(--mut);background:#f3f5f6;
  border:1px solid var(--line);border-radius:0;padding:0 6px;font-family:var(--mono);letter-spacing:.03em}
.linwrap .plbranch{color:#8a5200;background:#fff8e8;border-color:#e9c77d}
.linwrap .plh b{font-size:13px;color:var(--fg)}
.linwrap .plspan{font-size:10px;color:var(--mut);font-family:var(--mono)}
.linwrap .plq{color:var(--mut);font-size:12px;margin:4px 0 1px}
.linwrap .plp{font-size:12.5px;margin:0;color:#2b3136}
#graph svg{width:100%;height:auto;display:block}
@media (max-width:820px){
  #graph{overflow-x:auto;-webkit-overflow-scrolling:touch;padding:10px 14px 30px}
  #graph svg{width:760px;height:auto}
  #lins{overflow-x:auto;-webkit-overflow-scrolling:touch;padding:10px 14px 30px}
  #lins>svg{width:900px;height:auto}
}
@media (max-width:900px){
  header{padding:0 16px}
  .topline{flex-wrap:wrap}
  .sitenav{order:3;width:100%;justify-content:flex-start;padding-top:8px}
  .home-nav{padding:16px;flex-wrap:wrap}
  .home-issue{display:none}
  .home-center{padding:30px 20px 14px}
  .home-mission{max-width:92%}
  .home-visual{height:30vh;min-height:200px}
  .home-index{padding:42px 16px 50px}
  .home-index-head{display:block}
  .home-index-head p{margin-top:12px;max-width:none}
  .home-index-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .idx-card:nth-child(2){border-right:0}
  .idx-card:nth-child(-n+2){border-bottom:1px solid var(--fg)}
  .subhead-in{grid-template-columns:1fr;gap:18px;padding:30px 16px 22px}
  .linplay{grid-template-columns:1fr;gap:10px}
  .playnote{margin-left:0}
  .hero{padding:30px 0 20px}
  h1{font-size:clamp(36px,9.5vw,54px)}
  .strata-head{padding:22px 16px 14px;display:block}
  .strata-hint{text-align:left;margin-top:10px;max-width:none}
  .stratum{grid-template-columns:220px minmax(0,1fr);min-height:116px}
  .stratum-meta{padding:14px 14px 12px}
  .stratum-name{font-size:24px}
  .stratum-q{font-size:10.5px;max-width:160px}
  .stratum-track{min-height:116px}
  .dino{width:160px;height:86px;bottom:15px}
  .period-dossier{padding:0 16px 22px}
  .branch-grid{grid-template-columns:1fr}
  .stats{grid-template-columns:repeat(3,minmax(0,1fr))}
  .stat:nth-child(3n){border-right:0}
  .stat:nth-child(-n+3){border-bottom:1px solid var(--line)}
  .filters{padding:12px 16px 14px}
  .fgroup{grid-template-columns:1fr;gap:4px;padding-top:9px}
  .flabel{padding-top:0}
  .legend{grid-template-columns:1fr 1fr;margin:0 16px}
  .sectionhead{margin:16px 16px 0;padding:9px 0}
  main{padding:16px 16px 50px}
  .card{padding:16px 16px 18px}
  .ttl{padding-right:30px}
  footer{padding:0 16px 32px}
}
@media (max-width:600px){
  .topmeta{display:none}
  .brand-en{display:none}
  .home-signature{font-size:90px}
  .home-copy{font-size:13px}
  .home-index-grid{grid-template-columns:1fr}
  .idx-card{border-right:0;border-bottom:1px solid var(--fg);min-height:190px}
  .idx-card:last-child{border-bottom:0}
  .stratum{grid-template-columns:1fr;min-height:0}
  .stratum-meta{border-right:0;border-bottom:1px solid var(--line);padding:12px 14px 13px}
  .stratum-q{max-width:none}
  .stratum-track{min-height:104px}
  .dino{width:150px;height:80px;bottom:12px}
  .dossier-head h3{font-size:26px}
  .stats{grid-template-columns:repeat(2,minmax(0,1fr))}
  .stat:nth-child(2n){border-right:0}
  .stat:nth-child(-n+4){border-bottom:1px solid var(--line)}
  .legend{grid-template-columns:1fr}
  .views{width:100%}
  .vbtn{flex:1;padding:7px 8px}
}
@keyframes rise{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
.hero,.stats{animation:rise .45s cubic-bezier(.2,.7,.2,1) both}
.stats{animation-delay:.06s}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important;scroll-behavior:auto!important}
}
/* 群内连线用该群的颜色、压暗；跨群桥接用琥珀色虚线并压在最上层 */
.e{stroke-width:1.25;opacity:.38}
.e.br{stroke:#b26a00;stroke-width:2;stroke-dasharray:6 4;opacity:1;animation:dashflow 1.8s linear infinite}
@keyframes dashflow{to{stroke-dashoffset:-20}}
.lead{stroke-width:1;opacity:.35}
.gnode{cursor:pointer}
.e,.gnode{transition:opacity .18s ease}
#graph.focusing .e:not(.on),#graph.focusing .gnode:not(.on){opacity:.09}
#graph.focusing .gnode.on circle{stroke:#000;stroke-width:1.8}
.gnode circle{stroke:#fff;stroke-width:1.6}
.gnode:hover circle{stroke:#000;stroke-width:2.2}
.gnode:hover text{font-weight:600}
.gnode text{font-size:10.5px;fill:#2b3136;font-family:var(--sans);
  paint-order:stroke;stroke:#fff;stroke-width:3.2px;stroke-linejoin:round}

</style>
</head>
<body class="__BODY_CLASS__">
<header class="home-hero">
  <div class="home-nav">
    <a class="home-brand" href="index.html"><span class="mark"></span><span>SOCIOLOGICAL TERM ATLAS</span></a>
    <nav class="sitenav">
      <a href="index.html" data-nav="home">首页</a>
      <a href="terms.html" data-nav="terms">术语索引</a>
      <a href="network.html" data-nav="network">概念网络</a>
      <a href="lineages.html" data-nav="lineages">学科谱系</a>
      <a href="index.html#strata" data-nav="strata">三纪走廊</a>
    </nav>
    <div class="home-issue">VOL. 01 / 2026</div>
  </div>
  <div class="home-center">
    <div class="home-logo" aria-hidden="true">
      <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path fill-rule="evenodd" clip-rule="evenodd" d="M60 120C26.8629 120 0 93.1371 0 60V0C22.5654 0 42.2213 12.4569 52.4662 30.8691C38.4788 34.2089 28.0787 46.7902 28.0787 61.8006V63.1443C28.0787 79.9648 41.7146 93.6006 58.5353 93.6006H59.8789L59.8785 61.8006C59.8785 79.3633 74.1159 93.6006 91.6787 93.6006L91.6787 61.8006C91.6787 44.2783 77.5071 30.0661 60 30.0008L60 0H62.5352C94.2722 0 120 25.7279 120 57.4648V60C120 93.1371 93.1371 120 60 120Z" fill="currentColor"/>
      </svg>
    </div>
    <p class="home-mission">我们把散落在文献、谱系与经验案例中的社会学概念，整理成一套可检索、可追溯、可扩展的知识系统。</p>
    <h1 class="home-signature">S.T.A.<span>SOCIOLOGICAL TERM ATLAS</span></h1>
    <div class="home-copy">
      <p>术语从不孤立存在。一个概念的意义，取决于它与哪些概念相连、落在哪一条传统里，又如何被经验案例检验。</p>
      <p>所以这里不是一部封闭的词典，而是一张可以进入的地图：从词条出发，沿关系、案例、热点与学科谱系，回到它正在解释的社会问题。</p>
    </div>
    <div class="home-actions">
      <a class="home-cta" href="terms.html">进入术语索引 <span>→</span></a>
      <a class="home-cta ghost" href="lineages.html">查看学科谱系</a>
    </div>
  </div>
  <div class="home-scroll">SCROLL / 三纪走廊 <span>↓</span></div>
  <div class="home-visual">
    <canvas id="homeCanvas"></canvas>
    <div class="home-visual-fade"></div>
    <div class="home-visual-label">CONCEPT FIELD / <span data-count="terms">67</span> TERMS · <span data-count="relations">100</span> RELATIONS</div>
  </div>
</header>
<header class="app-header">
  <div class="topline">
    <a class="brand" href="index.html">
      <span class="mark"></span>
      <span class="brand-cn">社会学术语知识系统</span>
      <span class="brand-en">/ SOCIOLOGICAL TERM ATLAS</span>
    </a>
    <nav class="sitenav">
      <a href="index.html" data-nav="home">首页</a>
      <a href="terms.html" data-nav="terms">术语索引</a>
      <a href="network.html" data-nav="network">概念网络</a>
      <a href="lineages.html" data-nav="lineages">学科谱系</a>
      <a href="index.html#strata" data-nav="strata">三纪走廊</a>
    </nav>
    <div class="topmeta" id="topmeta"></div>
  </div>
  <div class="hero">
    <div class="kicker">__APP_KICKER__</div>
    <h1>__APP_H1A__<br><span>__APP_H1B__</span></h1>
    <p class="sub" id="sub"></p>
  </div>
  <div class="stats" id="stats"></div>
</header>
<section class="subhead" aria-labelledby="subheadTitle">
  <div class="subhead-in">
    <div>
      <div class="kicker">__APP_KICKER__</div>
      <h1 id="subheadTitle">__APP_H1A__<span>__APP_H1B__</span></h1>
    </div>
    <div>
      <p class="subhead-desc">__SUB_DESC__</p>
      <div class="subhead-metrics">__SUB_METRICS__</div>
    </div>
  </div>
</section>
<section class="home-index" id="index">
  <div class="home-index-in">
    <div class="home-index-head">
      <div>
        <div class="kicker">INDEX / 四个入口</div>
        <h2>从任意一条路径<br><span>进入同一张地图</span></h2>
      </div>
      <p>词条、关系、谱系与时期不是四个孤岛，而是同一套知识结构的四种进入方式。</p>
    </div>
    <div class="home-index-grid">
      <a class="idx-card" href="terms.html">
        <span class="idx-no">01 / TERMS</span><b>术语索引</b><span class="idx-en">TERM RECORDS</span>
        <p><span data-count="terms">67</span> 条术语，按首现年份排列；概念群、流派与应用场景三组筛选可叠加。</p>
        <span class="idx-arrow">→</span>
      </a>
      <a class="idx-card" href="network.html">
        <span class="idx-no">02 / RELATIONS</span><b>概念网络</b><span class="idx-en">RELATION NETWORK</span>
        <p><span data-count="relations">100</span> 条概念关系；群内连线按概念群着色，跨群桥接用琥珀色虚线。</p>
        <span class="idx-arrow">→</span>
      </a>
      <a class="idx-card" href="lineages.html">
        <span class="idx-no">03 / LINEAGES</span><b>学科谱系</b><span class="idx-en">DISCIPLINARY LINEAGES</span>
        <p><span data-count="periods">3</span> 个阶段、<span data-count="lineages">21</span> 条传统；把术语放回它正在解释的社会学问题。</p>
        <span class="idx-arrow">→</span>
      </a>
      <a class="idx-card" href="index.html#strata">
        <span class="idx-no">04 / STRATA</span><b>三纪走廊</b><span class="idx-en">THREE PERIODS</span>
        <p>古典、现代、当代各有一只恐龙；点击进入该时期的分支与传统。</p>
        <span class="idx-arrow">→</span>
      </a>
    </div>
  </div>
</section>
<section class="strata" id="strata" aria-labelledby="strataTitle">
  <div class="strata-head">
    <div>
      <div class="kicker">STRATA / 三纪走廊 / SCROLL TO EXCAVATE</div>
      <h2 id="strataTitle">滚动，让三个时期<br><span>从地层里走出来</span></h2>
    </div>
    <p class="strata-hint">向下滚动，三只恐龙沿各自的地层线前进。<br>点击一只 → 展开该时期的全部分支与传统。</p>
  </div>
  <div class="strata-rows" id="strataRows"></div>
  <div class="period-dossier" id="periodDossier" hidden></div>
</section>
<div class="filters">
  <div class="fgroup"><span class="flabel">概念群</span><div class="chips" id="fCluster"></div></div>
  <div class="fgroup"><span class="flabel">流派</span><div class="chips" id="fSchool"></div></div>
  <div class="fgroup"><span class="flabel">应用场景</span><div class="chips" id="fApp"></div></div>
  <input id="q" placeholder="搜索术语、英文名、别名、定义、提出者…">
  <div class="views">
    <a class="vbtn on" id="vList" href="terms.html">列表</a>
    <a class="vbtn" id="vGraph" href="network.html">网络</a>
    <a class="vbtn" id="vLineages" href="lineages.html">学科谱系</a>
  </div>
</div>
<div class="legend" id="legend"></div>
<div class="sectionhead" id="sectionhead"></div>
<main id="list"></main>
<div id="graph"></div>
<div id="lins"></div>
<footer id="foot"></footer>
<script>
const DATA = __DATA__;
const PAGE = '__PAGE__';
const PAGE_VIEW = '__PAGE_VIEW__';
const S = {cluster:new Set(), school:new Set(), app:new Set(), q:'', view:PAGE_VIEW,
           anchor:null, lineage:null, period:null};
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

// 学科谱系（宏观）：这个词在学科史里属于哪几条传统、在每条传统里解释什么问题。
function lineageBlock(t){
  const placed = t.placed || [];
  if (!placed.length) return '';
  const body = placed.map(x => {
    const per = (x.periods || []).map(p => `${esc(p.name)} · ${esc(p.span)}`).join(' / ');
    return `<li class="pl">
      <div class="plh"><span class="plper">${per}</span>` +
      `<span class="plbranch">${esc(x.branch || '未分组')}</span><b>${esc(x.name)}</b>` +
      `<span class="plspan">${x.from}${x.ongoing ? '–' : '–' + x.to}</span></div>
      <p class="plq">这一脉问的是：${esc(x.question)}</p>
      <p class="plp">在本谱系中解释：${esc(x.problem)}</p></li>`;
  }).join('');
  return `<details class="linwrap"><summary>学科谱系（${placed.length}）</summary>` +
    `<ul class="places">${body}</ul></details>`;
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
  return `<div class="card" id="t-${t.term_id}" data-index="T${String(t.term_id).split('-')[1] || ''}">
    <div class="ttl"><span class="zh">${esc(t.name_zh)}</span>
      <span class="en">${esc(t.name_en)}</span>
      ${t.entry_type==='分析范畴'?'<span class="badge cat">分析范畴</span>':''}
      <span class="badge">${esc(t.status)}</span></div>
    <div class="meta">${esc(t.proponent)} · ${t.first_year} · ${esc(t.first_source)}</div>
    <p class="def"><b>定义</b>　${esc(t.definition)}</p>
    <div class="tags">${t.school.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}
      ${t.application.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div>
    ${(t.polysemy||[]).length ? `<details><summary>多义性（${t.polysemy.length}）</summary><ul class="poly">${poly}</ul></details>` : ''}
    ${(t.placed||[]).length ? lineageBlock(t) : ''}
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
  `学科谱系视图把术语放回 ${DATA.meta.periods} 个阶段、${DATA.meta.lineages} 条传统`;

document.getElementById('stats').innerHTML = [
  ['术语', DATA.meta.terms], ['概念关系', DATA.meta.relations],
  ['经典案例', DATA.meta.cases], ['社会热点', DATA.meta.hotspots],
  ['多义性条目', DATA.meta.polysemy],
  ['学科谱系', DATA.meta.lineages]
].map(([k,v], i) => `<div class="stat"><span class="statno">${String(i+1).padStart(2,'0')}</span>` +
  `<b>${v}</b><span class="statlabel">${k}</span></div>`).join('');

document.getElementById('topmeta').innerHTML =
  `${DATA.meta.terms} TERMS / ${DATA.meta.lineages} TRADITIONS<span class="plus">+</span>`;

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
  document.getElementById('legend').innerHTML = DATA.clusterOrder.map((c, i) =>
    `<div><span class="legendno">${String(i+1).padStart(2,'0')}</span>` +
    `<span class="dot" style="background:${DATA.clusterColors[c]}"></span>` +
    `<b>${esc(c)}</b><span class="legendq">${esc(DATA.clusters[c]||'')}</span></div>`).join('');
}

function gotoCard(id){
  if (PAGE !== 'terms'){ location.href = `terms.html?term=${encodeURIComponent(id)}`; return; }
  const target = DATA.terms.find(t => t.term_id === id);
  // 谱系详情会列出该传统下的全部术语，即使当前筛选没有留下它们；
  // 点进来时若目标被筛掉，先清空筛选，否则会跳到一个不存在的卡片。
  if (target && !matched(target)){
    S.cluster.clear(); S.school.clear(); S.app.clear(); S.q = '';
    document.querySelectorAll('.chip.on').forEach(b => b.classList.remove('on'));
    document.getElementById('q').value = '';
  }
  S.view = 'list';
  setViewBtns('list');
  draw();
  const el = document.getElementById('t-' + id);
  if (el){ el.scrollIntoView({behavior:'smooth', block:'center'});
           el.classList.add('hl'); setTimeout(()=>el.classList.remove('hl'), 1800); }
}

// 三纪走廊：三个时期的恐龙。点击时期后，下面的档案板按 stage 聚合 branch / lineage。
const DINO_SVG = [
  `<svg viewBox="0 0 260 140" aria-hidden="true">
    <g class="tail dino-fill"><path d="M68 78 C46 76 24 62 4 42 C22 66 46 84 72 90 Z"/></g>
    <g class="body dino-fill">
      <ellipse cx="112" cy="80" rx="52" ry="24"/>
      <path d="M148 70 C158 52 173 33 191 21 L203 31 C187 42 175 56 167 73 Z"/>
      <ellipse cx="206" cy="18" rx="15" ry="9"/>
    </g>
    <g class="legs">
      <rect class="leg a dino-fill" x="72" y="95" width="12" height="29" rx="4"/>
      <rect class="leg b dino-fill" x="94" y="95" width="12" height="29" rx="4"/>
      <rect class="leg b dino-fill" x="140" y="95" width="12" height="29" rx="4"/>
      <rect class="leg a dino-fill" x="162" y="95" width="12" height="29" rx="4"/>
    </g>
    <circle class="eye" cx="210" cy="15" r="2.4"/>
  </svg>`,
  `<svg viewBox="0 0 260 140" aria-hidden="true">
    <g class="tail dino-fill"><path d="M74 78 C52 80 28 72 6 56 C22 80 48 96 78 94 Z"/></g>
    <g class="plates">
      <path class="plate" d="M84 57 L96 30 L110 58 Z"/>
      <path class="plate" d="M108 55 L121 25 L136 56 Z"/>
      <path class="plate" d="M134 55 L147 24 L162 56 Z"/>
      <path class="plate" d="M160 57 L172 31 L184 59 Z"/>
      <path class="plate" d="M184 61 L194 40 L202 64 Z"/>
      <path class="plate" d="M12 52 L3 38 L7 58 Z"/>
      <path class="plate" d="M24 63 L12 52 L21 70 Z"/>
    </g>
    <g class="body dino-fill">
      <ellipse cx="132" cy="83" rx="62" ry="27"/>
      <path d="M182 78 C192 70 206 68 220 72 C230 75 234 82 230 88 C226 94 216 94 208 90 L188 88 Z"/>
      <ellipse cx="223" cy="81" rx="13" ry="9"/>
    </g>
    <g class="legs">
      <rect class="leg a dino-fill" x="86" y="103" width="13" height="21" rx="4"/>
      <rect class="leg b dino-fill" x="108" y="103" width="13" height="21" rx="4"/>
      <rect class="leg b dino-fill" x="156" y="103" width="13" height="21" rx="4"/>
      <rect class="leg a dino-fill" x="178" y="103" width="13" height="21" rx="4"/>
    </g>
    <circle class="eye" cx="226" cy="77" r="2.2"/>
  </svg>`,
  `<svg viewBox="0 0 260 140" aria-hidden="true">
    <g class="tail dino-fill"><path d="M80 74 C58 80 32 68 6 46 C24 74 52 94 80 94 Z"/></g>
    <g class="body dino-fill">
      <ellipse cx="118" cy="82" rx="45" ry="29"/>
      <path d="M146 66 C154 52 170 44 188 44 L208 46 C218 48 222 55 218 62 C214 69 204 70 196 68 L184 66 L180 82 L164 82 L160 68 Z"/>
    </g>
    <g class="legs">
      <path class="leg a dino-fill" d="M102 98 L120 98 L116 122 L104 122 Z"/>
      <path class="leg b dino-fill" d="M140 98 L158 98 L154 122 L142 122 Z"/>
    </g>
    <path class="arm dino-fill" d="M164 78 L180 86 L176 92 L160 84 Z"/>
    <circle class="eye" cx="204" cy="52" r="2.2"/>
  </svg>`
];

const BRANCH_ORDER = {
  P1: ['古典三大家', '历史主义'],
  P2: ['整合与中层', '微观互动', '冲突与批判', '其他现代分支'],
  P3: ['综合路径', '后结构/后现代', '全球/后殖民', '晚近', '批判与差异']
};

function renderStrata(){
  const host = document.getElementById('strataRows');
  const en = ['CLASSICAL', 'MODERN', 'CONTEMPORARY'];
  host.innerHTML = DATA.periods.map((p, i) => {
    const ls = DATA.lineages.filter(l => l.stage === p.id);
    const branches = new Set(ls.map(l => l.branch).filter(Boolean));
    return `<div class="stratum" data-period="${p.id}" role="button" tabindex="0"` +
      ` aria-expanded="false" aria-controls="periodDossier">` +
      `<div class="stratum-meta">` +
        `<div class="stratum-no">P${i+1} / ${en[i] || ''}</div>` +
        `<div class="stratum-name">${esc(p.name)}</div>` +
        `<div class="stratum-span">${esc(p.span)}</div>` +
        `<p class="stratum-q">${esc(p.question)}</p>` +
        `<div class="stratum-count">${branches.size} 分支 · ${ls.length} 传统</div>` +
      `</div>` +
      `<div class="stratum-track"><div class="stratum-progress"></div>` +
        `<div class="dino">${DINO_SVG[i] || DINO_SVG[0]}</div>` +
        `<span class="stratum-enter">进入时期 →</span></div></div>`;
  }).join('');
  host.querySelectorAll('.stratum').forEach(row => {
    const toggle = () => selectPeriod(row.dataset.period);
    row.addEventListener('click', toggle);
    row.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); toggle(); }
    });
  });
}

function selectPeriod(id){
  const same = S.period === id;
  S.period = same ? null : id;
  const dossier = document.getElementById('periodDossier');
  document.querySelectorAll('.stratum').forEach(r => {
    const on = r.dataset.period === S.period;
    r.classList.toggle('on', on);
    r.setAttribute('aria-expanded', on ? 'true' : 'false');
  });
  if (!S.period){ dossier.hidden = true; dossier.innerHTML = ''; return; }
  const p = DATA.periods.find(x => x.id === S.period);
  if (!p) return;
  dossier.innerHTML = periodDossierHTML(p);
  dossier.hidden = false;
  wireDossier();
  if (!RM) requestAnimationFrame(() => dossier.scrollIntoView({behavior:'smooth', block:'nearest'}));
}

function periodDossierHTML(p){
  const ls = DATA.lineages.filter(l => l.stage === p.id)
    .sort((a,b) => a.from - b.from || a.name.localeCompare(b.name, 'zh'));
  const groups = [];
  ls.forEach(l => {
    const key = l.branch || '未分组';
    let g = groups.find(x => x.name === key);
    if (!g){ g = {name:key, items:[]}; groups.push(g); }
    g.items.push(l);
  });
  const order = BRANCH_ORDER[p.id] || [];
  groups.sort((a, b) => {
    const ia = order.indexOf(a.name), ib = order.indexOf(b.name);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  const branches = groups.map((g, gi) => `<section class="branch">` +
    `<div class="branch-head"><span class="branchno">B${String(gi+1).padStart(2,'0')}</span>` +
    `<b>${esc(g.name)}</b><span>${g.items.length} 条传统</span></div>` +
    g.items.map(lineageCardHTML).join('') + `</section>`).join('');
  return `<div class="dossier-head"><div><div class="kicker">PERIOD DOSSIER / ${p.id}</div>` +
    `<h3>${esc(p.name)}<span>${esc(p.span)}</span></h3>` +
    `<p class="dossier-q">${esc(p.question)}</p></div>` +
    `<button class="dossier-close" type="button" aria-label="收起时期档案">收起 ×</button></div>` +
    `<p class="dossier-note">${esc(p.note || '')}</p>` +
    `<div class="branch-grid">${branches}</div>`;
}

function lineageCardHTML(l){
  const ts = DATA.placements.filter(x => x.lineage_id === l.id).map(x => {
    const t = DATA.terms.find(y => y.term_id === x.term_id);
    return t ? {...x, name:t.name_zh} : null;
  }).filter(Boolean);
  return `<article class="lineage-card">` +
    `<div class="lc-top"><span class="lc-id">${l.id}</span>` +
    `<span class="lc-tier ${l.tier === 'core' ? 'core' : ''}">${l.tier === 'core' ? '主脉' : '扩展传统'}</span></div>` +
    `<h4>${esc(l.name)}</h4>` +
    `<div class="lc-meta">${l.from}${l.ongoing ? '–至今' : '–' + l.to}` +
    `${(l.figures || []).length ? ' · ' + esc(l.figures.join('、')) : ''}</div>` +
    `<p class="lc-q">${esc(l.question)}</p>` +
    `<details class="lc-more"><summary>主张、盲点与术语（${ts.length}）</summary>` +
      `<p class="lc-thesis">${esc(l.thesis)}</p>` +
      `<p class="lc-blind"><span class="tagline">看不见</span>${esc(l.blind)}</p>` +
      `<div class="lc-terms">${ts.map(x => `<button class="termchip" type="button"` +
        ` data-term="${x.term_id}" title="${esc(x.problem)}">${esc(x.name)}</button>`).join('') ||
        '<span class="case">暂无归属术语</span>'}</div>` +
    `</details>` +
    `<button class="lc-open" type="button" data-open="${l.id}">在谱系图中查看 →</button>` +
  `</article>`;
}

function wireDossier(){
  const d = document.getElementById('periodDossier');
  d.querySelectorAll('.termchip').forEach(b => b.onclick = () => openTerm(b.dataset.term));
  d.querySelectorAll('.lc-open').forEach(b => b.onclick = () => openLineageAction(b.dataset.open));
  const close = d.querySelector('.dossier-close');
  if (close) close.onclick = () => selectPeriod(S.period);
}

function openTerm(id){
  location.href = `terms.html?term=${encodeURIComponent(id)}`;
}

function openLineageAction(id){
  if (PAGE === 'lineages'){ openLineageView(id); return; }
  location.href = `lineages.html?lineage=${encodeURIComponent(id)}`;
}

function openLineageView(id){
  S.view = 'lineages'; S.lineage = id;
  setViewBtns('lineages'); draw();
  const lins = document.getElementById('lins');
  const fh = document.querySelector('.filters').offsetHeight || 0;
  const y = window.scrollY + lins.getBoundingClientRect().top - fh - 10;
  window.scrollTo({top:Math.max(0, y), behavior:RM ? 'auto' : 'smooth'});
}

let strataTick = false;
function updateStrata(){
  strataTick = false;
  const sec = document.getElementById('strata');
  if (!sec) return;
  const r = sec.getBoundingClientRect();
  const vh = window.innerHeight || 800;
  const span = Math.max(1, r.height + vh * .55);
  const p = Math.max(0, Math.min(1, (vh * .82 - r.top) / span));
  const speed = [.88, 1, 1.12];
  sec.querySelectorAll('.stratum').forEach((row, i) => {
    const dino = row.querySelector('.dino');
    const track = row.querySelector('.stratum-track');
    const bar = row.querySelector('.stratum-progress');
    const pi = RM ? .55 : Math.max(0, Math.min(1, p * (speed[i] || 1)));
    const max = Math.max(0, track.clientWidth - dino.offsetWidth - 26);
    dino.style.transform = `translateX(${(pi * max).toFixed(1)}px)`;
    bar.style.width = `${(pi * 100).toFixed(1)}%`;
  });
}
function scheduleStrata(){
  if (strataTick) return;
  strataTick = true;
  requestAnimationFrame(updateStrata);
}
addEventListener('scroll', scheduleStrata, {passive:true});
addEventListener('resize', scheduleStrata);

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

function showLineage(id){
  const host = document.getElementById('lins');
  const l = DATA.lineages.find(x => x.id === id);
  if (!l) return;
  S.lineage = id;
  host.querySelectorAll('.linaxis').forEach(g => g.classList.toggle('on', g.dataset.l === id));
  const per = (l.periods || []).map(pid => DATA.periods.find(p => p.id === pid)).filter(Boolean);
  const rows = DATA.placements.filter(p => p.lineage_id === id).map(p => {
    const t = DATA.terms.find(x => x.term_id === p.term_id);
    if (!t) return '';
    return `<li><a class="t" data-j="${t.term_id}">${esc(t.name_zh)}</a>` +
      `<span class="note"><span class="tagline me">在本谱系中解释</span>${esc(p.problem)}</span></li>`;
  }).join('');
  document.getElementById('linDet').innerHTML =
    `<div class="lindhead"><b>${esc(l.name)}</b>` +
    `<span class="lindspan">${l.from}${l.ongoing ? '–至今' : '–' + l.to}` +
    `　·　${DATA.placements.filter(p => p.lineage_id === id).length} 个术语</span></div>` +
    `<p class="lindq">这一脉问的是：${esc(l.question)}</p>` +
    `<p class="lindth">${esc(l.thesis)}</p>` +
    `<p class="lindb"><span class="tagline">看不见</span>${esc(l.blind)}</p>` +
    `<div class="lindper">分支：${esc(l.branch || '未分组')}　·　${l.tier === 'core' ? '主脉' : '扩展传统'}` +
    `${(l.figures || []).length ? `　·　代表：${esc(l.figures.join('、'))}` : ''}</div>` +
    `<div class="lindper">横跨：${per.map(p => `${esc(p.name)}（${esc(p.span)}）`).join('　→　')}</div>` +
    `<ul class="lindterms">${rows || '<li class="case">这一脉暂时没有归属术语</li>'}</ul>`;
  host.querySelectorAll('#linDet a.t').forEach(a => a.onclick = () => gotoCard(a.dataset.j));
}

let LIN_PLAY_RAF = 0;
function renderLineages(){
  if (LIN_PLAY_RAF){ cancelAnimationFrame(LIN_PLAY_RAF); LIN_PLAY_RAF = 0; }
  const host = document.getElementById('lins');
  if (!DATA.lineages.length){ host.innerHTML = '<div class="empty">还没有登记学科谱系</div>'; return; }
  const active = new Set(DATA.terms.filter(matched).map(t => t.term_id));
  const filtering = active.size < DATA.terms.length;
  const cnt = {};
  DATA.placements.forEach(p => {
    if (active.has(p.term_id)) cnt[p.lineage_id] = (cnt[p.lineage_id] || 0) + 1;
  });
  const sorted = [...DATA.lineages].sort((a,b) => a.from - b.from || a.name.localeCompare(b.name, 'zh'));
  const termById = Object.fromEntries(DATA.terms.map(t => [t.term_id, t]));
  const termsOf = id => DATA.placements.filter(p => p.lineage_id === id).map(p => {
    const t = termById[p.term_id];
    return t ? {id: t.term_id, name: t.name_zh, year: t.first_year, problem: p.problem} : null;
  }).filter(Boolean).sort((a,b) => a.year - b.year || a.name.localeCompare(b.name, 'zh'));
  const stageOf = year => {
    for (let i = 0; i < DATA.periods.length; i++){
      const m = String(DATA.periods[i].span).match(/(\d{4})[–-](\d{4})?/);
      if (!m) continue;
      const a = +m[1], b = m[2] ? +m[2] : Infinity;
      if (year >= a && year < b) return i;
    }
    return DATA.periods.length - 1;
  };
  // stage 是界面归组，不必等于 from 所在时期：福柯 1960 年出道，却归在当代的
  // 「后结构/后现代」分支里；periods 仍按实际年份记录，详情里会如实写「横跨」。
  const displayStage = l => {
    const i = DATA.periods.findIndex(p => p.id === l.stage);
    return i >= 0 ? i : stageOf(l.from);
  };
  const SHORT_BRANCH = {
    '古典三大家': '古典三大家',
    '历史主义': '历史主义',
    '整合与中层': '整合/中层',
    '微观互动': '微观互动',
    '冲突与批判': '冲突',
    '其他现代分支': '其他分支',
    '综合路径': '综合路径',
    '后结构/后现代': '后结构',
    '全球/后殖民': '全球/后殖民',
    '晚近': '晚近',
    '批判与差异': '批判与差异',
  };
  const lo = 1830, hi = 2026;
  const stageSegs = DATA.periods.map((p, i) => {
    const m = String(p.span).match(/(\d{4})[–-](\d{4})?/);
    const a = m ? +m[1] : lo;
    const b = m && m[2] ? +m[2] : hi;
    return {i, name: p.name, a, b, flex: Math.max(1, b - a),
            label: String(p.span).endsWith('–') ? `${a}–${hi}` : String(p.span)};
  });
  const W = 1240, X0 = 104, X1 = W - 26;
  const STAGE_Y = 84, Y0 = 170, Y1 = 850, H = 930;
  const BW = (X1 - X0) / DATA.periods.length;
  const stageX = i => X0 + i * BW;
  const y = year => Y0 + (Math.max(lo, Math.min(hi, year)) - lo) / (hi - lo) * (Y1 - Y0);
  const P = [];

  // 横轴：三个阶段按顺序等宽排布，只表示先后，不表示时长比例；年份由左侧竖轴承担
  DATA.periods.forEach((p, i) => {
    const xa = stageX(i), xb = stageX(i + 1), xc = (xa + xb) / 2;
    const span = String(p.span).endsWith('–') ? `${String(p.span).slice(0, -1)} 至今` : p.span;
    P.push(`<rect class="stageband${i % 2 ? ' alt' : ''}" x="${xa}" y="${STAGE_Y + 16}" ` +
      `width="${BW}" height="${Y1 - STAGE_Y - 4}">` +
      `<title>${esc(p.name)}（${esc(p.span)}）：${esc(p.note || p.question)}</title></rect>`);
    P.push(`<line class="stageguide" x1="${xa}" y1="${STAGE_Y}" x2="${xa}" y2="${Y1}"/>`);
    P.push(`<text class="stagename" x="${xc}" y="28" text-anchor="middle">${esc(p.name)}</text>`);
    P.push(`<text class="stagespan" x="${xc}" y="45" text-anchor="middle">${esc(span)}</text>`);
    P.push(`<g class="stagenode"><circle cx="${xc}" cy="${STAGE_Y}" r="4.6"/></g>`);
    P.push(`<text class="stageno" x="${xc}" y="${STAGE_Y + 31}" text-anchor="middle">P${i + 1}</text>`);
  });
  P.push(`<line class="stageguide" x1="${X1}" y1="${STAGE_Y}" x2="${X1}" y2="${Y1}"/>`);
  P.push(`<line class="stageaxis" x1="${X0}" y1="${STAGE_Y}" x2="${X1}" y2="${STAGE_Y}"/>`);
  P.push(`<path class="stagearrow" d="M ${X1 - 9} ${STAGE_Y - 4} L ${X1} ${STAGE_Y} L ${X1 - 9} ${STAGE_Y + 4} Z"/>`);

  // 竖轴：年份。传统竖线与术语圆点都按这个坐标落位
  P.push(`<text class="yearaxis" x="${X0 - 10}" y="${Y0 - 11}" text-anchor="end">年份</text>`);
  for (let year = 1850; year <= 2000; year += 25){
    const yy = y(year);
    P.push(`<line class="yearline" x1="${X0}" y1="${yy}" x2="${X1}" y2="${yy}"/>`);
    P.push(`<text class="yearlabel" x="${X0 - 10}" y="${yy + 3}" text-anchor="end">${year}</text>`);
  }
  P.push(`<text class="yearlabel" x="${X0 - 10}" y="${Y1 + 3}" text-anchor="end">2026</text>`);

  // 阶段内先按 branch 聚簇，再在簇内排传统竖轴；主脉用深色，扩展传统用浅色
  const stageGroups = DATA.periods.map((p, pi) => {
    const arr = sorted.filter(l => displayStage(l) === pi);
    const map = new Map();
    arr.forEach(l => {
      const b = l.branch || '其他';
      if (!map.has(b)) map.set(b, []);
      map.get(b).push(l);
    });
    const order = (BRANCH_ORDER[p.id] || []).concat([...map.keys()]);
    const seen = new Set(), out = [];
    order.forEach(b => {
      if (map.has(b) && !seen.has(b)){ seen.add(b); out.push({branch: b, lines: map.get(b)}); }
    });
    return out;
  });
  stageGroups.forEach((branchGroups, pi) => {
    const xa = stageX(pi), xb = stageX(pi + 1);
    const left = xa + 16, right = xb - 16;
    const G = branchGroups.length;
    const N = branchGroups.reduce((n, g) => n + g.lines.length, 0);
    const gap = G > 1 ? 14 : 0;
    const unit = (right - left - gap * (G - 1)) / Math.max(1, N);
    let cursor = left;
    branchGroups.forEach(bg => {
      const width = bg.lines.length * unit;
      const center = cursor + width / 2;
      const core = bg.lines.some(l => l.tier === 'core');
      P.push(`<line class="branchrule${core ? ' core' : ''}" x1="${cursor + 2}" ` +
        `y1="${STAGE_Y + 40}" x2="${cursor + width - 2}" y2="${STAGE_Y + 40}"/>`);
      const bname = bg.branch;
      const blines = bname.includes('/')
        ? bname.split('/').map((part, k, all) => k < all.length - 1 ? part + '/' : part)
        : [SHORT_BRANCH[bname] || bname];
      P.push(`<text class="branchlabel${core ? ' core' : ''}" x="${center}" ` +
        `y="${STAGE_Y + 51}" text-anchor="middle">` +
        blines.map((line, k) => `<tspan x="${center}" dy="${k ? 9 : 0}">${esc(line)}</tspan>`).join('') +
        `</text>`);
      bg.lines.sort((a,b) => a.from - b.from || a.name.localeCompare(b.name, 'zh'));
      bg.lines.forEach((l, i) => {
        const x = cursor + (i + 0.5) * unit;
        const terms = termsOf(l.id);
        const ya = y(l.from), yb = y(l.ongoing ? hi : Math.min(l.to, hi));
        const dim = filtering && !(cnt[l.id] || 0);
        P.push(`<g class="linaxis${dim ? ' dim' : ''}" data-l="${l.id}" ` +
          `data-from="${l.from}" data-to="${l.ongoing ? hi : Math.min(l.to, hi)}" tabindex="0" role="button" ` +
          `aria-label="${esc(l.name)}，${terms.length} 个术语，悬停查看解释">`);
        P.push(`<rect class="thit" x="${x - 8}" y="${ya - 12}" width="16" height="${Math.max(24, yb - ya + 26)}"/>`);
        P.push(`<line class="tline" x1="${x}" y1="${ya}" x2="${x}" y2="${yb}"/>`);
        P.push(`<circle class="tstart" cx="${x}" cy="${ya}" r="3.3"/>`);
        P.push(`<text class="tid" x="${x}" y="${ya - 5}" text-anchor="middle">${l.id}</text>`);
        const byYear = {};
        terms.forEach(t => (byYear[t.year] ||= []).push(t));
        Object.keys(byYear).forEach(year => {
          const same = byYear[year];
          if (same.length > 1){
            const half = (same.length - 1) / 2 * 6 + 3;
            P.push(`<line class="tdotrack" x1="${x - half}" x2="${x + half}" y1="${y(+year)}" y2="${y(+year)}"/>`);
          }
          same.forEach((t, k) => {
            const off = (k - (same.length - 1) / 2) * 6;
            P.push(`<circle class="tdot" data-year="${t.year}" data-term="${t.id}" ` +
              `cx="${x + off}" cy="${y(+year)}" r="2.6">` +
              `<title>${esc(t.name)}（${t.year}）：${esc(t.problem)}</title></circle>`);
          });
        });
        P.push(`<text class="tcount" x="${x}" y="${yb + 12}" text-anchor="middle">${terms.length}</text>`);
        P.push(`</g>`);
      });
      cursor += width + gap;
    });
  });
  P.push(`<line class="timecursor" id="timeCursor" x1="${X0}" y1="${Y0}" x2="${X1}" y2="${Y0}"/>`);
  P.push(`<circle class="timecursor-dot" id="timeCursorDot" cx="${X0}" cy="${Y0}" r="3.4"/>`);
  P.push(`<text class="timecursor-label" id="timeCursorLabel" x="${X1 - 4}" y="${Y0 - 7}" text-anchor="end">${lo}</text>`);

  host.innerHTML = `<div class="stephead"><b>阶段轴 → 分支 → 传统 → 术语</b>` +
    `<span>横线是三个阶段；阶段内按分支聚拢传统；粗线为主脉，细线为扩展传统；圆点是术语首现年份；左侧竖线是年份轴。</span></div>` +
    `<div class="linhint">三个阶段按学科史顺序等宽排列，不表示各阶段时长比例。当代内部按「综合路径 / 后结构·后现代 / 全球·后殖民 / 晚近 / 批判与差异」分组。悬停任一传统竖线：` +
    `该传统会高亮，下方立即列出它的全部术语及「在本谱系中解释」；点击可把当前传统固定下来。</div>` +
    `<div class="linplay" id="linPlay">` +
      `<button class="playbtn" id="linPlayBtn" type="button" aria-label="播放谱系时间轴" aria-pressed="false">` +
        `<span class="playico" id="linPlayIco">▶</span><span id="linPlayTxt">播放时间轴</span></button>` +
      `<div class="playmid">` +
        `<div class="playhead"><output class="playyear" id="linPlayYear">${lo}</output>` +
          `<span class="playnote" id="linPlayNote">点击播放，按术语首现年份展开</span></div>` +
        `<div class="playtrack" id="linPlayTrack">` +
          `<input class="linrange" id="linPlayRange" type="range" min="${lo}" max="${hi}" value="${lo}" step="1" aria-label="谱系年份">` +
          `<div class="playsaur" id="linPlaySaur" aria-hidden="true">${DINO_SVG[2]}</div>` +
        `</div>` +
        `<div class="playticks" aria-hidden="true">` +
          [lo, 1900, 1950, hi].map(year => `<span style="left:${((year - lo) / (hi - lo) * 100).toFixed(2)}%">${year}</span>`).join('') +
        `</div>` +
        `<div class="playstages" id="linPlayStages" aria-hidden="true">` +
          stageSegs.map(s => `<span data-stage="${s.i}" style="flex:${s.flex} 1 0">` +
            `<b>${esc(s.name)}</b><small>${esc(s.label)}</small></span>`).join('') +
        `</div>` +
      `</div>` +
    `</div>` +
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMinYMin meet">${P.join('')}</svg>` +
    `<div class="linhover" id="linHover"></div>` +
    `<div class="lindet" id="linDet">悬停或点击一条传统竖线，查看它的全部术语与解释。</div>`;

  const hover = document.getElementById('linHover');
  const placeHover = e => {
    const pad = 12;
    const r = hover.getBoundingClientRect();
    let left = e.clientX + 14, top = e.clientY + 14;
    if (left + r.width > window.innerWidth - pad) left = e.clientX - r.width - 14;
    if (top + r.height > window.innerHeight - pad) top = e.clientY - r.height - 14;
    hover.style.left = `${Math.max(pad, left)}px`;
    hover.style.top = `${Math.max(pad, top)}px`;
  };
  host.querySelectorAll('.linaxis').forEach(g => {
    const id = g.dataset.l;
    const l = DATA.lineages.find(x => x.id === id);
    const terms = termsOf(id);
    const span = `${l.from}${l.ongoing ? '–至今' : '–' + l.to}`;
    const figs = (l.figures || []).length ? `代表：${l.figures.join('、')}` : '';
    const show = e => {
      showLineage(id);
      hover.innerHTML = `<b>${esc(l.name)}</b><span>${esc(l.branch || '')}　·　${l.tier === 'core' ? '主脉' : '扩展传统'}　·　${span}　·　${terms.length} 个术语</span>` +
        (figs ? `<span>${esc(figs)}</span>` : '') +
        `<p>${terms.map(t => esc(t.name)).join('、') || '暂无归属术语'}</p>` +
        `<small>下方已展开全部术语与解释</small>`;
      hover.style.display = 'block';
      if (e && e.clientX != null) placeHover(e);
    };
    g.addEventListener('mouseenter', show);
    g.addEventListener('mousemove', placeHover);
    g.addEventListener('mouseleave', () => { hover.style.display = 'none'; });
    g.addEventListener('click', () => showLineage(id));
    g.addEventListener('focus', () => showLineage(id));
    g.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); showLineage(id); }
    });
  });

  const wireTimeline = () => {
    const btn = document.getElementById('linPlayBtn');
    const ico = document.getElementById('linPlayIco');
    const txt = document.getElementById('linPlayTxt');
    const yearOut = document.getElementById('linPlayYear');
    const note = document.getElementById('linPlayNote');
    const range = document.getElementById('linPlayRange');
    const track = document.getElementById('linPlayTrack');
    const stageEls = [...document.querySelectorAll('#linPlayStages [data-stage]')];
    const cursor = document.getElementById('timeCursor');
    const cursorDot = document.getElementById('timeCursorDot');
    const cursorLabel = document.getElementById('timeCursorLabel');
    const dots = [...host.querySelectorAll('.tdot')].map(el => ({el, year: +el.dataset.year}));
    const axes = [...host.querySelectorAll('.linaxis')].map(el => ({
      el, id: el.dataset.l, from: +el.dataset.from, to: +el.dataset.to
    }));
    const yearEvents = new Map();
    DATA.terms.forEach(t => {
      const yr = Math.floor(+t.first_year);
      if (!Number.isFinite(yr) || yr < lo || yr > hi) return;
      const lines = DATA.placements.filter(p => p.term_id === t.term_id).map(p => p.lineage_id);
      if (!yearEvents.has(yr)) yearEvents.set(yr, []);
      yearEvents.get(yr).push({name: t.name_zh, lines});
    });
    const eventYears = [...yearEvents.keys()].sort((a, b) => a - b);

    let playYear = lo, playing = false, lastTs = 0, lastInt = -1, liveSeq = 0;
    let dwellUntil = 0, dwellYear = -1;
    const DUR = 22000;
    const setButton = (icon, label, active) => {
      ico.textContent = icon;
      txt.textContent = label;
      btn.classList.toggle('playing', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      btn.setAttribute('aria-label', active ? '暂停谱系时间轴' :
        (label === '重播' ? '从头播放谱系时间轴' : '播放谱系时间轴'));
    };
    const flash = ids => {
      const seq = ++liveSeq;
      axes.forEach(a => a.el.classList.toggle('live', ids.has(a.id)));
      if (ids.size) setTimeout(() => {
        if (seq === liveSeq && playing)
          axes.forEach(a => a.el.classList.remove('live'));
      }, 460);
    };
    const applyYear = (v, force, dwell) => {
      const yr = Math.floor(v);
      const yy = y(v);
      const pct = `${((v - lo) / (hi - lo) * 100).toFixed(2)}%`;
      cursor.setAttribute('y1', yy);
      cursor.setAttribute('y2', yy);
      cursorDot.setAttribute('cy', yy);
      cursorLabel.setAttribute('y', yy - 7);
      cursorLabel.textContent = yr;
      range.style.setProperty('--p', pct);
      track.style.setProperty('--p', pct);
      if (yr === lastInt && !force) return;
      lastInt = yr;
      yearOut.textContent = yr;
      range.value = yr;
      const si = stageOf(yr);
      stageEls.forEach(el => el.classList.toggle('on', +el.dataset.stage === si));
      dots.forEach(d => {
        d.el.classList.toggle('shown', d.year <= yr);
        d.el.classList.toggle('new', d.year === yr);
      });
      axes.forEach(a => a.el.classList.toggle('future', a.from > yr));
      const evNow = yearEvents.get(yr) || [];
      flash(new Set(evNow.flatMap(e => e.lines)));
      if (evNow.length && dwell && dwellYear !== yr){
        dwellYear = yr;
        dwellUntil = performance.now() + 650 + Math.min(2, evNow.length) * 120;
      }
      let prevYear = null;
      for (const ey of eventYears){ if (ey > yr) break; prevYear = ey; }
      const ev = prevYear == null ? [] : yearEvents.get(prevYear);
      note.textContent = ev.length
        ? `${prevYear} · ${ev.slice(0, 3).map(e => e.name).join('、')}` +
          `${ev.length > 3 ? ` 等 ${ev.length} 个术语` : ''}出现`
        : '';
    };
    const pause = () => {
      if (!playing) return;
      playing = false;
      dwellUntil = 0;
      cancelAnimationFrame(LIN_PLAY_RAF);
      LIN_PLAY_RAF = 0;
      host.classList.remove('playing');
      setButton('▶', '继续播放', false);
    };
    const finish = () => {
      playing = false;
      dwellUntil = 0;
      cancelAnimationFrame(LIN_PLAY_RAF);
      LIN_PLAY_RAF = 0;
      host.classList.remove('playing');
      playYear = hi;
      applyYear(hi, true);
      setButton('↺', '重播', false);
      note.textContent = `全部 ${DATA.placements.length} 条术语归属已出现`;
    };
    const step = ts => {
      if (!playing) return;
      if (!lastTs) lastTs = ts;
      if (ts < dwellUntil){
        lastTs = ts;
        LIN_PLAY_RAF = requestAnimationFrame(step);
        return;
      }
      const dt = Math.min(80, ts - lastTs);
      lastTs = ts;
      playYear = Math.min(hi, playYear + dt * (hi - lo) / DUR);
      applyYear(playYear, false, true);
      if (playYear >= hi){ finish(); return; }
      LIN_PLAY_RAF = requestAnimationFrame(step);
    };
    const start = () => {
      if (playing) return;
      host.classList.add('timeline');
      if (innerWidth >= 1100){
        const filters = document.querySelector('.filters');
        const fh = filters ? filters.offsetHeight : 0;
        const ph = document.querySelector('.linplay').offsetHeight || 0;
        const svg = host.querySelector('svg');
        const top = scrollY + svg.getBoundingClientRect().top;
        const target = Math.max(0, top - fh - ph - 14);
        if (Math.abs(scrollY - target) > 12)
          scrollTo({top: target, behavior: RM ? 'auto' : 'smooth'});
      }
      if (playYear >= hi - .01){
        playYear = lo;
        lastInt = -1;
        dwellUntil = 0;
        dwellYear = -1;
        applyYear(lo, true);
      }
      playing = true;
      lastTs = 0;
      host.classList.add('playing');
      setButton('❚❚', '暂停', true);
      LIN_PLAY_RAF = requestAnimationFrame(step);
    };
    btn.addEventListener('click', () => playing ? pause() : start());
    range.addEventListener('input', () => {
      pause();
      host.classList.add('timeline');
      playYear = +range.value;
      lastInt = -1;
      dwellUntil = 0;
      dwellYear = -1;
      applyYear(playYear, true);
      setButton(playYear >= hi ? '↺' : '▶', playYear >= hi ? '重播' : '继续播放', false);
      if (playYear >= hi)
        note.textContent = `全部 ${DATA.placements.length} 条术语归属已出现`;
    });
    host.querySelectorAll('.linaxis').forEach(g => g.addEventListener('click', pause));
    applyYear(lo, true);
    note.textContent = '点击播放，按术语首现年份展开';
  };
  wireTimeline();
  showLineage(S.lineage && DATA.lineages.some(l => l.id === S.lineage) ? S.lineage : sorted[0].id);
  document.getElementById('foot').textContent =
    `阶段轴视图：${DATA.periods.length} 个阶段 · ${DATA.lineages.length} 条传统 · ` +
    `${DATA.placements.length} 条术语归属　·　左侧竖轴＝年份；圆点＝术语首现年份`;
}

// flip 只在「筛选条件变了、而列表本身还留着」时传 true；
// 换视图、搜索、跳词条都传默认值，避免每次重排都补间
function draw(flip){
  const v = S.view;
  document.getElementById('list').style.display  = v === 'list'  ? '' : 'none';
  document.getElementById('graph').style.display = v === 'graph' ? 'block' : 'none';
  document.getElementById('lins').style.display  = v === 'lineages' ? 'block' : 'none';
  const n = DATA.terms.filter(matched).length;
  document.getElementById('sectionhead').innerHTML = v === 'list'
    ? `<span><b>TERM RECORDS</b> / 词条索引</span><span>${n} / ${DATA.terms.length}</span>`
    : v === 'graph'
    ? `<span><b>RELATION NETWORK</b> / 概念关系网络</span><span>${n} / ${DATA.terms.length}</span>`
    : `<span><b>DISCIPLINARY LINEAGES</b> / 学科谱系</span>` +
      `<span>${DATA.meta.periods} 阶段 · ${DATA.meta.lineages} 传统 · ${DATA.placements.length} 条归属</span>`;
  if (v === 'graph') renderGraph();
  else if (v === 'lineages') renderLineages();
  else render(flip);
}

function setViewBtns(v){
  ['vList','vGraph','vLineages'].forEach(k =>
    document.getElementById(k).classList.toggle('on', k === 'v' + v[0].toUpperCase() + v.slice(1)));
}

function initHomeVisual(){
  const cv = document.getElementById('homeCanvas');
  if (!cv || !cv.getContext) return;
  const ctx = cv.getContext('2d');
  let W = 0, H = 0, nodes = [], raf = 0, vis = true;
  const N = 46;
  const draw = () => {
    raf = 0;
    ctx.clearRect(0, 0, W, H);
    const R = Math.min(190, Math.max(120, W * .16));
    for (let i = 0; i < nodes.length; i++){
      const a = nodes[i];
      if (!RM){
        a.x += a.vx; a.y += a.vy;
        if (a.x < -10 || a.x > W + 10) a.vx *= -1;
        if (a.y < -10 || a.y > H + 10) a.vy *= -1;
      }
      for (let j = i + 1; j < nodes.length; j++){
        const b = nodes[j], dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy);
        if (d < R){
          ctx.strokeStyle = `rgba(0,0,0,${(1 - d / R) * .17})`;
          ctx.lineWidth = .7;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    nodes.forEach(n => {
      ctx.fillStyle = n.white ? `rgba(255,255,255,${n.a * .8})` : `rgba(0,0,0,${n.a})`;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fill();
    });
    if (!RM && vis) raf = requestAnimationFrame(draw);
  };
  const resize = () => {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    W = cv.clientWidth || cv.parentElement.clientWidth || 1200;
    H = cv.clientHeight || 280;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    nodes = Array.from({length:N}, (_, i) => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - .5) * .22, vy: (Math.random() - .5) * .22,
      r: 1 + Math.random() * 2.2,
      a: .18 + Math.random() * .42,
      white: i % 5 === 0
    }));
    if (RM) draw();
  };
  resize();
  addEventListener('resize', resize);
  if (!RM){
    if ('IntersectionObserver' in window){
      new IntersectionObserver(es => {
        vis = es[0].isIntersecting;
        if (vis && !raf) raf = requestAnimationFrame(draw);
      }, {threshold:.02}).observe(cv);
    }
    raf = requestAnimationFrame(draw);
  }
}

const QS = new URLSearchParams(location.search);
if (PAGE !== 'home'){
  clusterChips(document.getElementById('fCluster'));
  chips(document.getElementById('fSchool'), DATA.enums.school, 'school', 'school');
  chips(document.getElementById('fApp'), DATA.enums.application, 'application', 'app');
  document.getElementById('q').oninput = e => { S.q = e.target.value.trim(); draw(); };
  if (PAGE === 'lineages'){
    const lid = QS.get('lineage');
    if (lid && DATA.lineages.some(l => l.id === lid)) S.lineage = lid;
  }
  legend();
  setViewBtns(S.view);
  draw();
  const filterEl = document.querySelector('.filters');
  const syncFilterH = () => document.documentElement.style.setProperty(
    '--filterh', (filterEl ? filterEl.offsetHeight : 0) + 'px');
  syncFilterH();
  addEventListener('resize', syncFilterH);
  if (PAGE === 'terms' && QS.get('term')){
    const tid = QS.get('term');
    setTimeout(() => gotoCard(tid), 120);
  }
  if (PAGE === 'lineages' && QS.get('lineage')){
    setTimeout(() => {
      const lins = document.getElementById('lins');
      const fh = document.querySelector('.filters').offsetHeight || 0;
      const y = window.scrollY + lins.getBoundingClientRect().top - fh - 10;
      window.scrollTo({top:Math.max(0, y), behavior:RM ? 'auto' : 'smooth'});
    }, 160);
  }
} else {
  renderStrata();
  initHomeVisual();
  document.querySelectorAll('[data-count]').forEach(el => {
    const n = DATA.meta[el.dataset.count];
    if (n != null) el.textContent = n;
  });
  scheduleStrata();
}
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

    # 学科史大谱系：阶段 / 分支 / 传统 / 术语归属。
    macro_raw = load("lineages.yaml") or {}
    if not isinstance(macro_raw, dict):
        macro_raw = {}
    period_by_id = {}
    macro_periods = []
    for p in macro_raw.get("periods", []):
        item = {"id": p["period_id"], "name": p["name"], "span": p["span"],
                "question": p["question"], "note": p.get("note")}
        period_by_id[item["id"]] = item
        macro_periods.append(item)

    macro_lineages = []
    lineage_by_id = {}
    for l in macro_raw.get("lineages", []):
        item = {"id": l["lineage_id"], "name": l["name"], "from": l["from"],
                "to": l["to"], "ongoing": bool(l.get("ongoing")),
                "periods": l.get("periods", []), "schools": l.get("schools", []),
                "stage": l.get("stage"), "branch": l.get("branch"),
                "tier": l.get("tier", "extended"), "figures": l.get("figures", []),
                "question": l["question"], "thesis": l["thesis"],
                "blind": l["blind_spot"]}
        lineage_by_id[item["id"]] = item
        macro_lineages.append(item)

    macro_placements = []
    placed_by_term = {}
    for p in macro_raw.get("placements", []):
        tid, lid = p.get("term_id"), p.get("lineage_id")
        if tid not in by_id or lid not in lineage_by_id:
            continue
        l = lineage_by_id[lid]
        entry = {"term_id": tid, "lineage_id": lid, "problem": p["problem"]}
        macro_placements.append(entry)
        placed_by_term.setdefault(tid, []).append({
            "lineage_id": lid, "name": l["name"], "question": l["question"],
            "thesis": l["thesis"], "blind": l["blind"], "from": l["from"],
            "to": l["to"], "ongoing": l["ongoing"], "problem": p["problem"],
            "branch": l.get("branch"), "figures": l.get("figures", []),
            "periods": [{"name": period_by_id[pid]["name"],
                         "span": period_by_id[pid]["span"]}
                        for pid in l["periods"] if pid in period_by_id],
        })
    for t in terms:
        if t["term_id"] in placed_by_term:
            t["placed"] = sorted(placed_by_term[t["term_id"]],
                                 key=lambda x: (x["from"], x["name"]))

    cluster_names = list(schema.get("clusters", {}))
    lay = layout(terms, rels, cluster_names)
    rad = node_radii(terms, rels)
    lab = place_labels(terms, lay, rad, NET_W, NET_H)
    view = content_box(terms, lay, rad, lab)
    cluster_of = {t["term_id"]: t.get("cluster") for t in terms}
    bridges = sum(1 for r in rels
                  if cluster_of.get(r.get("from_term")) != cluster_of.get(r.get("to_term")))
    payload = {
        "meta": {"terms": len(terms), "relations": len(rels), "cases": len(cases),
                 "hotspots": len(hots),
                 "clusters": len(cluster_names), "bridges": bridges,
                 "polysemy": sum(1 for t in terms if t.get("polysemy")),
                 "lineages": len(macro_lineages),
                 "periods": len(macro_periods),
                 "placements": len(macro_placements),
                 "drafts": sum(1 for t in terms if t.get("status") == "草稿")},
        "enums": schema["enums"], "terms": terms,
        "clusters": schema.get("clusters", {}),
        "clusterOrder": cluster_names,
        "clusterColors": {c: CLUSTER_COLORS.get(c, FALLBACK_COLOR) for c in cluster_names},
        "clusterOf": {t["term_id"]: t.get("cluster") for t in terms},
        "periods": macro_periods, "lineages": macro_lineages,
        "placements": macro_placements,
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
    print(f"  学科谱系：{len(macro_periods)} 个阶段 · {len(macro_lineages)} 条传统 · "
          f"{len(macro_placements)} 条归属　OK")
    out = os.path.join(ROOT, "site")
    os.makedirs(out, exist_ok=True)
    data_json = json.dumps(payload, ensure_ascii=False)
    pages = [
        {"file": "index.html", "page": "home", "view": "list", "body": "page-home",
         "title": "社会学术语知识系统 · S.T.A.",
         "kicker": "TERM RECORDS / 词条索引 / 概念 · 关系 · 谱系",
         "h1a": "社会学术语", "h1b": "知识系统"},
        {"file": "terms.html", "page": "terms", "view": "list", "body": "page-terms",
         "title": "术语索引 · 社会学术语知识系统",
         "kicker": "TERM RECORDS / 术语索引 / FILTER · SEARCH · READ",
         "h1a": "术语索引", "h1b": "TERM RECORDS",
         "desc": "先按概念群、流派或应用场景收窄范围，再读词条。折叠区保留多义性、学科谱系、概念关系、经典案例与社会热点；没有内容的栏目不会出现。",
         "metrics": [(len(terms), "术语"), (len(cluster_names), "概念群"), (sum(1 for t in terms if t.get("polysemy")), "多义性")]},
        {"file": "network.html", "page": "network", "view": "graph", "body": "page-network",
         "title": "概念网络 · 社会学术语知识系统",
         "kicker": "RELATION NETWORK / 概念网络 / NODES · EDGES · BRIDGES",
         "h1a": "概念网络", "h1b": "RELATION NETWORK",
         "desc": "每条边都带类型、证据、编者解读与边界。群内关系按概念群着色，跨群桥接用琥珀色虚线标出；点击节点回到对应词条。",
         "metrics": [(len(terms), "节点"), (len(rels), "关系"), (bridges, "跨群桥接")]},
        {"file": "lineages.html", "page": "lineages", "view": "lineages", "body": "page-lineages",
         "title": "学科谱系 · 社会学术语知识系统",
         "kicker": "DISCIPLINARY LINEAGES / 学科谱系 / PERIODS · TRADITIONS",
         "h1a": "学科谱系", "h1b": "DISCIPLINARY LINEAGES",
         "desc": "三个阶段按学科史顺序等宽排列，不代表各阶段的真实时长。每一脉都写明它追问的问题、核心主张与盲点；悬停传统即可定位术语。",
         "metrics": [(len(macro_periods), "阶段"), (len(macro_lineages), "传统"), (len(macro_placements), "术语归属")]},
    ]
    for spec in pages:
        html = (TEMPLATE
                .replace("__DATA__", data_json)
                .replace("__PAGE_TITLE__", spec["title"])
                .replace("__PAGE__", spec["page"])
                .replace("__PAGE_VIEW__", spec["view"])
                .replace("__BODY_CLASS__", spec["body"])
                .replace("__APP_KICKER__", spec["kicker"])
                .replace("__APP_H1A__", spec["h1a"])
                .replace("__APP_H1B__", spec["h1b"])
                .replace("__SUB_DESC__", spec.get("desc", ""))
                .replace("__SUB_METRICS__", "".join(
                    f'<div class="subhead-metric"><b>{n}</b><span>{label}</span></div>'
                    for n, label in spec.get("metrics", []))))
        path = os.path.join(out, spec["file"])
        open(path, "w", encoding="utf-8").write(html)
        print(f"已生成 {path}（{len(html)/1024:.0f} KB）")
    print("站点：index.html / terms.html / network.html / lineages.html（自包含，无外部依赖）")


if __name__ == "__main__":
    main()
