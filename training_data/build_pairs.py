"""建 preference_pairs.jsonl（B2）——從既有盲測 draft/answer JSON 直接抓文字，避免手動轉錄出錯。

來源（皆 Iven 評分為主，見 rationale_to_principles.md P27「Iven 判準優先」）：
- v1: blind_test_drafts.json + qoome-edge-share/iven-voice-blind-test-answers.json
- v2: blind_test_drafts_v2.json + qoome-edge-share/iven-voice-blind-test-v2-answers.json
- v3: blind_test_drafts_v3.json + qoome-edge-share/iven-voice-blind-test-v3-answers.json

⚠️ v1 p3 勘誤：FINDINGS.md §B5 把 Iven p3 rationale 的「C」標註為「naive_threads」，
但 Iven 當輪 order_map 實際是 A=naive_prof/B=naive_threads/C=real——C 其實是 real。
本腳本用原始 order_map 校正，不沿用 FINDINGS.md 的錯誤標註（已在 README.md 記錄此勘誤，
FINDINGS.md 本體本輪不動，留給 Karen 決定是否訂正）。

v0（訪談）沒有比較 draft，不產 pair，改進 tier_a_corpus/ 與 principle_signals.jsonl。
v1 p1 三方皆弱（Iven 評語「三個都比較像套版」，pick 只是三選一勉強選，非清楚偏好）→ 不產 pair。

Usage: python3 training_data/build_pairs.py > training_data/preference_pairs.jsonl
"""
import json
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()
EDGE_SHARE = HERE.parent / "qoome-edge-share"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


V1_DRAFTS = load(HERE / "blind_test_drafts.json")["drafts"]
V2_DRAFTS = load(HERE / "blind_test_drafts_v2.json")["drafts"]
V3_DRAFTS = load(HERE / "blind_test_drafts_v3.json")["drafts"]

V1_ANSWERS = load(EDGE_SHARE / "iven-voice-blind-test-answers.json")["submissions"]
V2_ANSWERS = load(EDGE_SHARE / "iven-voice-blind-test-v2-answers.json")["submissions"]
V3_ANSWERS = load(EDGE_SHARE / "iven-voice-blind-test-v3-answers.json")["submissions"]


def draft_text(drafts, topic_id, mode):
    for d in drafts:
        tid = d.get("topic_id") or d.get("id")
        if tid == topic_id:
            return d["modes"][mode]["draft"]
    raise KeyError((topic_id, mode))


def iven_answer(answers, topic_id):
    for sub in answers:
        if sub["rater"] == "iven":
            return sub["order_map"][topic_id], sub["answers"][topic_id]
    raise KeyError(topic_id)


pairs = []

# ---------- v1（present-self round，§B5）----------
# p2：real(C) 明確雙重被拒（不像也不欣賞），naive_threads(B) 相對最貼近
order, ans = iven_answer(V1_ANSWERS, "p2")
pairs.append({
    "prompt": "重組式機會 × 過剩市場（v1 p2 題材）",
    "chosen": draft_text(V1_DRAFTS, "p2", "naive_threads"),
    "rejected": draft_text(V1_DRAFTS, "p2", "real"),
    "rationale": ans["rationale"],
    "source": "iven_v1_p2",
    "dimensions_scored": ["register_playful", "narrative_examples"],
    "confidence": "weak",
    "confidence_note": "三方皆非強偏好（Iven：naive_threads『太軟』、real『不欣賞不擅長』，屬 least-bad 而非 clear win），present-self round 方法論已知有噪音（見 FINDINGS §B6 v2 隱藏 signal 教訓）。",
})

# p3：real(C) 在「敘事寫法」這一具體軸被欣賞，即使整體 pick 是 naive_prof(A)
# ⚠️ 勘誤：FINDINGS.md 標「C（naive_threads）」，Iven 當輪 order_map 顯示 C=real，本 pair 用正確標籤
order, ans = iven_answer(V1_ANSWERS, "p3")
pairs.append({
    "prompt": "HITL 分工律 × agent 熱潮（v1 p3 題材）",
    "chosen": draft_text(V1_DRAFTS, "p3", "real"),
    "rejected": draft_text(V1_DRAFTS, "p3", "naive_prof"),
    "rationale": ans["rationale"],
    "source": "iven_v1_p3",
    "dimensions_scored": ["narrative_examples"],
    "confidence": "weak",
    "confidence_note": "narrow-scope pair——只在『敘事寫法』單一維度成立，整體 pick 其實是 naive_prof。FINDINGS.md §B5 把此題 C 誤標成 naive_threads，實際 order_map 是 real，本 pair 已用正確標籤（見本檔案開頭勘誤說明）。這是 v1 就已出現 pick≠欣賞 分裂訊號的早期證據，比 v2 才浮現的認知更早，值得回填 FINDINGS。",
})

# ---------- v2（present-self round 2，§B6，隱藏 signal：pick≠欣賞）----------
for topic, chosen_mode, rejected_mode, dims in [
    ("p1_v2", "real", "naive_prof", ["narrative_examples", "vantage_point_entry"]),
    ("p2_v2", "real", "naive_prof", ["throughline_insight"]),
    ("p3_v2", "real", "naive_prof", ["narrative_examples", "vocalization_ease"]),
]:
    order, ans = iven_answer(V2_ANSWERS, topic)
    pairs.append({
        "prompt": f"v2 盲測題材（{topic}，見 FINDINGS.md §B6）",
        "chosen": draft_text(V2_DRAFTS, topic, chosen_mode),
        "rejected": draft_text(V2_DRAFTS, topic, rejected_mode),
        "rationale": ans["rationale"],
        "source": f"iven_v2_{topic}",
        "dimensions_scored": dims,
        "confidence": "medium",
        "confidence_note": "chosen 取『欣賞』方向非『pick』方向（P27：兩者需分開追蹤，v2 表面 pick 6/6 選 naive_prof，但 3/3 都欣賞 real，見 FINDINGS §B6）。",
    })

