#!/usr/bin/env python3
"""知识图谱数据校验器 —— 按 schema.yaml 定义的规范校验 data/ 下的条目。

用法：
    python3 validate.py                # 校验 data/
    python3 validate.py --dir negative # 校验指定目录

校验内容：必填字段、封闭枚举、ID 唯一、引用完整性、归属块反例必填、日期与复审周期。
"""
import argparse, datetime, glob, os, re, sys
from collections import Counter
import yaml

DATE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

FILES = {"terms": "terms.yaml", "relations": "relations.yaml",
         "cases": "cases.yaml", "hotspots": "hotspots.yaml",
         "genealogy": "genealogy.yaml"}


def load(path):
    if not os.path.exists(path):
        return None
    return yaml.safe_load(open(path, encoding="utf-8")) or []


def check_enum(issues, fname, where, field, value, allowed):
    vals = value if isinstance(value, list) else [value]
    for v in vals:
        if v not in allowed:
            issues.append(("错误", fname, f"{where}.{field}",
                           f"非法取值「{v}」，允许：{'/'.join(allowed[:4])}…"))


def check_required(issues, fname, where, record, req):
    for f in req:
        if f not in record or record[f] in (None, "", [], {}):
            issues.append(("错误", fname, f"{where}.{f}", "必填字段缺失或为空"))


def check_fields(issues, fname, where, record, allowed, label="字段"):
    """白名单校验：多余字段一律报错。

    行内 YAML 映射（{a: 1, b: 2}）里的值一旦含有英文逗号，就会被解析成
    两个字段——上一行的值被截断、后半段变成一个新字段。这类错误不会让
    校验失败，只会静默丢数据，必须靠白名单拦。
    """
    for k in record:
        if k not in allowed:
            issues.append(("错误", fname, where,
                           f"{label}「{k}」未在 schema.fields 中定义 —— 检查是否拼写错误，"
                           f"或上一行取值含英文逗号/换行导致被截断"))


def check_min_len(issues, fname, where, record, field, minimum, label=""):
    """长度下限：不是审美要求，是拦「写了等于没写」的值。

    「两者有关」「该说法与概念相符」这类值长度够了也仍然空，所以这条规则只
    负责挡住最短的那批；真正的门槛在规范细则里。
    """
    v = record.get(field)
    if v in (None, ""):
        return
    n = len(str(v).strip())
    if n < minimum:
        issues.append(("错误", fname, f"{where}.{field}",
                       f"{label or field}只有 {n} 字，少于下限 {minimum} 字"
                       f"—— 缺的是具体说明，不是字数"))


# 界面上带固定标签的字段：标签由 build_site.py 的模板加上去，数据里不该再写一遍
LABELED_FIELDS = {"match": "相符之处", "mismatch": "不符之处",
                  "explain": "编者解读", "boundary": "边界", "analysis": "解析"}

# 能由其它字段推出的分类标签：界面自己会标，数据里写死一遍是负债
DERIVED_LABEL = {"explain": "跨群桥接"}

# 出处只登记到「作者 + 书目」为止：页码与链接都不要求（v8 起）。
# 但「待填」标记比空着更危险——它看起来像已经登记过了，所以按字面拦下。
PLACEHOLDER_MARKERS = ("REPLACE", "待核", "待填", "TODO")
SOURCE_FIELDS = ("first_source", "definition_source", "source", "source_url")


def check_placeholder(issues, fname, where, record, fields=SOURCE_FIELDS):
    for f in fields:
        v = record.get(f)
        if isinstance(v, str) and any(m in v for m in PLACEHOLDER_MARKERS):
            issues.append(("警告", fname, f"{where}.{f}",
                           "出处含占位符标记 —— 不要求页码与链接，但不要留待填标记，"
                           "要么写作者与书目，要么留空"))


