"""跑驗證階梯 — 噪音地板 + L1 管線 + L2 行為 + L3 分數 + Exp2 遷移.

用法：
  python run.py --stub          # 免 API key，驗迴圈控制流＋回灌管線（L1/L2 + deterministic）
  python run.py --real          # 需 export ANTHROPIC_API_KEY，跑真 LLM（L3 分數 + 噪音地板 + 遷移）
  python run.py --real --model claude-sonnet-5
輸出：results/results.json + results/summary.md
"""
import argparse, json, os, sys
from iven_voice_graph import run_once, STYLE_PACK

HERE = os.path.dirname(os.path.abspath(__file__))

def _load_dotenv():
    p = os.path.join(HERE, ".env")
    if not os.path.exists(p): return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv()
SEEDS = json.load(open(os.path.join(HERE, "seeds/seeds.json"), encoding="utf-8"))["pairings"]


def frag(s: str, n: int = 16) -> str:
    return s[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--stub", action="store_true")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    mode = "real" if a.real else "stub"
    if mode == "real" and not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: --real 需 export ANTHROPIC_API_KEY")

    p1, p2 = SEEDS[0], SEEDS[1]
    report = {"mode": mode, "model": a.model, "checks": {}, "runs": {}}

    # naive_first：首稿故意用通用 prompt（無 style pack）＝模擬未調校 AI slop，
    # 逼 gate 退件 → 回灌 style pack 缺口 → 觀察真 LLM 有無被救回。
    # （真 Sonnet 直接套 style pack 首稿就過 0.70，迴圈不觸發，故用 naive 製造失敗起點。）
    NAIVE = mode == "real"

    # ---- 主迴圈：p1 跑一輪（含退件重寫）----
    r1 = run_once(p1, mode=mode, max_attempts=3, model=a.model, naive_first=NAIVE)
    report["runs"]["p1"] = r1
    report["naive_first"] = NAIVE
    h = r1["history"]

    # ---- 噪音地板：同 seed、不回灌、跑兩次，看 attempt-1 分數飄動 ----
    fa = run_once(p1, mode=mode, max_attempts=1, model=a.model, naive_first=NAIVE)["history"][0]["total"]
    fb = run_once(p1, mode=mode, max_attempts=1, model=a.model, naive_first=NAIVE)["history"][0]["total"]
    floor = round(abs(fa - fb), 3)
    report["checks"]["noise_floor"] = {"run_a": fa, "run_b": fb, "floor": floor}

    # ---- L1 管線：退件理由有無真的進下一輪 prompt ----
    l1 = None
    if r1["attempts"] > 1 and h[0]["pass"] is False and h[0].get("scores"):
        # 取 attempt0 失敗維度 label 片段，檢查是否出現在最終 prompt
        first_reasons = [d["label"] for d in STYLE_PACK["dimensions"]
                         if h[0]["scores"].get(d["key"], 1) < 0.5]
        l1 = any(fr in r1["last_prompt"] for fr in first_reasons) if first_reasons else None
    report["checks"]["L1_plumbing"] = {"redo_happened": r1["attempts"] > 1,
                                       "reason_in_next_prompt": l1}

    # ---- L2 行為：draft_v1 != draft_v2 ----
    l2 = (h[0]["draft"] != h[1]["draft"]) if len(h) > 1 else None
    report["checks"]["L2_behavior"] = {"v1_ne_v2": l2}

    # ---- L3 分數：回灌後總分升沒升，且提升 > 噪音地板 ----
    if len(h) > 1:
        lift = round(h[-1]["total"] - h[0]["total"], 3)
        report["checks"]["L3_score"] = {"first": h[0]["total"], "final": h[-1]["total"],
                                        "lift": lift, "beats_noise_floor": lift > floor}
    else:
        report["checks"]["L3_score"] = {"note": "首稿即過，無退件；改壞 seed 或降 threshold 觀察退件"}

    # ---- Exp2 遷移：p1 抽的規則套沒看過的 p2，first-draft 分數升沒升 ----
    rule = "redefinition（不是X而是Y重定義）低分：套招牌逆向共識句式 不是X而是Y。short_assertive（短句斷言化）低分：句子縮短。code_switch：術語留英文。"
    base2 = run_once(p2, mode=mode, max_attempts=1, model=a.model, naive_first=NAIVE)["history"][0]["total"]
    treat2 = run_once(p2, mode=mode, max_attempts=1, model=a.model, naive_first=NAIVE, preset_feedback=[rule])["history"][0]["total"]
    report["checks"]["L4_transfer"] = {"p2_baseline": base2, "p2_with_rule": treat2,
                                       "transfer_lift": round(treat2 - base2, 3),
                                       "learned_not_parroted": treat2 > base2}

    # ---- 輸出 ----
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(report, open(os.path.join(HERE, "results/results.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    write_summary(report)
    print_report(report)


def write_summary(rep):
    c = rep["checks"]
    def yn(v): return "✅" if v is True else ("❌" if v is False else "—")
    lines = [f"# Iven-Voice 核心迴圈 — 驗證結果（mode={rep['mode']}）\n"]
    nf = c["noise_floor"]; lines.append(f"**噪音地板** = {nf['floor']}（同題不回灌兩跑 {nf['run_a']} vs {nf['run_b']}）\n")
    lines.append("| 層 | 檢查 | 結果 | 判定 |")
    lines.append("|---|---|---|---|")
    l1 = c["L1_plumbing"]; lines.append(f"| L1 管線 | 退件理由進下一輪 prompt | redo={l1['redo_happened']}, in_prompt={l1['reason_in_next_prompt']} | {yn(l1['reason_in_next_prompt'])} |")
    l2 = c["L2_behavior"]; lines.append(f"| L2 行為 | v1≠v2 | {l2['v1_ne_v2']} | {yn(l2['v1_ne_v2'])} |")
    l3 = c.get("L3_score", {})
    if "lift" in l3: lines.append(f"| L3 分數 | 回灌提升 & 過噪音 | first={l3['first']} final={l3['final']} lift={l3['lift']} | {yn(l3['beats_noise_floor'])} |")
    else: lines.append(f"| L3 分數 | — | {l3.get('note','')} | — |")
    l4 = c["L4_transfer"]; lines.append(f"| L4 遷移 | 規則套 unseen 題升分 | base={l4['p2_baseline']} rule={l4['p2_with_rule']} lift={l4['transfer_lift']} | {yn(l4['learned_not_parroted'])} |")
    lines.append("\n> L5 語意（像不像 Iven）非離線層，需 Iven 盲測。stub 的隱性維度為 placeholder，數值僅驗管線。\n")
    # v1 vs final 對照
    h = rep["runs"]["p1"]["history"]
    lines.append("## v1（首稿）vs final（末稿）對照\n")
    lines.append(f"**v1** (total {h[0]['total']}):\n\n> {h[0]['draft']}\n")
    lines.append(f"**final** (total {h[-1]['total']}, attempts {rep['runs']['p1']['attempts']}):\n\n> {h[-1]['draft']}\n")
    open(os.path.join(HERE, "results/summary.md"), "w", encoding="utf-8").write("\n".join(lines))


def print_report(rep):
    print(json.dumps(rep["checks"], ensure_ascii=False, indent=2))
    print("\n→ results/summary.md 已寫")


if __name__ == "__main__":
    main()
