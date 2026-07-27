"""B3 校準 — 拿 contrastive judge 直接測 seeds/eval_set.json 的 6 真 Iven + 5 slop，
看能不能分開（有 gap）。跟 run.py 的 draft→gate 迴圈無關，只測 judge 本身準不準。

用法：python calibrate.py   （需 export ANTHROPIC_API_KEY，走 real judge）
輸出：results/calibration.json + 印出 gap 判定
"""
import json, os, sys
from iven_voice_graph import EVAL_SET, make_caller, _contrastive_judge

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    p = os.path.join(HERE, ".env")
    if not os.path.exists(p): return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: 需 export ANTHROPIC_API_KEY")
    judge_model = os.environ.get("SPIKE_JUDGE_MODEL", "claude-haiku-4-5-20251001")
    judge_call = make_caller("real", judge_model)

    rows = []
    for e in EVAL_SET["iven_tier_a"]:
        score = _contrastive_judge(e["text"], judge_call)
        rows.append({"id": e["id"], "label": "iven_tier_a", "score": score, "text": e["text"][:60]})
    for e in EVAL_SET["slop"]:
        score = _contrastive_judge(e["text"], judge_call)
        rows.append({"id": e["id"], "label": "slop", "text": e["text"][:60], "score": score})

    iven_scores = [r["score"] for r in rows if r["label"] == "iven_tier_a"]
    slop_scores = [r["score"] for r in rows if r["label"] == "slop"]
    gap = min(iven_scores) - max(slop_scores)
    report = {"judge_model": judge_model, "rows": rows,
              "iven_min": min(iven_scores), "iven_max": max(iven_scores),
              "slop_min": min(slop_scores), "slop_max": max(slop_scores),
              "gap": round(gap, 3), "separated": gap > 0}

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(report, open(os.path.join(HERE, "results/calibration.json"), "w", encoding="utf-8"),
               ensure_ascii=False, indent=2)

    for r in rows:
        print(f'{r["label"]:12} {r["id"]:4} {r["score"]:.2f}  {r["text"]}')
    print(f'\nIven range: [{report["iven_min"]}, {report["iven_max"]}]')
    print(f'Slop range: [{report["slop_min"]}, {report["slop_max"]}]')
    print(f'Gap (iven_min - slop_max): {report["gap"]}  ->  {"分得開 ✅" if report["separated"] else "分不開 ❌ 撞天花板"}')


if __name__ == "__main__":
    main()