def check_label_echo(issues, fname, where, record):
    """拦「数据里把界面标签又写了一遍」。

    这个错误不会让任何校验失败：`match` 写成「相符之处是……」，渲染出来就是
    「相符之处：相符之处是……」。只能靠规则拦，人眼在几百条数据里看不出来。
    """
    for f, label in LABELED_FIELDS.items():
        v = record.get(f)
        if isinstance(v, str) and v.startswith(label):
            issues.append(("警告", fname, f"{where}.{f}",
                           f"取值以「{label}」开头，但界面会自动加上这个标签，"
                           f"页面上会重复成「{label}：{label}…」"))


def check_derived_label(issues, fname, where, record, cluster_of):
    """拦「把能推出的分类标签写死在数据里」。

    桥接与否由两端术语的 `cluster` 推出，界面自己会标（`build_site.py` 的
    `relRow()` 按 cluster 是否相同决定要不要挂「跨群桥接」标签）。数据里再写
    一遍，代价不只是页面上重复：术语迁去别的概念群之后，这行前缀会不声不响
    变成一句错的断言，而其它规则只看 cluster，永远发现不了。
    """
    label = DERIVED_LABEL.get("explain")
    v = record.get("explain")
    if not (isinstance(v, str) and v.startswith(label)):
        return
    a = cluster_of.get(record.get("from_term"))
    b = cluster_of.get(record.get("to_term"))
    if a and b and a != b:
        issues.append(("警告", fname, f"{where}.explain",
                       f"取值以「{label}」开头，但界面会按两端所属概念群自动标注这个标签，"
                       f"页面上会重复"))
    else:
        issues.append(("警告", fname, f"{where}.explain",
                       f"取值以「{label}」开头，但两端术语同属「{a}」群 —— 这行标签与实际的"
                       f"群归属矛盾，术语迁移后会变成错的断言"))


def check_schema(schema):
    """schema 自身的自洽性：clusters 与 enums.cluster 必须一一对应。
    新增一个概念群要同时改两处——clusters 里写核心问题、enums.cluster 里放开取值。
    只改前者不会报「配置有问题」，而是让该群的每一条术语都报「枚举非法」：
    错误信息指向数据，根因却在配置，是这套系统里最难查的一类报错。
    这条规则把根因直接点出来，让报错指向该改的那一行。
    """
    issues = []
    declared = set(schema.get("clusters") or {})
    allowed = set(schema["enums"].get("cluster") or [])
    for c in sorted(declared - allowed):
        issues.append(("错误", "schema.yaml", "schema.clusters",
                       f"概念群「{c}」在 clusters 里有定义，却不在 enums.cluster 里 —— "
                       f"该群术语会被误判为枚举非法"))
    for c in sorted(allowed - declared):
        issues.append(("错误", "schema.yaml", "schema.clusters",
                       f"枚举值「{c}」在 enums.cluster 里，却不在 clusters 中 —— 缺核心问题定义"))
    return issues



