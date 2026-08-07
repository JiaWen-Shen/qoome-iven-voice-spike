"""Iven aspirational-voice 單次生成腳本（不走 gate/redo 迴圈，見 references/method.md）。

沿用 qoome-iven-voice-spike/scripts/gen_blind_test_drafts_v3.py 的 gen_real() 邏輯，
泛化成任意題材 + register（Threads/長文）參數化版本。

Usage:
  export ANTHROPIC_API_KEY=...
  python3 gen.py --topic "AI agent 熱潮下的 HITL 分工律" --register Threads
  python3 gen.py --topic "供應鏈韌性的新典範" --gist "舊心法：分散風險不是分散信任" --register 長文
  python3 gen.py --topic "..." --dry-run   # 不需要 API key，只印組好的 prompt
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()
REFERENCES = HERE / "references"

env_path = HERE / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

MODEL = "claude-sonnet-5"
MAX_TOKENS = 8192  # 沿用 spike 教訓（commit aee8017）：4096 會被 extended thinking 吃光導致首稿全空

STYLE_PACK = json.loads((REFERENCES / "style_pack_v1.json").read_text(encoding="utf-8"))
EXEMPLAR_POOL = json.loads((REFERENCES / "exemplar_pool_v4.json").read_text(encoding="utf-8"))["exemplars"]

REGISTER_ALIASES = {"Threads": "Threads", "threads": "Threads", "長文": "長文", "long": "長文", "long-form": "長文"}


def _dims_for_register(register: str) -> list:
    """篩出適用該 register 的 dim（register 欄位含『全 register』或指定 register 字串即納入）。"""
    out = []
    for d in STYLE_PACK["dimensions"]:
        reg = d.get("register", "全 register")
        if "全 register" in reg or register in reg:
            out.append(d)
    return out


def _build_exemplar_block() -> str:
    lines = ["【Iven aspirational 參考段落】（追『他想成為的樣子』、非『他現在的樣子』）\n"]
    for e in EXEMPLAR_POOL:
        lines.append(f"— [{e['id']}] 來源 {e['source_section']}（{e['source_file']}）")
        lines.append(f"  為何 aspirational：{e['why_aspirational']}")
        lines.append(f"  段落：\n{e['text']}\n")
    return "\n".join(lines)


def _build_dim_checklist(dims: list) -> str:
    lines = []
    for d in dims:
        if d["polarity"] == "+":
            lines.append(f"- {d['label']}：{d['guide']}")
    return "\n".join(lines)


def build_prompt(topic: str, gist: str, register: str, pillar: str) -> tuple:
    dims = _dims_for_register(register)
    exemplar_block = _build_exemplar_block()
    dim_checklist = _build_dim_checklist(dims)

    system = (
        "你是 Iven 本人在探索『想成為的自己』時、正在練習的新聲音。"
        "任務不是複製他現在的日常寫作平均值——是往他嚮往、他欣賞、他自己認為『那樣寫更好』的方向靠攏。\n\n"
        "核心方向（不分 register）：\n"
        "- **命名式概念**（把類比鑄成專有名詞——這是他招牌手法）\n"
        "- **重定義結構**（『不是 X，是 Y』『不是 X，而是 Y』，帶對比張力）\n"
        "- **層層推導、非快速斷言**（3+ 層前提→中介→結論，不要一句話跳結論）\n"
        "- **具體故事/舉例/人物承載觀點**（不要條列或抽象論證）\n"
        "- **貫穿主軸洞見**（一個 non-obvious 的核心 idea 貫穿全文、不套版）\n"
        "- **反覆辯證 + 反直覺洞察**（先立常識/直覺，明確轉折，再反轉出新洞見——非單向論述）\n"
        "- **口讀感順口**（唸出聲要順，不要堆疊修飾語/從句嵌套到需要反覆看才懂）\n"
        f"\n本次 register：{register}。適用 dim checklist：\n{dim_checklist}\n"
    )

    prompt_lines = []
    length_hint = "≤500 字，前 175 字要有 hook" if register == "Threads" else "800-1500 字，可分段深入"
    prompt_lines.append(f"用 Iven aspirational 聲音寫一篇{register}內容（{length_hint}）。\n")
    if gist:
        prompt_lines.append(f"心法：{gist}")
    prompt_lines.append(f"題材錨點：{topic}")
    if pillar:
        prompt_lines.append(f"支柱（pillar）：{pillar}")
    prompt_lines.append(f"\n{exemplar_block}\n")
    prompt_lines.append("寫作原則：")
    prompt_lines.append("- 開場用場景化人物切入或特殊視角切入，不要抽象命題起手")
    prompt_lines.append("- 至少 1 個命名式概念（把類比鑄成專有名詞）")
    prompt_lines.append("- 至少 1 處『不是 X，是 Y』重定義結構")
    prompt_lines.append("- 一個 non-obvious 主軸洞見在中段浮現、貫穿到結尾")
    prompt_lines.append("- 若有量化對比，用對稱句式與具體數字")
    if register == "長文":
        prompt_lines.append("- 可承載較高資訊密度（數據/機制細節），但骨架仍要敘事化承載，不要變成純技術規格條列")
    else:
        prompt_lines.append("- 優先容易入口 + 保留論點張力，短句斷言只能出現在開場或結尾")
    prompt_lines.append("- 不要提到『大時叔叔』/『尾崎秀實』/『Iven』/『忘機』這些名字本身——只採用它們的敘事骨架與精神")
    if gist:
        prompt_lines.append("- 不要逐字複製上面『心法』的原句——那是抄提示，不是轉譯成 Iven 語感")

    user = "\n".join(prompt_lines)
    return system, user


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", required=True, help="題材錨點")
    ap.add_argument("--gist", default="", help="舊心法/既有觀點一句話（可選）")
    ap.add_argument("--register", default="Threads", help="Threads 或 長文")
    ap.add_argument("--pillar", default="", help="標籤用（商業/HTP專業/私域/生活觀察），不影響生成邏輯")
    ap.add_argument("--dry-run", action="store_true", help="只印組好的 prompt，不呼叫 API")
    args = ap.parse_args()

    register = REGISTER_ALIASES.get(args.register, args.register)
    if register not in ("Threads", "長文"):
        sys.exit(f"ERROR: --register 只接受 Threads 或 長文，收到 {args.register!r}")

    system, user = build_prompt(args.topic, args.gist, register, args.pillar)

    if args.dry_run:
        print("=" * 20, "SYSTEM PROMPT", "=" * 20)
        print(system)
        print("=" * 20, "USER PROMPT", "=" * 20)
        print(user)
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: export ANTHROPIC_API_KEY first（或用 --dry-run 先檢查 prompt 組裝）")

    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=MODEL, max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    draft = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
    print(draft)


if __name__ == "__main__":
    main()
