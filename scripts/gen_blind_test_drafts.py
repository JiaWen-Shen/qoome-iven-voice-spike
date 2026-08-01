"""Generate 9 drafts for blind test (3 topics × 3 modes).

Modes:
  real          — spike full loop (Iven style, B2 gate default, naive_first=False for cleanest output)
  naive_prof    — baseline #2: 「以商業專家身份寫 Threads 貼文」zero Iven persona
  naive_threads — baseline #5: Threads 高互動格式 conventions（逆向共識/造詞/短句）but no specific persona

Output: blind_test_drafts.json
Usage:
  export ANTHROPIC_API_KEY=...
  python scripts/gen_blind_test_drafts.py
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(HERE))

# load .env if exists (else rely on env)
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

SEEDS = json.load(open(HERE / "seeds/seeds.json", encoding="utf-8"))["pairings"]
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


def gen_naive_threads_only(seed):
    """Baseline #5: Threads 高互動格式 conventions but no Iven persona."""
    prompt = (
        f"用符合 Threads 平台高互動貼文格式的寫法（≤500 字，前 175 字要有 hook）。\n"
        f"格式要求：\n"
        f"- 逆向共識角度切入（挑戰主流論述）\n"
        f"- 短句斷言、少用轉折連接詞\n"
        f"- 允許中英夾雜、命名式造詞\n"
        f"- 提問或引戰收尾\n\n"
        f"題目：{seed['new_topic']['anchor']}\n"
        f"帶到「{seed['old_heart']['name']}」這個觀點：{seed['old_heart']['gist']}\n"
    )
    r = client.messages.create(
        model=MODEL, max_tokens=4096,
        system="你是一位擅長 Threads 平台的社群寫作者，掌握該平台的高互動貼文格式。不要模仿任何特定人物的口吻，用你自己的方式寫。",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()


def gen_real(seed):
    """Spike full loop with Iven style (naive_first=False for cleanest single-pass output).

    Note: uses B2 gate (contrastive + judge/draft split + no_seed_leak veto), which is
    the current spike default. If gate rejects, loop retries up to 3 times with feedback.
    """
    r = run_once(seed, mode="real", max_attempts=3, model=MODEL, naive_first=False)
    return {
        "draft": r["history"][-1]["draft"],
        "attempts": r["attempts"],
        "final_pass": r["final_pass"],
        "final_total": r["final_total"],
    }


def main():
    out = {
        "meta": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": MODEL,
            "spike_gate_version": "B2 (contrastive + judge/draft split + no_seed_leak veto)",
            "modes": {
                "real": "spike full loop, Iven style (STYLE_PACK), naive_first=False",
                "naive_prof": "baseline #2: 以商業專家身份寫，無 Iven persona",
                "naive_threads": "baseline #5: Threads 格式 conventions 但無特定 persona",
            },
        },
        "drafts": [],
    }

    for seed in SEEDS[:3]:
        print(f"\n=== {seed['id']}: {seed['old_heart']['name']} × {seed['new_topic']['anchor']} ===", file=sys.stderr)
        entry = {"topic_id": seed["id"], "seed": seed, "modes": {}}

        print(f"  [real] spike loop...", file=sys.stderr)
        real = gen_real(seed)
        entry["modes"]["real"] = real
        print(f"    → attempts={real['attempts']} pass={real['final_pass']} total={real['final_total']:.3f}", file=sys.stderr)

        print(f"  [naive_prof] baseline #2...", file=sys.stderr)
        entry["modes"]["naive_prof"] = {"draft": gen_naive_prof(seed)}
        print(f"    → done ({len(entry['modes']['naive_prof']['draft'])} chars)", file=sys.stderr)

        print(f"  [naive_threads] baseline #5...", file=sys.stderr)
        entry["modes"]["naive_threads"] = {"draft": gen_naive_threads_only(seed)}
        print(f"    → done ({len(entry['modes']['naive_threads']['draft'])} chars)", file=sys.stderr)

        out["drafts"].append(entry)

    output_path = HERE / "blind_test_drafts.json"
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ wrote {output_path} ({sum(len(json.dumps(e)) for e in out['drafts'])} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