def check_genealogy(issues, gen, term_ids, schema, fname="genealogy.yaml"):
    """谱系校验：三张子表（谱系 / 版本 / 边）之间的关系约束。

    这里有一条别处没有的硬规则：**谱系边两端必须属于同一个术语**。
    跨术语的谱系（例如「理性化 → 麦当劳化」）已经由 relations.yaml 承担，
    在这里再记一遍就是同一事实存两份，两处一旦不同步就会互相矛盾。
    """
    enums, req, cons, fld = schema["enums"], schema["required"], schema["constraints"], schema["fields"]
    if not isinstance(gen, dict):
        issues.append(("错误", fname, "根", "genealogy.yaml 应为 {lineages, nodes, edges} 三段"))
        return 0, 0, 0

    lins = gen.get("lineages") or []
    nodes = gen.get("nodes") or []
    edges = gen.get("edges") or []

    lin_term, lin_ids = {}, set()
    for l in lins:
        where = l.get("lineage_id", "?")
        check_required(issues, fname, where, l, req["genealogy_lineages"])
        check_fields(issues, fname, where, l, fld["genealogy_lineage"], "谱系字段")
        if where in lin_ids:
            issues.append(("错误", fname, where, "lineage_id 重复"))
        lin_ids.add(where)
        if l.get("term_id") not in term_ids:
            issues.append(("错误", fname, f"{where}.term_id",
                           f"谱系挂在不存在的术语 {l.get('term_id')} 上"))
        lin_term[where] = l.get("term_id")
        check_enum(issues, fname, where, "status", l.get("status"), enums["status"])
        check_placeholder(issues, fname, where, l)

    node_lin, node_ids = {}, set()
    for n in nodes:
        where = n.get("node_id", "?")
        check_required(issues, fname, where, n, req["genealogy_nodes"])
        check_fields(issues, fname, where, n, fld["genealogy_node"], "版本字段")
        if where in node_ids:
            issues.append(("错误", fname, where, "node_id 重复"))
        node_ids.add(where)
        if n.get("lineage_id") not in lin_ids:
            issues.append(("错误", fname, f"{where}.lineage_id",
                           f"引用了不存在的谱系 {n.get('lineage_id')}"))
        node_lin[where] = n.get("lineage_id")
        if not re.match(r"^\d{4}$", str(n.get("year", ""))):
            issues.append(("错误", fname, f"{where}.year", "年份格式应为 YYYY"))
        check_min_len(issues, fname, where, n, "claim", cons["claim_min_chars"], "定义要点")
        # 版本的出处由 作者+书名+年份 唯一确定，所以 book 就是它的 source，
        # 占位符检查必须覆盖 work，否则「待补书名」会一路混进正式数据
        check_placeholder(issues, fname, where, n, SOURCE_FIELDS + ("work",))

    used_lineages = Counter(node_lin.values())
    for lid in lin_ids:
        if not used_lineages.get(lid):
            issues.append(("错误", fname, lid, "这条谱系没有任何版本 —— 要么补版本，要么删除谱系"))

    parents = {nid: [] for nid in node_ids}
    edge_ids = set()
    for e in edges:
        where = e.get("edge_id", "?")
        check_required(issues, fname, where, e, req["genealogy_edges"])
        check_fields(issues, fname, where, e, fld["genealogy_edge"], "谱系边字段")
        if where in edge_ids:
            issues.append(("错误", fname, where, "edge_id 重复"))
        edge_ids.add(where)
        check_enum(issues, fname, where, "type", e.get("type"), enums["genealogy_edge_type"])
        a, b = e.get("from"), e.get("to")
        if a not in node_ids:
            issues.append(("错误", fname, f"{where}.from", f"引用了不存在的版本 {a}"))
            continue
        if b not in node_ids:
            issues.append(("错误", fname, f"{where}.to", f"引用了不存在的版本 {b}"))
            continue
        ta = lin_term.get(node_lin.get(a))
        tb = lin_term.get(node_lin.get(b))
        if ta != tb:
            issues.append(("错误", fname, where,
                           f"谱系边跨了术语（{ta} → {tb}）—— 跨术语关系归 relations.yaml，"
                           f"不在此重复；若确实是同一个词的两个版本，应归入同一条谱系"))
            continue
        ya = next((n.get("year") for n in nodes if n.get("node_id") == a), None)
        yb = next((n.get("year") for n in nodes if n.get("node_id") == b), None)
        if ya and yb and int(ya) > int(yb):
            issues.append(("错误", fname, where,
                           f"时间倒流：{a}({ya}) → {b}({yb})，后一版必须不早于前一版"))
        parents[b].append(a)
        check_min_len(issues, fname, where, e, "what_changed", cons["change_min_chars"], "改掉了什么")
        check_min_len(issues, fname, where, e, "evidence", cons["genealogy_evidence_min_chars"], "证据")
        check_placeholder(issues, fname, where, e)

    # 环检测：谱系是有向无环图，成环说明有人把「后者影响前者」也记了一条边
    state = {}
    cycles = []

    def dfs(u, stack):
        state[u] = 1
        for v in parents.get(u, []):
            if state.get(v) == 1:
                # 报在环上编号最小的节点：遍历起点由 sorted() 决定，但
                # set 的迭代顺序受字符串哈希随机化影响，不能拿起点当定位
                path = stack[stack.index(v):] + [u, v] if v in stack else [u, v]
                cycles.append(path)
                continue
            if state.get(v) is None:
                dfs(v, stack + [u])
        state[u] = 2

    for nid in sorted(node_ids):
        if state.get(nid) is None:
            dfs(nid, [])

    seen_cycles = set()
    for path in cycles:
        key = frozenset(path)
        if key in seen_cycles:
            continue
        seen_cycles.add(key)
        issues.append(("错误", fname, min(path),
                       f"谱系成环：{' → '.join(path)}"))

    return len(lins), len(nodes), len(edges)