# ---------- v3（aspirational round，§B6 v3，dual rubric，score2 為主）----------
V3_REAL_LETTER = {"p1_v3": "A", "p2_v3": "B", "p3_v3": "B", "p4_v3": "A"}  # 已用 order_map 反解，見 rationale_to_principles.md R-index

order, ans = iven_answer(V3_ANSWERS, "p1_v3")
pairs.append({
    "prompt": "商業/專業資產化題（v3 p1，見 FINDINGS.md §B6 v3）",
    "chosen": draft_text(V3_DRAFTS, "p1_v3", "naive_prof"),
    "rejected": draft_text(V3_DRAFTS, "p1_v3", "real"),
    "rationale": ans["rationale"],
    "source": "iven_v3_p1",
    "dimensions_scored": ["vocalization_ease"],
    "confidence": "medium",
    "confidence_note": "v3 4 題唯一 real 輸的題（score2_real=2 < score2_naive_prof=5）——反面樣本，非隨機噪音：real 骨架對但『文筆太拗口生硬』（vocalization_ease 負例），非結構問題。P28 反面警訊守則檢查：Iven 仍稱 naive_prof『我不擅長這樣寫』= 仍是 aspirational 方向，只是這篇 real 執行沒到位，不算方向錯誤警訊。",
})

order, ans = iven_answer(V3_ANSWERS, "p2_v3")
pairs.append({
    "prompt": "商業模式題（v3 p2，見 FINDINGS.md §B6 v3）",
    "chosen": draft_text(V3_DRAFTS, "p2_v3", "real"),
    "rejected": draft_text(V3_DRAFTS, "p2_v3", "naive_prof"),
    "rationale": ans["rationale"],
    "source": "iven_v3_p2",
    "dimensions_scored": ["argument_tension", "vantage_point_entry"],
    "confidence": "strong",
    "confidence_note": "score2 real(4) > naive_prof(3)，rationale 明確指出 naive_prof『偏說教缺乏誘因』、real『容易入口但缺論點張力』——argument_tension dim 直接來源。",
})

order, ans = iven_answer(V3_ANSWERS, "p3_v3")
pairs.append({
    "prompt": "判斷力題（v3 p3，見 FINDINGS.md §B6 v3）",
    "chosen": draft_text(V3_DRAFTS, "p3_v3", "real"),
    "rejected": draft_text(V3_DRAFTS, "p3_v3", "naive_prof"),
    "rationale": ans["rationale"],
    "source": "iven_v3_p3",
    "dimensions_scored": ["narrative_examples", "vocalization_ease"],
    "confidence": "strong",
    "confidence_note": "score2 real(4) > naive_prof(3)，rationale 明確給出 tier 錨點：naive_prof=『及格標準』、real=『欣賞方向但張力不夠』（P21/P30 tier 定義出處）。",
})

# p4：教科書級雙變數 preference，拆兩對 pair（骨架 vs 密度）——見 rationale_to_principles.md P07
# ⚠️ 與 Vault plan 24-*.md 原草稿「chosen=B, rejected=A」寫法不同：plan 寫作當下未反解 order_map，
# 用 A/B 泛指「real 類/naive 類」語意角色，非本題實際字母。已用 order_map 反解後之正確方向如下：
order, ans = iven_answer(V3_ANSWERS, "p4_v3")
pairs.append({
    "prompt": "生活觀察題（v3 p4，骨架維度，見 FINDINGS.md §B6 v3）",
    "chosen": draft_text(V3_DRAFTS, "p4_v3", "real"),
    "rejected": draft_text(V3_DRAFTS, "p4_v3", "naive_prof"),
    "rationale": ans["rationale"],
    "source": "iven_v3_p4_structure",
    "dimensions_scored": ["layered_reasoning", "narrative_examples"],
    "confidence": "strong",
    "confidence_note": "骨架維度：real 手法優於 naive_prof（rationale『B的敘事結構像，但更像是在寫技術白皮書』——B=naive_prof 缺敘事骨架）。",
})
pairs.append({
    "prompt": "生活觀察題（v3 p4，密度維度，見 FINDINGS.md §B6 v3）",
    "chosen": draft_text(V3_DRAFTS, "p4_v3", "naive_prof"),
    "rejected": draft_text(V3_DRAFTS, "p4_v3", "real"),
    "rationale": ans["rationale"],
    "source": "iven_v3_p4_density",
    "dimensions_scored": ["structure_density_hybrid"],
    "confidence": "strong",
    "confidence_note": "密度維度：naive_prof 資訊密度優於 real（rationale『A的寫法…雖然在技術資訊的密度上，不及B』——A=real 密度不足）。此對 + 上一對合起來就是 P07 hybrid 訊號的資料來源：理想解不是二選一，是骨架學 real、密度學 naive_prof。",
})

for p in pairs:
    print(json.dumps(p, ensure_ascii=False))
