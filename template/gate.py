#!/usr/bin/env python3
"""gate.py — 用工具當裁判，而不是 AI 的意見。

檢查項目：
  1. 每個 sim log 的 UVM_ERROR / UVM_FATAL 都是 0，而且有跑完 report summary
  2. vplan 裡每個 REQ 至少有一次 `REQ_PASS`
  3. 偏題偵測：log 或原始碼裡出現 vplan 沒有的 REQ 編號 -> FAIL
  4. 凍結檔案被改 -> FAIL（和 .contract_hash 比對；第一次執行時建立）
  5. vplan 裡列的 covergroup 在 urg groups.txt 要達到 coverage_goal
  6. open_questions 還有 open 的 -> 列出來（WARN，提醒人去裁決）
輸出：gate_report.json，給「導演」模型與人看。結束碼 0 = PASS。
"""
import argparse, hashlib, json, os, re, sys, glob

REQ_RE = re.compile(r"\bREQ-\d{3,}\b")

def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vplan", default="vplan.json")
    ap.add_argument("--logs", default="logs")
    ap.add_argument("--urg", default="urgReport")
    ap.add_argument("--src", default="tb")
    a = ap.parse_args()

    vp = json.load(open(a.vplan, encoding="utf-8"))
    reqs = {r["id"]: r for r in vp["requirements"]}
    fails, warns = [], []

    # 1) sim logs
    passed = {rid: 0 for rid in reqs}
    seen_ids = set()
    sim_logs = [p for p in glob.glob(os.path.join(a.logs, "*.log"))
                if os.path.basename(p) not in ("compile.log", "urg.log")]
    if not sim_logs:
        fails.append("沒有找到任何模擬 log")
    for p in sim_logs:
        txt = open(p, encoding="utf-8", errors="replace").read()
        name = os.path.basename(p)
        m_err = re.search(r"UVM_ERROR\s*:\s*(\d+)", txt)
        m_fat = re.search(r"UVM_FATAL\s*:\s*(\d+)", txt)
        if not m_err or not m_fat:
            fails.append(f"{name}: 沒有 UVM report summary（可能當掉或 timeout）")
        else:
            if int(m_err.group(1)) or int(m_fat.group(1)):
                fails.append(f"{name}: UVM_ERROR={m_err.group(1)} UVM_FATAL={m_fat.group(1)}")
        for m in re.finditer(r"\[REQCHK\]\s*(REQ-\d+)\s+PASS", txt):
            if m.group(1) in passed:
                passed[m.group(1)] += 1
        seen_ids.update(REQ_RE.findall(txt))

    for rid, n in passed.items():
        if n == 0:
            fails.append(f"{rid}: 沒有任何 REQ_PASS（沒被檢查到）")

    # 3) 偏題偵測：原始碼裡的 REQ 編號
    for p in glob.glob(os.path.join(a.src, "**", "*.sv*"), recursive=True):
        seen_ids.update(REQ_RE.findall(open(p, encoding="utf-8", errors="replace").read()))
    for rid in sorted(seen_ids - set(reqs)):
        fails.append(f"{rid}: 不在 vplan 裡（偏題：有人自己加了需求）")

    # 4) 凍結檔案
    hash_file = ".contract_hash"
    cur = {f: sha(f) for f in vp.get("frozen_files", []) if os.path.exists(f)}
    for f in vp.get("frozen_files", []):
        if not os.path.exists(f):
            warns.append(f"凍結檔案不存在: {f}")
    if os.path.exists(hash_file):
        old = json.load(open(hash_file))
        for f, h in cur.items():
            if old.get(f) and old[f] != h:
                fails.append(f"凍結檔案被修改: {f}（要改請走 open question）")
    else:
        json.dump(cur, open(hash_file, "w"), indent=1)
        warns.append("第一次執行：已建立 .contract_hash")

    # 5) 功能覆蓋率（urg text 報告；不同 VCS 版本格式略有差異，必要時調整 regex）
    goal = vp.get("coverage_goal", {}).get("functional_pct", 100)
    gtxt_path = os.path.join(a.urg, "groups.txt")
    gtxt = open(gtxt_path, encoding="utf-8", errors="replace").read() if os.path.exists(gtxt_path) else ""
    if not gtxt:
        warns.append("找不到 urgReport/groups.txt，略過功能覆蓋率檢查")
    cov = {}
    for r in reqs.values():
        for cg in r.get("covergroups", []):
            m = re.search(r"(\d+(?:\.\d+)?)\s*%?[^\n]*\b" + re.escape(cg) + r"\b", gtxt) or \
                re.search(r"\b" + re.escape(cg) + r"\b[^\n]*?(\d+(?:\.\d+)?)", gtxt)
            if gtxt and not m:
                fails.append(f"{r['id']}: covergroup {cg} 不在覆蓋率報告裡")
            elif m:
                pct = float(m.group(1)); cov[cg] = pct
                if pct < goal:
                    fails.append(f"{r['id']}: {cg} = {pct}% < {goal}%")

    # 6) open questions
    for q in vp.get("open_questions", []):
        if q.get("status") == "open":
            warns.append(f"{q['id']} 待裁決: {q['question']}")

    report = {
        "result": "PASS" if not fails else "FAIL",
        "fails": fails, "warns": warns,
        "req_pass_counts": passed, "coverage": cov,
        "sim_logs": len(sim_logs),
    }
    json.dump(report, open("gate_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"GATE {report['result']}  fails={len(fails)} warns={len(warns)}")
    for f in fails: print("  FAIL", f)
    for w in warns: print("  WARN", w)
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
