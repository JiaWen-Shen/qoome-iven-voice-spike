"""Generate v3 drafts for blind test (4 topics × 2 modes = 8 drafts).

## v3 核心目標轉向

v0-v2 追 present-self（clone 現在的 Iven）；v3 起追 **aspirational-self**（Iven 想成為的樣子）。
v2 Karen+Iven 100% 覺得 naive_prof 才像 Iven、但 3/3 都欣賞 real——present 跟 aspirational 是分開兩件事。
spike 存在意義本來就是幫 Iven 長成他想成為的樣子，不是複製現在。

## v3 差異（相對 v2）

- **4 題×4 pillar**（v2 3 題）：商業 / HTP 專業 / 私域客戶 / 生活觀察
- **real mode**：直接吃 aspirational_exemplar_pool_v3.json 4 條 exemplar + 保留大時叔叔敘事錨點
  - 不走 langgraph gate loop（v2 gate rubric 是 present metric，v3 aspirational 用不上）
  - 系統 prompt 明確指示：往 aspirational 方向靠，不追「現在 Iven 平常寫法」
- **naive_prof**：**完全同 v2**（baseline 不動、對照組）
- Output: blind_test_drafts_v3.json（schema 同 v2、加 `mode_desc.real` 說明轉向）

Usage:
  export ANTHROPIC_API_KEY=...
  python scripts/gen_blind_test_drafts_v3.py
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

SEEDS = json.load(open(HERE / "seeds/seeds_v3.json", encoding="utf-8"))["pairings"]
EXEMPLAR_POOL = json.load(open(HERE / "seeds/aspirational_exemplar_pool_v3.json", encoding="utf-8"))["exemplars"]
MODEL = "claude-sonnet-5"

client = anthropic.Anthropic()


def _build_aspirational_exemplar_block() -> str:
    """把 aspirational_exemplar_pool_v3.json 4 條 exemplar 塞成 prompt 區塊。"""
    lines = ["【Iven aspirational 參考段落】（v3 起改追『他想成為的樣子』、非『他現在的樣子』）\n"]
    for e in EXEMPLAR_POOL:
        lines.append(f"— [{e['id']}] 來源 {e['source_section']}（{e['source_file']}）")
        lines.append(f"  為何 aspirational：{e['why_aspirational']}")
        lines.append(f"  段落：\n{e['text']}\n")
    return "\n".join(lines)


ASPIRATIONAL_BLOCK = _build_aspirational_exemplar_block()


def gen_naive_prof(seed):
    """Baseline — 完全同 v2。以商業專家身份寫，無 Iven persona。"""
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
    """Aspirational real — 吃 aspirational exemplar pool 4 條 + 大時叔叔錨點。

    v3 不走 gate loop：gate rubric 是 present metric（『像 Iven default 聲音』），
    aspirational 目標下用不上、還會反噬。直接一次 gen、由盲測讀者 aspirational-score 打分。
    """
    system = (
        "你是 Iven 本人在探索『想成為的自己』時、正在練習的新聲音。"
        "任務不是複製他現在的日常寫作平均值——是往他嚮往、他欣賞、他自己認為『那樣寫更好』的方向靠攏。\n\n"
        "核心方向：\n"
        "- **命名式概念**（把類比鑄成專有名詞：『向善的機巧』『大惑易性』『失真』『玄德值』——這是他招牌手法）\n"
        "- **重定義結構**（『不是 X，是 Y』『不是 X，而是 Y』，帶對比張力）\n"
        "- **層層推導、非快速斷言**（3+ 層前提→中介→結論，不要一句話跳結論）\n"
        "- **具體故事/舉例/人物承載觀點**（不要條列或抽象論證）\n"
        "- **貫穿主軸洞見**（一個 non-obvious 的核心 idea 貫穿全文、不套版）\n"
        "- **自覺矛盾/自嘲張力**（Iven soul 特徵——把診斷成病根的東西當藥引那種轉折）\n"
        "- **大時叔叔敘事結構**（Iven 2026-08-01 自認的敘事完形錨點）"
    )
    prompt = (
        f"用 Iven aspirational 聲音寫一則 Threads 貼文（≤500 字，前 175 字要有 hook）。\n\n"
        f"心法：{seed['old_heart']['name']} — {seed['old_heart']['gist']}\n"
        f"題材錨點：{seed['new_topic']['anchor']}\n"
        f"支柱（pillar）：{seed['new_topic']['pillar']}\n\n"
        f"{ASPIRATIONAL_BLOCK}\n\n"
        f"寫作原則：\n"
        f"- 開場用場景化人物切入、不要抽象命題起手\n"
        f"- 至少 1 個命名式概念（把類比鑄成專有名詞）\n"
        f"- 至少 1 處『不是 X，是 Y』重定義結構\n"
        f"- 一個 non-obvious 主軸洞見在中段浮現、貫穿到結尾\n"
        f"- 若有量化對比，用對稱句式與具體數字\n"
        f"- 不要提到『大時叔叔』/『尾崎秀實』/『Iven』/『忘機』這些名字本身——只採用他們的敘事骨架與精神\n"
    )
    r = client.messages.create(
        model=MODEL, max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()


def main():
    out = {
        "meta": {
            "version": "v3",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": MODEL,
            "target_shift": "v0-v2 追 present-self（clone 現在的 Iven）；v3 起追 aspirational-self（想成為的樣子）",
            "modes": {
                "real": "aspirational — 直接吃 aspirational_exemplar_pool_v3.json 4 條 exemplar + 大時叔叔錨點，不走 gate loop（gate rubric 是 present metric）",
                "naive_prof": "baseline — 完全同 v2（以商業專家身份寫，無 Iven persona）",
            },
            "changes_from_v2": [
                "3 題 → 4 題（跨 4 pillar：商業/HTP 專業/私域/生活）",
                "aspirational exemplar pool 取代 v2 eval_set.json iven_tier_a（present-flavored）",
                "real mode 不再跑 langgraph gate loop（gate rubric 是 present、跟 aspirational 目標不對齊）",
                "answer schema 改雙評分（score1=像現在／score2=想成為），HTML + workflow 同步改",
            ],
            "exemplar_pool_selected_by": "karen_fallback (Iven 若自選、覆蓋 aspirational_exemplar_pool_v3.json)",
        },
        "drafts": [],
    }

    for seed in SEEDS:
        print(f"\n=== {seed['id']}（{seed['pillar']}）: {seed['old_heart']['name']} × {seed['new_topic']['anchor'][:40]} ===", file=sys.stderr)
        entry = {"topic_id": seed["id"], "seed": seed, "modes": {}}

        print(f"  [real] aspirational one-shot (no gate loop)...", file=sys.stderr)
        real_draft = gen_real(seed)
        entry["modes"]["real"] = {"draft": real_draft, "len": len(real_draft)}
        print(f"    → done ({len(real_draft)} chars)", file=sys.stderr)

        print(f"  [naive_prof] baseline #2 (unchanged from v2)...", file=sys.stderr)
        naive_draft = gen_naive_prof(seed)
        entry["modes"]["naive_prof"] = {"draft": naive_draft, "len": len(naive_draft)}
        print(f"    → done ({len(naive_draft)} chars)", file=sys.stderr)

        out["drafts"].append(entry)

    output_path = HERE / "blind_test_drafts_v3.json"
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ wrote {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