def check_all(d, schema):
    """校验目录 d 下的四张表，返回 (issues, counts)。供命令行与 selftest.py 共用。"""
    enums, req, cons = schema["enums"], schema["required"], schema["constraints"]
    fld = schema["fields"]

    data = {k: load(os.path.join(d, v)) for k, v in FILES.items() if k != "genealogy"}
    data["genealogy"] = load(os.path.join(d, "genealogy.yaml")) or {}
    issues, counts = check_schema(schema), {}

    # ---------- 术语 ----------
    term_ids = set()
    for t in data["terms"]:
        where = t.get("term_id", "?")
        check_required(issues, "terms.yaml", where, t, req["terms"])
        check_fields(issues, "terms.yaml", where, t, fld["terms"])
        tid = t.get("term_id")
        if tid in term_ids:
            issues.append(("错误", "terms.yaml", tid, "term_id 重复"))
        term_ids.add(tid)
        if not DATE.match(str(t.get("first_year", ""))) and not re.match(r"^\d{4}$", str(t.get("first_year", ""))):
            issues.append(("错误", "terms.yaml", f"{where}.first_year", "年份格式应为 YYYY"))
        check_enum(issues, "terms.yaml", where, "school", t.get("school", []), enums["school"])
        check_enum(issues, "terms.yaml", where, "cluster", t.get("cluster"), enums["cluster"])
        check_enum(issues, "terms.yaml", where, "application", t.get("application", []), enums["application"])
        check_enum(issues, "terms.yaml", where, "status", t.get("status"), enums["status"])
        check_enum(issues, "terms.yaml", where, "confidence", t.get("confidence"), enums["confidence"])
        check_enum(issues, "terms.yaml", where, "entry_type", t.get("entry_type"), enums["entry_type"])
        check_placeholder(issues, "terms.yaml", where, t)
        seen_authors = set()
        for i, p in enumerate(t.get("polysemy") or [], 1):
            w = f"{where}.polysemy[{i}]"
            check_fields(issues, "terms.yaml", w, p, fld["polysemy"], "多义性字段")
            for f in ("author", "definition", "source"):
                if not p.get(f):
                    issues.append(("错误", "terms.yaml", f"{w}.{f}", "多义性条目必填"))
            check_placeholder(issues, "terms.yaml", w, p)
            check_enum(issues, "terms.yaml", w, "school", p.get("school", []), enums["school"])
            if p.get("author") in seen_authors:
                issues.append(("错误", "terms.yaml", w, f"同一作者 {p.get('author')} 重复列出"))
            seen_authors.add(p.get("author"))
    counts["terms"] = len(data["terms"])

    # ---------- 关系 ----------
    rel_ids = set()
    per_term = Counter()
    cluster_of = {t["term_id"]: t.get("cluster") for t in data["terms"]}
    for r in data["relations"]:
        where = r.get("rel_id", "?")
        check_required(issues, "relations.yaml", where, r, req["relations"])
        check_fields(issues, "relations.yaml", where, r, fld["relations"])
        if r.get("rel_id") in rel_ids:
            issues.append(("错误", "relations.yaml", where, "rel_id 重复"))
        rel_ids.add(r.get("rel_id"))
        check_enum(issues, "relations.yaml", where, "type", r.get("type"), enums["relation_type"])
        check_enum(issues, "relations.yaml", where, "status", r.get("status"), enums["status"])
        check_min_len(issues, "relations.yaml", where, r, "explain",
                      cons["explain_min_chars"], "关系解释")
        check_min_len(issues, "relations.yaml", where, r, "boundary",
                      cons["boundary_min_chars"], "边界说明")
        check_label_echo(issues, "relations.yaml", where, r)
        check_derived_label(issues, "relations.yaml", where, r, cluster_of)
        check_placeholder(issues, "relations.yaml", where, r)
        for side in ("from_term", "to_term"):
            if r.get(side) not in term_ids:
                issues.append(("错误", "relations.yaml", f"{where}.{side}",
                               f"引用了不存在的术语 {r.get(side)}"))
            per_term[r.get(side)] += 1
        if r.get("from_term") == r.get("to_term"):
            issues.append(("错误", "relations.yaml", where, "关系两端指向同一术语"))
    for tid, n in per_term.items():
        if n > cons["relations_per_term_max"]:
            issues.append(("警告", "relations.yaml", tid,
                           f"关系数 {n} 超过上限 {cons['relations_per_term_max']}，检查是否过度连接"))
    counts["relations"] = len(data["relations"])

    # 跨群桥接：跨概念群的关系最容易牵强，单独设约束
    pair_bridges, bridges = Counter(), 0
    for r in data["relations"]:
        ca, cb = cluster_of.get(r.get("from_term")), cluster_of.get(r.get("to_term"))
        if not ca or not cb or ca == cb:
            continue
        bridges += 1
        pair_bridges[tuple(sorted((ca, cb)))] += 1
        if r.get("type") == "等同":
            issues.append(("错误", "relations.yaml", r.get("rel_id"),
                           "跨概念群不得断言「等同」—— 若两个术语确实同一，说明两个群本应合并"))
    for (ca, cb), n in pair_bridges.items():
        if n > cons["bridge_per_cluster_pair_max"]:
            issues.append(("警告", "relations.yaml", f"{ca} ↔ {cb}",
                           f"桥接 {n} 条，超过每对概念群上限 "
                           f"{cons['bridge_per_cluster_pair_max']}，检查是否有为了连通而连的边"))
    counts["bridges"] = bridges

    # ---------- 谱系 ----------
    gl, gn, ge = check_genealogy(issues, data["genealogy"], term_ids, schema)
    counts["genealogy"], counts["g_nodes"], counts["g_edges"] = gl, gn, ge

    # 谱系与多义性的一致性：同一个作者不能在两处给出互相矛盾的身份
    # （多义性记「还有谁这么定义」，谱系记「这些定义怎么一步步变来」——同一个作者
    #  若在多义性里，却不在谱系里，说明有一条改动链断在中间，值得人工看一眼）
    by_term = {}
    for n in (data["genealogy"].get("nodes") or []):
        lid = n.get("lineage_id")
        tid = next((l.get("term_id") for l in (data["genealogy"].get("lineages") or [])
                    if l.get("lineage_id") == lid), None)
        by_term.setdefault(tid, set()).add(n.get("author"))
    for t in data["terms"]:
        if t.get("term_id") not in by_term:
            continue
        authors = {p.get("author") for p in (t.get("polysemy") or [])}
        missing = authors - by_term[t["term_id"]]
        if missing:
            issues.append(("警告", "terms.yaml", t.get("term_id"),
                           f"多义性里的 {'、'.join(sorted(missing))} 不在谱系中 —— "
                           f"若他确实改写过该词，应补成版本；若只是另一种用法，可在 note 里说明"))

    # 分析范畴是划分维度，不应被具体现象归属
    categories = {t["term_id"] for t in data["terms"] if t.get("entry_type") == "分析范畴"}

    # ---------- 案例与热点（共用归属块校验）----------
    for key, fname in (("cases", "cases.yaml"), ("hotspots", "hotspots.yaml")):
        id_field = "case_id" if key == "cases" else "hot_id"
        seen_ids = set()
        for c in data[key]:
            where = c.get("case_id") or c.get("hot_id") or "?"
            if c.get(id_field) in seen_ids:
                issues.append(("错误", fname, where, f"{id_field} 重复"))
            seen_ids.add(c.get(id_field))
            check_required(issues, fname, where, c, req[key])
            check_fields(issues, fname, where, c, fld[key])
            check_enum(issues, fname, where, "status", c.get("status"), enums["status"])
            atts = c.get("attributions") or []
            if len(atts) < cons["attribution_min"]:
                issues.append(("错误", fname, where,
                               f"归属数 {len(atts)} 少于下限 {cons['attribution_min']}"))
            for i, a in enumerate(atts, 1):
                w = f"{where}.attributions[{i}]"
                check_fields(issues, fname, w, a, fld["attribution"], "归属块字段")
                check_required(issues, fname, w, a, req["attribution_required"])
                check_enum(issues, fname, w, "confidence", a.get("confidence"), enums["confidence"])
                if a.get("term_id") in categories:
                    issues.append(("警告", fname, f"{w}.term_id",
                                   f"{a.get('term_id')} 是分析范畴，不应被具体现象归属"))
                if a.get("term_id") not in term_ids:
                    issues.append(("错误", fname, f"{w}.term_id",
                                   f"引用了不存在的术语 {a.get('term_id')}"))
                check_min_len(issues, fname, w, a, "match", cons["match_min_chars"], "相符之处")
                check_label_echo(issues, fname, w, a)
                # 防牵强的核心规则
                if not str(a.get("mismatch", "")).strip():
                    issues.append(("错误", fname, f"{w}.mismatch",
                                   "「不符之处」为空 —— 归属缺少反面说明，视为牵强附会"))
                if a.get("confidence") == "有争议" and not a.get("dissent"):
                    issues.append(("警告", fname, w, "确信度为「有争议」但未记录 dissent 意见"))
            check_min_len(issues, fname, where, c, "analysis", cons["analysis_min_chars"], "热点解析")
            check_label_echo(issues, fname, where, c)
            check_placeholder(issues, fname, where, c)
            if key == "hotspots":
                dt, ra = str(c.get("date", "")), str(c.get("review_after", ""))
                for f, v in (("date", dt), ("review_after", ra)):
                    if not DATE.match(v):
                        issues.append(("错误", fname, f"{where}.{f}", "日期格式应为 YYYY-MM"))
                if DATE.match(dt) and DATE.match(ra) and ra <= dt:
                    issues.append(("错误", fname, f"{where}.review_after", "复审日期必须晚于事件日期"))
                if DATE.match(ra):
                    ty, tm = int(ra[:4]), int(ra[5:7])
                    today = datetime.date.today()
                    if (ty, tm) < (today.year, today.month):
                        issues.append(("警告", fname, f"{where}.review_after",
                                       f"已过复审期（{ra}）—— 复审后延后日期，或降级为「历史热点」"))
        counts[key] = len(data[key])

    return issues, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data")
    args = ap.parse_args()
    root = os.path.dirname(os.path.abspath(__file__))
    schema = yaml.safe_load(open(os.path.join(root, "schema.yaml"), encoding="utf-8"))
    d = args.dir if os.path.isabs(args.dir) else os.path.join(root, args.dir)
    issues, counts = check_all(d, schema)

    # ---------- 输出 ----------
    print(f"校验目录：{os.path.relpath(d, root)}")
    for k, v in counts.items():
        if k in ("bridges", "genealogy", "g_nodes", "g_edges"):
            continue
        print(f"  {FILES.get(k, k):<16} {v} 条")
    print(f"  {'跨群桥接':<16} {counts['bridges']} 条")
    print(f"  {'谱系':<16} {counts['genealogy']} 条（版本 {counts['g_nodes']} 个，"
          f"边 {counts['g_edges']} 条）")
    print()
    if not issues:
        print("全部通过，未发现问题。")
        return 0
    lvl = Counter(i[0] for i in issues)
    print(f"发现 {len(issues)} 个问题：错误 {lvl['错误']}、警告 {lvl['警告']}\n")
    for level in ("错误", "警告"):
        for l, f, w, msg in issues:
            if l == level:
                print(f"  [{l}] {f} · {w}：{msg}")
    return 1 if lvl["错误"] else 0


if __name__ == "__main__":
    sys.exit(main())
