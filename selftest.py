#!/usr/bin/env python3
"""负例自检 —— 验证校验器本身能不能抓住每一条规范。

只跑一遍 validate.py 看输出没有意义：人眼会漏，也说不清「看到的就是全部」。
这个脚本按 negative/expected.yaml 的清单逐条断言，并统计未被认领的报错。

结论只有两种：
  命中全部注入点、且没有多余报错 —— 校验器可信；
  出现漏检 —— 某条规范形同虚设，必须修 validate.py；
  出现误报 —— 负例数据里有非预期问题，或某条规则过严。

用法：
    python3 selftest.py
"""
import os
import sys
import yaml
from validate import check_all

ROOT = os.path.dirname(os.path.abspath(__file__))
NEG = os.path.join(ROOT, "negative")


def main():
    schema = yaml.safe_load(open(os.path.join(ROOT, "schema.yaml"), encoding="utf-8"))
    # N57 注入 schema 自身的不一致：只在 clusters 里登记，没在 enums.cluster 里放开。
    #     该群不挂任何术语，因此不会连带污染其它负例的报错。
    schema["clusters"]["负例未登记群"] = "负例：只在 clusters 出现，未在 enums.cluster 出现"
    expected = yaml.safe_load(open(os.path.join(NEG, "expected.yaml"), encoding="utf-8"))
    issues, _ = check_all(NEG, schema)

    claimed = [False] * len(issues)
    missed = []
    for e in expected:
        for i, (lvl, fname, where, msg) in enumerate(issues):
            if claimed[i]:
                continue
            if (lvl == e["level"] and fname == e["file"]
                    and where == e["where"] and e["contains"] in msg):
                claimed[i] = True
                break
        else:
            missed.append(e)

    extra = [issues[i] for i, c in enumerate(claimed) if not c]
    hit = len(expected) - len(missed)

    print(f"负例集：{os.path.relpath(NEG, ROOT)}")
    print(f"  注入的规范违反点   {len(expected)} 个")
    print(f"  校验器实际报错     {len(issues)} 条")
    print(f"  命中 {hit} · 漏检 {len(missed)} · 误报 {len(extra)}\n")

    for e in missed:
        print(f"  [漏检] {e['id']} · {e['file']} · {e['where']}")
        print(f"         期望报{e['level']}「{e['contains']}」（{e['desc']}），校验器没有报出来")
    for lvl, fname, where, msg in extra:
        print(f"  [误报] {fname} · {where}：{msg}")

    if missed or extra:
        print("\n自检不通过：校验器的实际行为与预期清单不一致。")
        return 1
    print("自检通过：每条注入的违规都被精确命中，且没有多余报错。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
