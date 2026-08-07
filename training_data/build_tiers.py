"""建 tier_annotations.jsonl（B2 第二部分）——explicit + 少量 inferred tier 標註。

Tier 詞彙表（暫定，非正式 rubric，golden-set 填完後應重新校準——見 README.md）：
- below_passing：明顯缺骨架或嚴重拗口，Iven rationale 明確負評
- passing：Iven 明訂『及格標準』/『不輸人』下限（P21/P30 出處）
- aspirational_direction：骨架/方向對，Iven 明訂『欣賞但執行未到位』——不是 fail，是『還沒完成的對的方向』

Usage: python3 training_data/build_tiers.py > training_data/tier_annotations.jsonl
"""
import json
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


V1_DRAFTS = load(HERE / "blind_test_drafts.json")["drafts"]
V3_DRAFTS = load(HERE / "blind_test_drafts_v3.json")["drafts"]


def draft_text(drafts, topic_id, mode):
    for d in drafts:
        tid = d.get("topic_id") or d.get("id")
        if tid == topic_id:
            return d["modes"][mode]["draft"]
    raise KeyError((topic_id, mode))


rows = [
    {
        "text": draft_text(V3_DRAFTS, "p3_v3", "naive_prof"),
        "tier": "passing",
        "annotator": "iven",
        "source": "v3_p3",
        "explicit": True,
        "iven_quote": "我自覺A這篇文章就是我認為的「及格標準」，寫到這程度，其實就不輸人了。",
    },
    {
        "text": draft_text(V3_DRAFTS, "p3_v3", "real"),
        "tier": "aspirational_direction",
        "annotator": "iven",
        "source": "v3_p3",
        "explicit": True,
        "iven_quote": "B更生動的故事寫法，雖然張力還不夠，但確實是我欣賞的方向。",
    },
    {
        "text": draft_text(V3_DRAFTS, "p1_v3", "real"),
        "tier": "below_passing",
        "annotator": "iven",
        "source": "v3_p1",
        "explicit": False,
        "iven_quote": "A比較像是我的敘事結構，但文筆實在太拗口生硬…一個句子要讀懂需要反覆看好幾次。",
        "inferred_note": "Iven 未明講 tier 字眼，但『反覆看好幾次才懂』是 vocalization_ease 嚴重失敗的具體描述，推定 below_passing。",
    },
    {
        "text": draft_text(V3_DRAFTS, "p2_v3", "naive_prof"),
        "tier": "below_passing",
        "annotator": "iven",
        "source": "v3_p2",
        "explicit": False,
        "iven_quote": "觀點可能很好，但會偏說教，缺乏吸引人不自覺一直想往下看的誘因。",
        "inferred_note": "推定：hook/argument_tension 失敗即便論點內容尚可，仍不到 Threads register 的 passing 門檻。",
    },
    {
        "text": draft_text(V1_DRAFTS, "p1", "naive_prof"),
        "tier": "below_passing",
        "annotator": "iven",
        "source": "v1_p1",
        "explicit": False,
        "iven_quote": "這三個都比較像是套版的文字，缺少一個貫穿主軸洞見或視角。",
        "inferred_note": "v1 p1 三個 mode 皆被此評語涵蓋（naive_prof/naive_threads/real 全部），這裡只取 naive_prof 一則示範；三則皆 tier=below_passing on throughline_insight 維度。",
    },
]

for r in rows:
    print(json.dumps(r, ensure_ascii=False))
