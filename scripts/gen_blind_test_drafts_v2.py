"""Generate v2 drafts for blind test (3 topics × 2 modes = 6 drafts).

v2 差異：
- 只出 2 mode（real + naive_prof）— Karen 2026-08-01 決策：v2 只測「新 real vs baseline」
- real mode 沿用 spike full loop、但吃更新過的 style_pack.json（含 4 新 Iven dim）
- naive_prof 沿用 v1 pattern（baseline 不動）
- feedback loop 自動生效：gate 判 4 新 dim 低分 → reasons 進 next attempt prompt → 重寫（see iven_voice_graph.py）

Modes:
  real       — spike full loop, style_pack v2 已含 Iven 4 signal dim
  naive_prof — baseline #2: 「以商業專家身份寫」無 Iven persona

Output: blind_test_drafts_v2.json
Usage:
  export ANTHROPIC_API_KEY=...
  python scripts/gen_blind_test_drafts_v2.py
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(HERE))

env_path = HERE / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ERROR: export ANTHROPIC_API_KEY first")

import anthropic
from iven_voice_graph import run_once

SEEDS = json.load(open(HERE / "seeds/seeds_v2.json", encoding="utf-8"))["pairings"]
MODEL = "claude-sonnet-5"

client = anthropic.Anthropic()


def gen_naive_prof(seed):
    prompt = (
        f"以商業專家身份寫一則 Threads 貼文（≤500 字）。\n"
        f"題目：{seed['new_topic']['anchor']}\n"
        f"帶到「{seed['old_heart']['name']}」這個觀點：{seed['old_heart']['gist']}\n"
    )
    r = client.messages.create(
        model=MODEL, max_tokens=4096,
        system="你是一位商業專家，寫作專業、清晰、有洞察力。",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()


def gen_real(seed):
    """Spike full loop, style_pack v2 已含 Iven 4 signal dim (layered_reasoning /
    narrative_examples / throughline_insight / daishi_narrative_style)。

    gate 判 4 新 dim 低分 → reasons 進 feedback → next attempt prompt 帶
    差評重寫。max_attempts=3、若 3 輪都不過就回最後一稿。
    """
    r = run_once(seed, mode="real", max_attempts=3, model=MODEL, naive_first=False)
    return {
        "draft": r["history"][-1]["draft"],
        "attempts": r["attempts"],
        "final_pass": r["final_pass"],
        "final_total": r["final_total"],
        "history": [
            {"attempt": h["attempt"], "total": h["total"], "pass": h["pass"]}
            for h in r["history"]
        ],
    }


def main():
    out = {
        "meta": {
            "version": "v2",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": MODEL,
            "spike_gate_version": "B2 + Iven 4 signal dims (2026-08-01)",
            "modes": {
                "real": "spike full loop, style_pack v2 含 Iven 4 signal（layered_reasoning / narrative_examples / throughline_insight / daishi_narrative_style）",
                "naive_prof": "baseline #2: 以商業專家身份寫，無 Iven persona（不動）",
            },
            "changes_from_v1": [
                "style_pack.json 加 4 新 dim（see commit 2f530ec）",
                "gate feedback loop 自動吃 Iven 4 signal（_llm_judge auto-select detect==llm dim）",
                "只留 real + naive_prof 2 mode（Karen 2026-08-01 決策：只測新版 vs baseline）",
            ],
        },
        "drafts": [],
    }

    for seed in SEEDS[:3]:
        print(f"\n=== {seed['id']}: {seed['old_heart']['name']} × {seed['new_topic']['anchor']} ===", file=sys.stderr)
        entry = {"topic_id": seed["id"], "seed": seed, "modes": {}}

        print(f"  [real] spike loop with Iven 4-signal gate...", file=sys.stderr)
        real = gen_real(seed)
        entry["modes"]["real"] = real
        print(f"    → attempts={real['attempts']} pass={real['final_pass']} total={real['final_total']:.3f}", file=sys.stderr)
        for h in real["history"]:
            print(f"      attempt {h['attempt']}: total={h['total']:.3f} pass={h['pass']}", file=sys.stderr)

        print(f"  [naive_prof] baseline #2 (unchanged)...", file=sys.stderr)
        entry["modes"]["naive_prof"] = {"draft": gen_naive_prof(seed)}
        print(f"    → done ({len(entry['modes']['naive_prof']['draft'])} chars)", file=sys.stderr)

        out["drafts"].append(entry)

    output_path = HERE / "blind_test_drafts_v2.json"
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ wrote {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
