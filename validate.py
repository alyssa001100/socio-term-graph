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
         "cases": "cases.yaml", "hotspots": "hotspots.yaml"}


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


def check_all(d, schema):
    """校验目录 d 下的四张表，返回 (issues, counts)。供命令行与 selftest.py 共用。"""
    enums, req, cons = schema["enums"], schema["required"], schema["constraints"]
    fld = schema["fields"]

    data = {k: load(os.path.join(d, v)) for k, v in FILES.items()}
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
        seen_authors = set()
        for i, p in enumerate(t.get("polysemy") or [], 1):
            w = f"{where}.polysemy[{i}]"
            check_fields(issues, "terms.yaml", w, p, fld["polysemy"], "多义性字段")
            for f in ("author", "definition", "source"):
                if not p.get(f):
                    issues.append(("错误", "terms.yaml", f"{w}.{f}", "多义性条目必填"))
            check_enum(issues, "terms.yaml", w, "school", p.get("school", []), enums["school"])
            if p.get("author") in seen_authors:
                issues.append(("错误", "terms.yaml", w, f"同一作者 {p.get('author')} 重复列出"))
            seen_authors.add(p.get("author"))
    counts["terms"] = len(data["terms"])

    # ---------- 关系 ----------
    rel_ids = set()
    per_term = Counter()
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
    cluster_of = {t["term_id"]: t.get("cluster") for t in data["terms"]}
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
                # 防牵强的核心规则
                if not str(a.get("mismatch", "")).strip():
                    issues.append(("错误", fname, f"{w}.mismatch",
                                   "「不符之处」为空 —— 归属缺少反面说明，视为牵强附会"))
                if a.get("confidence") == "有争议" and not a.get("dissent"):
                    issues.append(("警告", fname, w, "确信度为「有争议」但未记录 dissent 意见"))
            check_min_len(issues, fname, where, c, "analysis", cons["analysis_min_chars"], "热点解析")
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
                if "REPLACE" in str(c.get("source_url", "")):
                    issues.append(("警告", fname, f"{where}.source_url", "来源链接仍是占位符，需替换为可核验来源"))
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
        if k == "bridges":
            continue
        print(f"  {FILES[k]:<16} {v} 条")
    print(f"  {'跨群桥接':<16} {counts['bridges']} 条")
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
