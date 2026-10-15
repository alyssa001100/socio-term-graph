#!/usr/bin/env python3
"""标注者间一致性检验 —— 对应《标注规范细则》第六节。

用法：python3 agreement.py annotations/*.yaml

三个指标：
  完全一致率        最直观，但会高估一致性
  平均 Jaccard      多标签集合的重合程度
  Krippendorff's α  主指标，可处理多标注者与缺失

已知局限：多标签展开为二值矩阵后会低估 α，须与 Jaccard 对照解读。
"""
import glob, itertools, sys
from collections import defaultdict
import yaml


def jaccard(a, b):
    if not (a or b):
        return 1.0
    return len(a & b) / len(a | b)


def alpha_from_units(units):
    """名义尺度 α。units 中每个元素是一组该单元上各标注者给出的取值。"""
    n = sum(len(u) for u in units)
    if not units or n < 2:
        return None
    do = sum(2 * sum(u) * (len(u) - sum(u)) / (len(u) - 1) for u in units) / n
    flat = [v for u in units for v in u]
    n1 = sum(flat)
    n0 = len(flat) - n1
    de = 2 * n1 * n0 / (n * (n - 1))
    return None if de == 0 else 1 - do / de


def units_for(by_item, names, labels):
    """把 (条目, 术语) 展开成二值单元。labels 决定编码本范围。"""
    units = []
    for _, annot in sorted(by_item.items()):
        if len(annot) < 2:
            continue
        for t in labels:
            units.append([1 if t in s else 0 for s in annot.values()])
    return units


def codebook_from_terms(path="data/terms.yaml"):
    try:
        return [t["term_id"] for t in yaml.safe_load(open(path, encoding="utf-8"))]
    except Exception:
        return []


def main():
    import argparse
    ap = argparse.ArgumentParser(description="标注者间一致性检验")
    ap.add_argument("files", nargs="*", help="标注者 yaml 文件")
    ap.add_argument("--codebook", default=None,
                    help="编码本（term_id 的 yaml 列表）。不指定则读取 data/terms.yaml")
    args = ap.parse_args()
    files = args.files or sorted(glob.glob("annotations/*.yaml"))
    if len(files) < 2:
        print("至少需要两份标注文件"); return 1

    data = {}
    for f in files:
        d = yaml.safe_load(open(f, encoding="utf-8"))
        data[d["annotator"]] = {i["item_id"]: set(i["term_ids"])
                                for i in (d.get("labels") or [])}
    names = list(data)

    by_item = defaultdict(dict)
    for who in names:
        for item, terms in data[who].items():
            by_item[item][who] = terms

    items = sorted(by_item)
    both = [i for i in items if len(by_item[i]) == len(names)]
    print(f"标注者：{', '.join(names)}")
    print(f"复标条目：{len(items)} 条（其中 {len(both)} 条被全员标注）\n")

    exact = sum(1 for i in both if len(set(map(frozenset, by_item[i].values()))) == 1)
    jac = [jaccard(by_item[i][names[0]], by_item[i][names[1]]) for i in both] \
        if len(names) == 2 else []

    # 编码本口径决定 α 的取值，必须给区间而非单一数值
    mention_union = sorted({t for i in both for v in by_item[i].values() for t in v})
    base = (yaml.safe_load(open(args.codebook, encoding="utf-8"))
            if args.codebook else codebook_from_terms())
    codebook = sorted(set(base or []) | set(mention_union))
    a_low = alpha_from_units(units_for(by_item, names, mention_union))
    a_high = alpha_from_units(units_for(by_item, names, codebook))
    alpha = a_high

    print("── 分歧条目 ──")
    shown = 0
    for i in both:
        vals = [by_item[i][w] for w in names]
        if len(set(map(frozenset, vals))) > 1:
            shown += 1
            a, b = vals[0], vals[1]
            print(f"  {i}  {names[0]}:{sorted(a) or '空'}  {names[1]}:{sorted(b) or '空'}"
                  f"   仅{names[0]}有:{sorted(a-b)} 仅{names[1]}有:{sorted(b-a)}")
    if not shown:
        print("  无")

    print("\n── 一致性指标 ──")
    if both:
        print(f"  完全一致率        {exact}/{len(both)} = {exact/len(both):.3f}")
    if jac:
        print(f"  平均 Jaccard 重合  {sum(jac)/len(jac):.3f}")
    if a_low is not None and a_high is not None:
        print(f"  Krippendorff α    {a_low:.3f} ～ {a_high:.3f}   （下界=仅计入被提及的术语，"
              f"{len(mention_union)} 个；上界=计入完整编码本，{len(codebook)} 个）")
        print(f"    区间说明：多标签数据上 α 随编码本口径变动。下界因多数类被放大而偏低，"
              f"上界因大量「双方都未标注」的空单元而偏高。")
        print(f"    解读纪律：α 不可单用，须与下方可解释指标对照。")
    if alpha is not None:
        if alpha >= 0.80:
            verdict = "规范可用，可进入正式标注"
        elif alpha >= 0.67:
            verdict = "仅供探索性结论，须逐条复核分歧点"
        else:
            verdict = "规范不可用 —— 必须修改规范后重新复标，不得靠培训标注员绕过"
        print(f"\n  判定：{verdict}")
    else:
        print("  Krippendorff α    无法计算（分歧期望值缺失或有效单元不足）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
